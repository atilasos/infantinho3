from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from django.db.models import Avg, Max
from django.utils import timezone

from ai.models import LearnerContextSnapshot


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
        return {
            "focus_areas": list(
                user.focus_areas.filter(active=True, class_context=class_context).values(
                    "focus_text", "priority", "created_at"
                )
            ),
            "class_overview": self._class_overview(class_context),
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
