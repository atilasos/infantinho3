from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Dict, Optional

from django.db.models import Avg, Max
from django.utils import timezone

from ai.models import LearnerContextSnapshot

logger = logging.getLogger(__name__)


@dataclass
class ContextData:
    payload: Dict[str, Any]


class ContextBroker:
    def build_context(
        self,
        user,
        persona: str,
        class_context=None,
        origin_app: Optional[str] = None,
        extras: Optional[Dict[str, Any]] = None,
        raw_query: Optional[str] = None,
    ) -> ContextData:
        context: Dict[str, Any] = {
            "user": {
                "id": user.id,
                "name": user.get_full_name() or user.username,
                "role": user.role,
            },
            "persona": persona,
            "origin_app": origin_app,
            "extras": extras or {},
        }
        if class_context:
            context["class"] = {
                "id": class_context.id,
                "name": getattr(class_context, "name", ""),
                "year": getattr(class_context, "academic_year", ""),
            }
        context["class_overview"] = self._class_overview(class_context)
        if persona == "student":
            context.update(self._student_context(user, class_context))
        elif persona == "teacher":
            context.update(self._teacher_context(user, class_context))
            # If no class_context, suggest class disambiguation when multiple classes are found
            if class_context is None:
                candidates = self._teacher_class_candidates(user)
                if len(candidates) > 1:
                    context["disambiguation"] = {
                        "type": "class",
                        "options": [{"id": c.get("id"), "name": c.get("name")} for c in candidates[:6]],
                    }
            # If a teacher mentions a specific student by name in the query, attach a compact student focus
            student = self._resolve_student_from_query(raw_query, class_context)
            if student:
                student_focus = self._student_focus_compact(student, class_context)
                context["student_focus"] = student_focus
                context["teacher_student_brief"] = self._teacher_student_brief(student_focus)
                try:
                    logger.info(
                        "AI Context: matched student name -> id=%s name=%s class_id=%s",
                        student.id,
                        student.get_full_name() or student.username,
                        getattr(class_context, "id", None),
                    )
                except Exception:
                    pass
        return ContextData(payload=context)

    def _student_context(self, user, class_context) -> Dict[str, Any]:
        profile: Dict[str, Any] = {
            "grade_level": self._extract_grade_level(class_context),
            "age_hint": self._estimate_age(self._extract_grade_level(class_context)),
            "learner_snapshot": self._latest_snapshot(user, class_context),
            "pit": self._current_pit(user, class_context),
            "checklists": self._checklist_progress(user, class_context),
        }
        profile["checklist_focus"] = self._checklist_focus(profile["checklists"])
        profile["recent_projects"] = self._recent_projects(user, class_context)
        profile["council_notes"] = self._recent_council_highlights(class_context)
        return {"learner_profile": profile}

    def _teacher_context(self, user, class_context) -> Dict[str, Any]:
        class_ck = self._class_checklist_summary(class_context)
        brief = self._teacher_class_brief(class_ck=class_ck, class_context=class_context)
        return {
            "focus_areas": list(
                user.focus_areas.filter(active=True, class_context=class_context).values(
                    "focus_text", "priority", "created_at"
                )
            ),
            "class_overview": self._class_overview(class_context),
            "class_checklists": class_ck,
            "teacher_class_brief": brief,
        }

    def _latest_snapshot(self, user, class_context) -> Dict[str, Any]:
        snapshot = (
            LearnerContextSnapshot.objects.filter(student=user, class_context=class_context)
            .order_by("-refreshed_at")
            .first()
        )
        if not snapshot:
            return {}
        return {
            "summary": snapshot.summary,
            "strengths": snapshot.strengths,
            "needs": snapshot.needs,
            "mem_competencies": snapshot.mem_competencies,
            "last_checklist_update": snapshot.last_checklist_update.isoformat()
            if snapshot.last_checklist_update
            else None,
        }

    def _current_pit(self, user, class_context) -> Dict[str, Any]:
        try:
            from pit.models import IndividualPlan

            plan = (
                IndividualPlan.objects.filter(student=user, student_class=class_context)
                .order_by("-created_at")
                .first()
            )
        except Exception:
            plan = None
        if not plan:
            return {}
        return {
            "period": plan.period_label,
            "status": plan.status,
            "objectives": plan.general_objectives,
        }

    def _checklist_progress(self, user, class_context) -> Dict[str, Any]:
        try:
            from checklists.models import ChecklistStatus

            statuses = (
                ChecklistStatus.objects.filter(student=user, student_class=class_context)
                .select_related("template")
                .prefetch_related("marks__item")
                .order_by("template__name")
            )
        except Exception:
            statuses = []
        progress = {}
        for status in statuses:
            marks = list(status.marks.select_related("item"))
            pending = [
                {
                    "item": mark.item.text,
                    "code": mark.item.code,
                    "status": mark.mark_status,
                    "order": getattr(mark.item, "order", 0),
                    "template": status.template.name,
                    "percent_complete": status.percent_complete,
                }
                for mark in marks
                if mark.mark_status not in {"COMPLETED", "VALIDATED"}
            ]
            progress[status.template.name] = {
                "percent_complete": status.percent_complete,
                "last_updated": status.updated_at.isoformat(),
                "pending_items": pending,
            }
        return progress

    def _recent_projects(self, user, class_context) -> Dict[str, Any]:
        try:
            from projects.models import Project

            projects = (
                Project.objects.filter(student_class=class_context, members=user)
                .order_by("-updated_at")[:3]
            )
        except Exception:
            projects = []
        return {
            project.title: {
                "state": project.state,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            }
            for project in projects
        }

    def _class_checklist_summary(self, class_context) -> Dict[str, Any]:
        if not class_context:
            return {}
        try:
            from checklists.models import ChecklistStatus

            statuses = (
                ChecklistStatus.objects.filter(student_class=class_context)
                .select_related("template")
                .prefetch_related("marks__item")
            )
        except Exception:
            return {}

        # Aggregate pending items across class and average completion per template
        pending_counter: dict[tuple[str, str], int] = {}
        template_totals: dict[str, dict[str, float]] = {}
        overall_sum = 0.0
        overall_count = 0

        for status in statuses:
            # Percent complete per template
            tpl = status.template.name if getattr(status, "template", None) else ""
            if tpl:
                if tpl not in template_totals:
                    template_totals[tpl] = {"sum": 0.0, "count": 0.0}
                template_totals[tpl]["sum"] += float(getattr(status, "percent_complete", 0) or 0)
                template_totals[tpl]["count"] += 1
            overall_sum += float(getattr(status, "percent_complete", 0) or 0)
            overall_count += 1

            # Pending items per mark
            try:
                marks = list(status.marks.select_related("item"))
            except Exception:
                marks = []
            for mark in marks:
                mark_status = getattr(mark, "mark_status", None)
                if mark_status in {"COMPLETED", "VALIDATED"}:
                    continue
                item = getattr(mark, "item", None)
                if not item:
                    continue
                code = getattr(item, "code", "") or getattr(item, "id", "?")
                key = (tpl or "?", f"{code} — {getattr(item, 'text', '')[:80]}")
                pending_counter[key] = pending_counter.get(key, 0) + 1

        # Top pending items across class
        top_pending_items = [
            {"template": k[0], "item": k[1], "count_pending": c}
            for k, c in sorted(pending_counter.items(), key=lambda kv: (-kv[1], kv[0][0]))[:5]
        ]

        # Strengths by template (highest average completion)
        template_strengths = []
        for tpl, agg in template_totals.items():
            avg = (agg["sum"] / agg["count"]) if agg["count"] else 0.0
            template_strengths.append({"template": tpl, "avg_complete": round(avg, 1)})
        template_strengths.sort(key=lambda x: -x["avg_complete"])
        template_strengths = template_strengths[:5]

        overall_avg = round((overall_sum / overall_count) if overall_count else 0.0, 1)

        return {
            "overall_avg": overall_avg,
            "top_pending_items": top_pending_items,
            "template_strengths": template_strengths,
        }

    def _resolve_student_from_query(self, raw_query: Optional[str], class_context):
        if not raw_query or not class_context:
            return None
        try:
            raw = raw_query.strip().lower()
            if not raw:
                return None
            # Collect candidate students by fuzzy name match (first and/or last name contained)
            candidates = []
            for s in class_context.students.all():
                full = f"{s.first_name} {s.last_name}".strip().lower()
                if not full:
                    full = (s.get_full_name() or s.username or "").lower()
                # Require at least one token match of length >=3
                tokens = [t for t in full.split() if len(t) >= 3]
                if any(t in raw for t in tokens):
                    candidates.append(s)
            if len(candidates) == 1:
                return candidates[0]
            # If multiple, prefer exact substring of full name
            for s in candidates:
                full = f"{s.first_name} {s.last_name}".strip().lower()
                if full and full in raw:
                    return s
            # If still ambiguous (e.g., two “Ana”), return a special marker in extras
            if len(candidates) > 1:
                names = [c.get_full_name() or c.username for c in candidates[:6]]
                # Attach disambiguation options via logging; orchestrator prompt can ask confirmation
                logger.info("AI Context: multiple students matched: %s", names)
                return None
        except Exception:
            return None
        return None

    def _student_focus_compact(self, student, class_context) -> Dict[str, Any]:
        # Reuse existing helpers but keep only compact fields to save tokens
        profile = {
            "id": student.id,
            "name": student.get_full_name() or student.username,
        }
        snapshot = self._latest_snapshot(student, class_context)
        if snapshot:
            profile["strengths"] = snapshot.get("strengths")
            profile["needs"] = snapshot.get("needs")
        pit = self._current_pit(student, class_context)
        if pit:
            profile["pit"] = {k: pit.get(k) for k in ("period", "status")}
        # Checklist short: only average and top 2 pending items
        ck = self._checklist_progress(student, class_context)
        if ck:
            # compute simple average across templates
            try:
                percents = [v.get("percent_complete", 0) for v in ck.values()]
                avg = round(sum(percents) / len(percents), 1) if percents else 0
            except Exception:
                avg = 0
            pending_all = []
            for v in ck.values():
                pending_all.extend(v.get("pending_items", []) or [])
            # sort by highest template completion first then order
            pending_all.sort(key=lambda it: (-it.get("percent_complete", 0), it.get("order", 0)))
            profile["checklists"] = {
                "avg_complete": avg,
                "top_pending": [
                    {k: it.get(k) for k in ("item", "code", "template")}
                    for it in pending_all[:2]
                ],
            }
        return profile

    def _teacher_student_brief(self, student_focus: Dict[str, Any]) -> str:
        name = student_focus.get("name", "O aluno")
        avg = student_focus.get("checklists", {}).get("avg_complete", 0)
        pend = student_focus.get("checklists", {}).get("top_pending", [])
        pend_str = ", ".join(
            f"{p.get('item')} [{p.get('template')}]" for p in pend
        ) or "—"
        pit = student_focus.get("pit", {})
        pit_str = f"PIT: {pit.get('status', '—')} ({pit.get('period', '—')})."
        lines = [
            f"{name}: média de conclusão {avg}%.",
            f"Pendentes principais: {pend_str}.",
            pit_str,
        ]
        return " ".join(lines)

    def _teacher_class_brief(self, class_ck: Dict[str, Any], class_context) -> str:
        if not class_ck:
            return "Sem dados consolidados de checklists para esta turma."
        name = getattr(class_context, "name", "Turma") if class_context else "Turma"
        overall = class_ck.get("overall_avg", 0)
        strengths = ", ".join(
            f"{s['template']} ({s['avg_complete']}%)" for s in (class_ck.get("template_strengths") or [])[:2]
        ) or "—"
        pendings = ", ".join(
            f"{p['item']} [{p['template']}] (x{p['count_pending']})" for p in (class_ck.get("top_pending_items") or [])[:2]
        ) or "—"
        # 3-4 linhas curtas para orientar a resposta do assistente
        lines = [
            f"{name}: média de conclusão {overall}%.",
            f"Pontos fortes: {strengths}.",
            f"A melhorar (mais pendentes): {pendings}.",
        ]
        return " ".join(lines)

    def _teacher_class_candidates(self, user) -> list[Dict[str, Any]]:
        """Best-effort discovery of classes taught by the user.
        Returns a list of {id, name}. Robust to schema differences.
        """
        try:
            from classes.models import Class  # type: ignore

            # Try common relations
            try:
                qs = Class.objects.filter(teachers=user)
                return [{"id": c.id, "name": getattr(c, "name", str(c))} for c in qs[:8]]
            except Exception:
                pass
            try:
                qs = Class.objects.filter(staff=user)
                return [{"id": c.id, "name": getattr(c, "name", str(c))} for c in qs[:8]]
            except Exception:
                pass
            try:
                # Fallback: any class where user is member with role teacher
                qs = Class.objects.filter(members__user=user, members__role__in=["teacher", "professor"]).distinct()
                return [{"id": c.id, "name": getattr(c, "name", str(c))} for c in qs[:8]]
            except Exception:
                pass
            # Last resort: classes where user appears in generic M2M "members"
            try:
                qs = Class.objects.filter(members=user).distinct()
                return [{"id": c.id, "name": getattr(c, "name", str(c))} for c in qs[:8]]
            except Exception:
                return []
        except Exception:
            return []

    def _recent_council_highlights(self, class_context) -> Dict[str, Any]:
        if not class_context:
            return {}
        try:
            from council.models import CouncilDecision

            decisions = (
                CouncilDecision.objects.filter(student_class=class_context)
                .order_by("-created_at")[:5]
            )
        except Exception:
            decisions = []
        return {
            decision.description[:60]: {
                "category": decision.category,
                "status": decision.status,
            }
            for decision in decisions
        }

    def _class_overview(self, class_context) -> Dict[str, Any]:
        if not class_context:
            return {}
        stats = {
            "students": class_context.students.count() if hasattr(class_context, "students") else 0,
        }
        try:
            from projects.models import Project

            stats["projects_activos"] = class_context.projects.filter(
                state=Project.ProjectState.ACTIVE
            ).count()
        except Exception:
            stats["projects_activos"] = 0
        try:
            from pit.models import IndividualPlan

            stats["planos_submetidos"] = IndividualPlan.objects.filter(
                student_class=class_context
            ).count()
        except Exception:
            stats["planos_submetidos"] = 0
        try:
            stats["peers"] = [
                self._student_summary(student, class_context)
                for student in class_context.students.all()
            ]
        except Exception:
            stats["peers"] = []
        return stats

    def _extract_grade_level(self, class_context):
        if not class_context or not getattr(class_context, "name", None):
            return None
        import re

        match = re.search(r"(\d{1,2})º", class_context.name)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    def _estimate_age(self, grade_level: int | None) -> int | None:
        if grade_level is None:
            return None
        age_map = {
            1: 6,
            2: 7,
            3: 8,
            4: 9,
            5: 10,
            6: 11,
            7: 12,
            8: 13,
            9: 14,
        }
        return age_map.get(grade_level)

    def _checklist_focus(self, checklists: Dict[str, Any]) -> list[Dict[str, str]]:
        candidates = []
        for data in checklists.values():
            for item in data.get("pending_items", []):
                candidates.append(item)
        if not candidates:
            return []
        candidates.sort(key=lambda entry: (-entry.get("percent_complete", 0), entry.get("order", 0)))
        trimmed = []
        seen_templates = set()
        for candidate in candidates:
            template = candidate.get("template")
            if template in seen_templates and len(trimmed) >= 2:
                continue
            trimmed.append(
                {
                    "template": template,
                    "item": candidate.get("item"),
                    "code": candidate.get("code"),
                    "percent_complete": candidate.get("percent_complete"),
                }
            )
            seen_templates.add(template)
            if len(trimmed) >= 2:
                break
        return trimmed

    def _student_summary(self, student, class_context) -> Dict[str, Any]:
        summary = {
            "id": student.id,
            "name": student.get_full_name() or student.username,
            "role": student.role,
        }
        try:
            from checklists.models import ChecklistStatus

            aggregates = ChecklistStatus.objects.filter(
                student=student,
                student_class=class_context,
            ).aggregate(
                avg_percent=Avg('percent_complete'),
                max_percent=Max('percent_complete'),
            )
            summary["checklist_average"] = round(aggregates.get('avg_percent') or 0, 1)
            summary["checklist_best"] = round(aggregates.get('max_percent') or 0, 1)
        except Exception:
            summary["checklist_average"] = 0
            summary["checklist_best"] = 0
        return summary
