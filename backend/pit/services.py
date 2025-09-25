"""Domain services for PIT generation and related workflows."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from io import BytesIO
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pit.models import (
    IndividualPlan,
    PlanLogEntry,
    PlanSection,
    PlanSuggestion,
    PlanTask,
    PitTemplate,
    TemplateSection,
    TemplateSuggestion,
)
from council.models import CouncilDecision


@dataclass
class GenerationResult:
    plan: IndividualPlan
    created_sections: int
    created_suggestions: int
    created_pendings: int
    created_council: int


def _week_bounds(reference: date) -> tuple[date, date]:
    start = reference - timedelta(days=reference.weekday())
    end = start + timedelta(days=6)
    return start, end


def _pick_template(student_class) -> PitTemplate:
    qs = PitTemplate.objects.filter(student_class=student_class, is_active=True).order_by('-version', '-updated_at')
    template = qs.first()
    if not template:
        template = (
            PitTemplate.objects.filter(student_class__isnull=True, is_active=True)
            .order_by('-version', '-updated_at')
            .first()
        )
    if not template:
        raise ValidationError({'template': 'Não existe um modelo de PIT configurado.'})
    return template


def _build_period_label(start: date, end: date) -> str:
    return f"Semana {start.strftime('%d/%m')} – {end.strftime('%d/%m')}"


@transaction.atomic
def generate_weekly_plan(
    *,
    student,
    student_class,
    target_date: Optional[date] = None,
) -> GenerationResult:
    if target_date is None:
        target_date = date.today()

    week_start, week_end = _week_bounds(target_date)
    period_label = _build_period_label(week_start, week_end)

    if IndividualPlan.objects.filter(
        student=student,
        student_class=student_class,
        period_label=period_label,
    ).exists():
        raise ValidationError({'period': 'Já existe um PIT para esta semana.'})

    template = _pick_template(student_class)

    origin_plan = (
        IndividualPlan.objects.filter(student=student, student_class=student_class)
        .exclude(start_date__isnull=True)
        .filter(start_date__lt=week_start)
        .order_by('-start_date', '-created_at')
        .first()
    )
    if not origin_plan:
        origin_plan = (
            IndividualPlan.objects.filter(student=student, student_class=student_class)
            .order_by('-start_date', '-created_at')
            .first()
        )

    plan = IndividualPlan.objects.create(
        student=student,
        student_class=student_class,
        template=template,
        template_version=template.version,
        origin_plan=origin_plan,
        period_label=period_label,
        start_date=week_start,
        end_date=week_end,
        status=IndividualPlan.PlanStatus.DRAFT,
    )

    created_sections = _create_plan_sections(plan, template)
    created_suggestions = _import_template_suggestions(plan, template)
    created_pendings = _import_pending_tasks(plan, origin_plan)
    created_council = _import_council_suggestions(plan)

    plan.suggestions_imported = created_suggestions > 0
    plan.pendings_imported = created_pendings > 0
    plan.save(update_fields=['suggestions_imported', 'pendings_imported', 'updated_at'])

    _log_generation(
        plan,
        template,
        created_sections,
        created_suggestions,
        created_pendings,
        created_council,
    )

    return GenerationResult(
        plan=plan,
        created_sections=created_sections,
        created_suggestions=created_suggestions,
        created_pendings=created_pendings,
        created_council=created_council,
    )


def _create_plan_sections(plan: IndividualPlan, template: PitTemplate) -> int:
    sections = template.sections.order_by('order', 'id')
    bulk = [
        PlanSection(
            plan=plan,
            title=section.title,
            area_code=section.area_code,
            order=section.order,
            template_section=section,
        )
        for section in sections
    ]
    if not bulk:
        return 0
    PlanSection.objects.bulk_create(bulk)
    return len(bulk)


def _import_template_suggestions(plan: IndividualPlan, template: PitTemplate) -> int:
    template_suggestions = template.suggestions.select_related('section').order_by('order', 'id')
    bulk = [
        PlanSuggestion(
            plan=plan,
            text=suggestion.text,
            origin=PlanSuggestion.SuggestionSource.TEMPLATE,
            template_suggestion=suggestion,
            order=index,
            is_pending=suggestion.is_pending,
        )
        for index, suggestion in enumerate(template_suggestions, start=1)
    ]
    if not bulk:
        return 0
    PlanSuggestion.objects.bulk_create(bulk)
    return len(bulk)


def _import_pending_tasks(plan: IndividualPlan, origin_plan: Optional[IndividualPlan]) -> int:
    if not origin_plan:
        return 0
    pending_tasks = origin_plan.tasks.exclude(
        state__in=[
            PlanTask.TaskState.DONE,
            PlanTask.TaskState.VALIDATED,
        ]
    ).order_by('order', 'id')
    bulk: list[PlanSuggestion] = []
    start_order = plan.suggestions.count() + 1
    for offset, task in enumerate(pending_tasks, start=start_order):
        bulk.append(
            PlanSuggestion(
                plan=plan,
                text=f"Rever tarefa pendente: {task.description}",
                origin=PlanSuggestion.SuggestionSource.PENDING,
                from_task=task,
                order=offset,
                is_pending=True,
            )
        )
    if not bulk:
        return 0
    PlanSuggestion.objects.bulk_create(bulk)
    return len(bulk)


def _import_council_suggestions(plan: IndividualPlan) -> int:
    recent_window = plan.start_date - timedelta(days=30) if plan.start_date else date.today() - timedelta(days=30)
    decisions = (
        CouncilDecision.objects.filter(
            student_class=plan.student_class,
            date__gte=recent_window,
        )
        .exclude(status=CouncilDecision.Status.DONE)
        .order_by('-date', '-created_at')[:5]
    )
    if not decisions:
        return 0

    start_order = plan.suggestions.count() + 1
    bulk = [
        PlanSuggestion(
            plan=plan,
            text=f"Decisão do Conselho: {decision.description}",
            origin=PlanSuggestion.SuggestionSource.COUNCIL,
            order=start_order + idx,
            is_pending=True,
        )
        for idx, decision in enumerate(decisions)
    ]
    PlanSuggestion.objects.bulk_create(bulk)
    return len(bulk)


def _log_generation(
    plan: IndividualPlan,
    template: PitTemplate,
    created_sections: int,
    created_suggestions: int,
    created_pendings: int,
    created_council: int,
) -> None:
    PlanLogEntry.objects.create(
        plan=plan,
        action=PlanLogEntry.Action.GENERATED,
        message='Plano gerado a partir do modelo.',
        payload={
            'template_id': template.id,
            'template_version': template.version,
            'sections_created': created_sections,
            'suggestions_from_template': created_suggestions,
            'pending_transported': created_pendings,
            'suggestions_from_council': created_council,
        },
    )


def render_plan_pdf(plan: IndividualPlan) -> bytes:
    """Renderiza um PIT em PDF (A4) com cabeçalho, tarefas e sugestões."""

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2 * cm,
        title=f"PIT {plan.period_label}",
    )

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.fontSize = 20
    title_style.leading = 24

    subtitle_style = ParagraphStyle(
        name='Subtitle',
        parent=styles['Heading2'],
        fontSize=12,
        leading=14,
        spaceAfter=6,
        textColor=colors.HexColor('#1f2937'),
    )

    section_heading_style = ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading3'],
        fontSize=12,
        leading=14,
        spaceBefore=12,
        spaceAfter=4,
        textColor=colors.HexColor('#0f172a'),
    )

    muted_style = ParagraphStyle(
        name='Muted',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#6b7280'),
    )

    body_style = ParagraphStyle(
        name='Body', parent=styles['BodyText'], leading=14, fontSize=11, spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        name='Bullet',
        parent=styles['BodyText'],
        fontSize=10,
        leading=13,
    )

    elements: list = []

    student_name = (plan.student.get_full_name() or plan.student.username) if plan.student_id else 'Aluno'
    class_name = plan.student_class.name if plan.student_class_id and plan.student_class else 'Turma'

    elements.append(Paragraph('Plano Individual de Trabalho', title_style))
    elements.append(Paragraph(f"{student_name} — {class_name}", subtitle_style))
    elements.append(Paragraph(plan.period_label, muted_style))
    elements.append(Spacer(1, 12))

    date_range = '—'
    if plan.start_date and plan.end_date:
        date_range = f"{plan.start_date.strftime('%d/%m/%Y')} → {plan.end_date.strftime('%d/%m/%Y')}"
    elif plan.start_date:
        date_range = plan.start_date.strftime('%d/%m/%Y')
    elif plan.end_date:
        date_range = plan.end_date.strftime('%d/%m/%Y')

    metadata_table = Table(
        [
            ['Estado', plan.get_status_display()],
            ['Período', plan.period_label],
            ['Datas', date_range],
            ['Modelo', plan.template.name if plan.template else '—'],
        ],
        colWidths=[3 * cm, 12 * cm],
        hAlign='LEFT',
    )
    metadata_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0f172a')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1f2937')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5f5')),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e2e8f0')),
            ]
        )
    )

    elements.append(metadata_table)

    if plan.general_objectives:
        elements.append(Paragraph('Objetivos gerais', section_heading_style))
        elements.append(Paragraph(plan.general_objectives, body_style))

    if plan.self_evaluation:
        elements.append(Paragraph('Autoavaliação do aluno', section_heading_style))
        elements.append(Paragraph(plan.self_evaluation, body_style))

    if plan.teacher_evaluation:
        elements.append(Paragraph('Avaliação do professor', section_heading_style))
        elements.append(Paragraph(plan.teacher_evaluation, body_style))

    sections = list(plan.sections.order_by('order', 'id'))
    tasks = list(plan.tasks.order_by('order', 'id'))
    tasks_by_section: dict[int | None, list] = {}

    for section in sections:
        tasks_by_section[section.id] = [
            task
            for task in tasks
            if section.area_code and task.subject == section.area_code or not section.area_code
        ]

    remaining_tasks = [task for task in tasks if not any(task in grouped for grouped in tasks_by_section.values())]

    if sections:
        elements.append(Paragraph('Áreas e tarefas', section_heading_style))
        for section in sections:
            elements.append(Paragraph(section.title, ParagraphStyle(name=f"SectionTitle-{section.id}", parent=body_style, fontSize=12, leading=14, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor('#1f2937'))))
            if section.area_code:
                elements.append(Paragraph(f"Disciplina: {section.area_code}", muted_style))
            section_tasks = tasks_by_section.get(section.id, [])
            if section_tasks:
                section_items = []
                for task in section_tasks:
                    display_state = task.get_state_display()
                    description = task.description
                    if task.subject and (not section.area_code or task.subject != section.area_code):
                        description = f"{task.description} ({task.subject})"
                    text = f"<b>{description}</b> — {display_state}"
                    if task.teacher_feedback:
                        text += f"<br/><font size=9 color='#64748b'>Feedback: {task.teacher_feedback}</font>"
                    if task.evidence_link:
                        text += f"<br/><font size=9 color='#0ea5e9'>Evidência: {task.evidence_link}</font>"
                    section_items.append(ListItem(Paragraph(text, bullet_style), leftIndent=0, bulletColor=colors.HexColor('#0f172a')))
                elements.append(
                    ListFlowable(
                        section_items,
                        bulletType='bullet',
                        start='circle',
                        bulletFontName='Helvetica',
                        bulletFontSize=8,
                        leftPadding=12,
                        bulletDedent=6,
                    )
                )
            else:
                elements.append(Paragraph('Sem tarefas associadas.', muted_style))

    if remaining_tasks:
        elements.append(Paragraph('Outras tarefas', section_heading_style))
        remaining_items = []
        for task in remaining_tasks:
            description = task.description
            if task.subject:
                description = f"{task.description} ({task.subject})"
            text = f"<b>{description}</b> — {task.get_state_display()}"
            remaining_items.append(ListItem(Paragraph(text, bullet_style)))
        elements.append(
            ListFlowable(
                remaining_items,
                bulletType='bullet',
                start='circle',
                leftPadding=12,
                bulletDedent=6,
            )
        )

    suggestions = list(plan.suggestions.order_by('order', 'id'))
    if suggestions:
        elements.append(Paragraph('Sugestões e pendências', section_heading_style))
        suggestion_items = []
        for suggestion in suggestions:
            origin_display = suggestion.get_origin_display()
            text = f"<b>{suggestion.text}</b>"
            details: list[str] = []
            if origin_display:
                details.append(origin_display)
            if suggestion.is_pending:
                details.append('Pendente')
            if details:
                text += f"<br/><font size=9 color='#64748b'>{' · '.join(details)}</font>"
            suggestion_items.append(ListItem(Paragraph(text, bullet_style)))
        elements.append(
            ListFlowable(
                suggestion_items,
                bulletType='bullet',
                start='circle',
                leftPadding=12,
                bulletDedent=6,
            )
        )

    document.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def log_plan_event(
    *,
    plan: IndividualPlan,
    action: PlanLogEntry.Action,
    actor=None,
    message: str = '',
    payload: Optional[dict] = None,
) -> PlanLogEntry:
    """Cria um registo de auditoria para o plano."""

    entry = PlanLogEntry.objects.create(
        plan=plan,
        action=action,
        message=message,
        payload=payload or {},
        actor=actor,
    )
    return entry
