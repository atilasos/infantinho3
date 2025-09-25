from __future__ import annotations

import itertools
import math
import os
import random
import uuid
from collections import Counter, defaultdict
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from django.utils import timezone

from ai.models import AIInteractionSession, AIRequest, AIResponseLog, AIUsageQuota, LearnerContextSnapshot, TeacherFocusArea
from blog.models import Comment, Post
from checklists.models import ChecklistItem, ChecklistMark, ChecklistStatus, ChecklistTemplate
from classes.models import Class
from council.models import CouncilDecision, StudentProposal
from demo.models import DemoBatch, DemoRecord
from diary.models import DiaryEntry, DiarySession
from pit.models import (
    IndividualPlan,
    PlanTask,
    PitTemplate,
    TemplateSection,
    TemplateSuggestion,
)
from pit.services import generate_weekly_plan
from projects.models import Project, ProjectTask
from users.models import GuardianRelation

User = get_user_model()

DEFAULT_PASSWORD = 'demo1234'
DEFAULT_SEED = 42
DEFAULT_CLASSES = 2
DEFAULT_STUDENTS = 10
MAX_LABEL_LENGTH = 120

ROLE_GROUPS = {
    'admin': 'administrador',
    'professor': 'professor',
    'aluno': 'aluno',
    'encarregado': 'encarregado',
}

FIRST_NAMES = [
    'Ana', 'Bruno', 'Carla', 'Diogo', 'Eva', 'Filipe', 'Gonçalo', 'Helena', 'Inês', 'João',
    'Leonor', 'Miguel', 'Nuno', 'Olívia', 'Paula', 'Rita', 'Sofia', 'Tiago', 'Vera', 'Xavier',
]
LAST_NAMES = [
    'Almeida', 'Barbosa', 'Carvalho', 'Domingues', 'Esteves', 'Ferreira', 'Gonçalves', 'Henriques',
    'Igrejas', 'Jardim', 'Leal', 'Matos', 'Neves', 'Oliveira', 'Pereira', 'Queirós', 'Ribeiro',
    'Soares', 'Teixeira', 'Valente', 'Xavier',
]
DISCIPLINES = ['Português', 'Matemática', 'Estudo do Meio', 'Inglês', 'Cidadania']
PROJECT_TOPICS = ['Jardim Sensorial', 'Feira de Ciências', 'Rádio da Escola', 'Revista da Turma', 'Exposição de Arte']
COUNCIL_DECISIONS = [
    'Organizar escala de responsabilidade pela biblioteca de sala.',
    'Preparar apresentação para partilhar aprendizagens com o 6.º ano.',
    'Reforçar momentos de leitura silenciosa antes do conselho semanal.',
]
COUNCIL_PROPOSALS = [
    'Gostava que organizássemos um torneio de xadrez na sala.',
    'Proponho criarmos um espaço verde com plantas aromáticas.',
    'Sugiro revisitarmos as regras de utilização do tablet na sala.',
]


class DemoSeeder:
    def __init__(self, *, batch: DemoBatch, classes: int, students_per_class: int, rng: random.Random, stdout):
        self.batch = batch
        self.classes = classes
        self.students_per_class = students_per_class
        self.rng = rng
        self.stdout = stdout
        self._content_types = {}
        self._records: list[DemoRecord] = []
        self._recorded_keys: set[tuple[int, int]] = set()
        self.summary = Counter()
        self.login_rows: list[tuple[str, str, str]] = []
        self.demo_teachers: list[User] = []
        self.demo_students: list[User] = []
        self.demo_guardians: list[User] = []
        self.demo_classes: list[Class] = []
        self.now = timezone.now()

    # ---------------------------
    # helpers
    # ---------------------------
    def mark(self, obj, label: str = '') -> None:
        ct = self._content_types.get(type(obj))
        if ct is None:
            ct = ContentType.objects.get_for_model(obj, for_concrete_model=False)
            self._content_types[type(obj)] = ct
        key = (ct.id, obj.pk)
        if key in self._recorded_keys:
            return
        self._recorded_keys.add(key)
        self._records.append(
            DemoRecord(
                batch=self.batch,
                content_type=ct,
                object_id=obj.pk,
                label=label[:MAX_LABEL_LENGTH],
            )
        )

    def persist_records(self) -> None:
        if self._records:
            DemoRecord.objects.bulk_create(self._records, batch_size=500)
            self.stdout.write(f'Registos demo armazenados ({len(self._records)})')

    def unique_email(self, prefix: str) -> str:
        token = uuid.uuid4().hex[:6]
        return f'{prefix}.{token}@demo.infantinho.pt'.lower()

    def make_user(self, *, role: str, first_name: str, last_name: str, username: str | None = None, is_staff=False, is_superuser=False) -> User:
        if not username:
            username = f'{first_name}.{last_name}'.lower().replace(' ', '.')
            username = f'{username}@demo.infantinho.pt'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': username,
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
                'is_staff': is_staff,
                'is_superuser': is_superuser,
            },
        )
        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.status = 'ativo'
            user.save()
            self.mark(user, f'{role} {username}')
        else:
            # ensure role and flags reflect demo run
            update_fields = []
            if user.role != role:
                user.role = role
                update_fields.append('role')
            target_status = 'ativo'
            if getattr(user, 'status', None) != target_status:
                user.status = target_status
                update_fields.append('status')
            if is_staff and not user.is_staff:
                user.is_staff = True
                update_fields.append('is_staff')
            if is_superuser and not user.is_superuser:
                user.is_superuser = True
                update_fields.append('is_superuser')
            if update_fields:
                user.save(update_fields=update_fields)
        group_name = ROLE_GROUPS.get(role)
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        self.summary[f'users_{role}'] += 1
        self.login_rows.append((user.email, DEFAULT_PASSWORD, role))
        return user

    # ---------------------------
    def seed(self):
        self.stdout.write('> A preparar dados demo...')
        self.ensure_groups()
        self.create_admin()
        self.create_teachers_and_classes()
        self.create_students_and_guardians()
        self.create_blog_content()
        self.create_checklists()
        self.create_pits()
        self.create_projects()
        self.create_council_records()
        self.create_diary_entries()
        self.create_ai_traces()
        self.stdout.write('Dados demo criados.')

    def ensure_groups(self):
        for internal, name in ROLE_GROUPS.items():
            Group.objects.get_or_create(name=name)
        self.stdout.write('  Grupos verificados.')

    def create_admin(self):
        admin = self.make_user(
            role='admin',
            first_name='Carla',
            last_name='Direção',
            username='admin@demo.infantinho.pt',
            is_staff=True,
            is_superuser=True,
        )
        self.summary['admins'] += 1
        self.demo_admin = admin

    def pick_name(self):
        first = self.rng.choice(FIRST_NAMES)
        last = self.rng.choice(LAST_NAMES)
        return first, last

    def create_teachers_and_classes(self):
        base_year = date.today().year
        for idx in range(self.classes):
            first, last = self.pick_name()
            username = f'prof{idx+1}@demo.infantinho.pt'
            teacher = self.make_user(role='professor', first_name=first, last_name=last, username=username, is_staff=True)
            self.demo_teachers.append(teacher)

            class_name = f"{5 + idx}º {chr(65 + idx)} Demo"
            turma = Class.objects.create(name=class_name, year=base_year)
            turma.teachers.add(teacher)
            self.mark(turma, f'Classe {class_name}')
            self.demo_classes.append(turma)
            self.summary['classes'] += 1
        self.stdout.write(f'  Criadas {len(self.demo_classes)} turmas demo.')

    def create_students_and_guardians(self):
        guardian_cycle = itertools.cycle(range(1, math.ceil(self.students_per_class / 2) + 1))
        for turma in self.demo_classes:
            class_students = []
            for idx in range(self.students_per_class):
                first, last = self.pick_name()
                username = f'{first}.{last}.{turma.pk}@demo.infantinho.pt'.lower()
                student = self.make_user(role='aluno', first_name=first, last_name=last, username=username)
                turma.students.add(student)
                self.mark(student, f'Aluno {turma.name}')
                class_students.append(student)
                self.summary['students'] += 1
            self.demo_students.extend(class_students)

            # guardians – pair every two students with one guardian
            iterator = iter(class_students)
            for pair in itertools.zip_longest(iterator, iterator):
                students = [student for student in pair if student is not None]
                if not students:
                    continue
                first, last = self.pick_name()
                number = next(guardian_cycle)
                username = f'enc.{turma.pk}.{number}@demo.infantinho.pt'
                guardian = self.make_user(role='encarregado', first_name=first, last_name=last, username=username)
                for student in students:
                    relation, _ = GuardianRelation.objects.get_or_create(aluno=student, encarregado=guardian)
                    self.mark(relation, f'Encarregado {guardian.email}')
                self.demo_guardians.append(guardian)
                self.summary['guardians'] += 1
        self.stdout.write('  Alunos e encarregados associados às turmas.')

    def create_blog_content(self):
        lorem_sentences = [
            'Hoje explorámos frações com recurso a materiais manipuláveis.',
            'Durante o trabalho autónomo, o grupo B apresentou o relatório do projeto.',
            'Os alunos demonstraram grande colaboração na organização do espaço da sala.',
            'Fizemos uma roda de leitura partilhada com textos informativos.',
            'O conselho de turma decidiu rever as regras de utilização dos tablets.',
        ]
        for turma, teacher in zip(self.demo_classes, self.demo_teachers):
            # teacher posts
            for i in range(3):
                content = ' '.join(self.rng.sample(lorem_sentences, k=3))
                categoria = self.rng.choice([choice[0] for choice in Post.CATEGORIA_CHOICES])
                status = 'PUBLISHED' if i < 2 else 'PENDING'
                post = Post.objects.create(
                    turma=turma,
                    autor=teacher,
                    titulo=f'Registo {i+1} da {turma.name}',
                    conteudo=content,
                    categoria=categoria,
                    status=status,
                    approved_by=teacher if status == 'PUBLISHED' else None,
                    approved_at=self.now if status == 'PUBLISHED' else None,
                )
                self.mark(post, 'Post demo professor')
                self.summary['posts'] += 1

            # student posts
            for student in turma.students.all():
                content = ' '.join(self.rng.sample(lorem_sentences, k=2))
                status = self.rng.choice(['PENDING', 'PUBLISHED'])
                post = Post.objects.create(
                    turma=turma,
                    autor=student,
                    titulo=f'Reflexão {student.first_name}',
                    conteudo=content,
                    categoria='REFLEXAO',
                    status=status,
                    approved_by=teacher if status == 'PUBLISHED' else None,
                    approved_at=self.now if status == 'PUBLISHED' else None,
                )
                self.mark(post, 'Post demo aluno')
                self.summary['posts'] += 1

                # comments from teacher & peers
                comments = [
                    (teacher, 'Gostei da forma como organizaste o teu trabalho!'),
                    (self.rng.choice(list(turma.students.all())), 'Também tive dificuldade em fracionar, podemos treinar juntos.'),
                ]
                for author, text in comments:
                    comment = Comment.objects.create(post=post, autor=author, conteudo=text)
                    self.mark(comment, 'Comentário demo')
                    self.summary['comments'] += 1
        self.stdout.write('  Blog/diário reforçados com publicações demo.')

    def ensure_templates(self) -> list[ChecklistTemplate]:
        templates = list(ChecklistTemplate.objects.all()[:2])
        if templates:
            return templates
        # create fallback template
        template = ChecklistTemplate.objects.create(
            name='Português 5.º ano (Demo)',
            description='Metas principais de leitura e escrita para demonstração.',
        )
        items = [
            ChecklistItem(template=template, code='L1', text='Ler textos narrativos com entoação adequada', order=1),
            ChecklistItem(template=template, code='E2', text='Escrever pequenos relatos com ortografia correta', order=2),
            ChecklistItem(template=template, code='O3', text='Participar em discussões respeitando a vez de falar', order=3),
        ]
        ChecklistItem.objects.bulk_create(items)
        template.refresh_from_db()
        self.mark(template, 'Template checklist demo')
        for item in template.items.all():
            self.mark(item, 'Item checklist demo')
        return [template]

    def create_checklists(self):
        templates = self.ensure_templates()
        mark_cycle = ['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'VALIDATED']
        state_cycle = [
            ChecklistStatus.LVState.DRAFT,
            ChecklistStatus.LVState.SUBMITTED,
            ChecklistStatus.LVState.NEEDS_REVISION,
            ChecklistStatus.LVState.VALIDATED,
        ]
        for student in self.demo_students:
            turma = student.classes_attended.first()
            for template in templates:
                state = self.rng.choice(state_cycle)
                status = ChecklistStatus.objects.create(
                    template=template,
                    student=student,
                    student_class=turma,
                    template_version=template.version,
                    state=state,
                    student_notes='Notas registadas automaticamente para demonstração.'
                )
                if state in {ChecklistStatus.LVState.SUBMITTED, ChecklistStatus.LVState.NEEDS_REVISION, ChecklistStatus.LVState.VALIDATED}:
                    status.submitted_at = timezone.now() - timedelta(days=self.rng.randint(1, 5))
                    status.save(update_fields=['submitted_at'])
                self.mark(status, 'Checklist status')
                marks_to_create = []
                for item in template.items.all():
                    mark_status = self.rng.choice(mark_cycle)
                    mark = ChecklistMark(
                        status_record=status,
                        item=item,
                        mark_status=mark_status,
                        marked_by=student if mark_status in {'IN_PROGRESS', 'COMPLETED'} else turma.teachers.first(),
                        teacher_validated=mark_status == 'VALIDATED',
                    )
                    marks_to_create.append(mark)
                created_marks = ChecklistMark.objects.bulk_create(marks_to_create)
                for mark in created_marks:
                    self.mark(mark, 'Checklist mark')
                status.update_percent_complete()
                self.summary['checklists'] += 1
        self.stdout.write('  Checklists preenchidas com estados variados.')

    def create_pit_templates(self) -> list[PitTemplate]:
        if hasattr(self, '_pit_templates'):
            return self._pit_templates

        templates = list(PitTemplate.objects.order_by('-updated_at')[:3])
        if templates:
            self._pit_templates = templates
            return templates

        creator = self.demo_teachers[0] if self.demo_teachers else None
        template = PitTemplate.objects.create(
            name='PIT Semanal MEM (Demo)',
            description='Modelo base semanal com áreas TEA, Projetos e Comunidade.',
            cycle_label='2.º ciclo',
            version=1,
            created_by=creator,
        )
        sections = TemplateSection.objects.bulk_create(
            [
                TemplateSection(template=template, title='Trabalho de Estudo Autónomo', area_code='TEA', order=1),
                TemplateSection(template=template, title='Projetos e Comunicações', area_code='PROJETOS', order=2),
                TemplateSection(template=template, title='Comunidade e Tarefas da Turma', area_code='COMUNIDADE', order=3),
            ]
        )
        suggestions = TemplateSuggestion.objects.bulk_create(
            [
                TemplateSuggestion(template=template, section=sections[0], text='Rever leitura diária durante TEA.', order=1),
                TemplateSuggestion(template=template, section=sections[1], text='Preparar comunicação do projeto cooperativo.', order=2),
                TemplateSuggestion(template=template, section=sections[2], text='Organizar responsabilidades da sala.', order=3, is_pending=True),
            ]
        )
        self.mark(template, 'Modelo PIT demo')
        for section in sections:
            self.mark(section, 'Secção modelo PIT')
        for suggestion in suggestions:
            self.mark(suggestion, 'Sugestão modelo PIT')

        self._pit_templates = [template]
        return self._pit_templates

    @staticmethod
    def week_bounds(target: date) -> tuple[date, date]:
        start = target - timedelta(days=target.weekday())
        end = start + timedelta(days=6)
        return start, end

    def _get_or_generate_plan(self, *, student: User, turma: Class, target_date: date):
        try:
            result = generate_weekly_plan(student=student, student_class=turma, target_date=target_date)
            return result.plan
        except ValidationError:
            start, end = self.week_bounds(target_date)
            label = f"Semana {start.strftime('%d/%m')} – {end.strftime('%d/%m')}"
            plan = (
                IndividualPlan.objects.filter(student=student, student_class=turma, period_label=label)
                .order_by('-created_at')
                .first()
            )
            return plan

    def _populate_plan_tasks(self, plan: IndividualPlan) -> None:
        plan.tasks.all().delete()
        discipline_pool = DISCIPLINES[:]
        self.rng.shuffle(discipline_pool)
        tasks = []
        for idx in range(1, 5):
            discipline = discipline_pool[idx % len(discipline_pool)]
            state = self.rng.choice([
                PlanTask.TaskState.PENDING,
                PlanTask.TaskState.IN_PROGRESS,
                PlanTask.TaskState.DONE,
                PlanTask.TaskState.VALIDATED,
            ])
            tasks.append(
                PlanTask(
                    plan=plan,
                    description=f'{discipline}: atividade #{idx}',
                    subject=discipline,
                    state=state,
                    order=idx,
                )
            )
        created = PlanTask.objects.bulk_create(tasks)
        for task in created:
            self.mark(task, 'PIT tarefa')

    def _prepare_plan_common(self, plan: IndividualPlan, *, status: str, objectives: str, start: date, end: date) -> None:
        plan.general_objectives = objectives
        plan.status = status
        plan.start_date = start
        plan.end_date = end
        plan.save(update_fields=['general_objectives', 'status', 'start_date', 'end_date', 'updated_at'])
        self._populate_plan_tasks(plan)
        self.mark(plan, 'PIT demo')
        for suggestion in plan.suggestions.all():
            self.mark(suggestion, 'PIT sugestão')
        for section in plan.sections.all():
            self.mark(section, 'PIT secção')

    def create_pits(self):
        templates = self.create_pit_templates()
        active_cycle = [
            IndividualPlan.PlanStatus.DRAFT,
            IndividualPlan.PlanStatus.SUBMITTED,
            IndividualPlan.PlanStatus.APPROVED,
            IndividualPlan.PlanStatus.CONCLUDED,
        ]

        for index, student in enumerate(self.demo_students):
            turma = student.classes_attended.first()
            if not turma:
                continue

            # plano ativo (semana atual)
            active_target = date.today()
            active_plan = self._get_or_generate_plan(student=student, turma=turma, target_date=active_target)
            if not active_plan:
                continue
            start, end = self.week_bounds(active_target)
            active_status = active_cycle[index % len(active_cycle)]
            self._prepare_plan_common(
                active_plan,
                status=active_status,
                objectives='Consolidar operações com frações e melhorar a leitura expressiva.',
                start=start,
                end=end,
            )
            self.summary['pits'] += 1

            # plano histórico avaliado
            history_target = active_target - timedelta(days=21)
            history_plan = self._get_or_generate_plan(student=student, turma=turma, target_date=history_target)
            if history_plan and history_plan.id != active_plan.id:
                h_start, h_end = self.week_bounds(history_target)
                self._prepare_plan_common(
                    history_plan,
                    status=IndividualPlan.PlanStatus.EVALUATED,
                    objectives='Plano concluído com foco em leitura orientada e escrita criativa.',
                    start=h_start,
                    end=h_end,
                )
                history_plan.self_evaluation = 'Refleti sobre o meu progresso e identifiquei próximas metas.'
                history_plan.teacher_evaluation = 'Professor validou as aprendizagens e recomendou reforço em leitura expressiva.'
                history_plan.save(update_fields=['self_evaluation', 'teacher_evaluation', 'updated_at'])
                self.summary['pits'] += 1

        self.stdout.write('  PITs criados com planos ativos e histórico avaliado.')

    def create_projects(self):
        for turma in self.demo_classes:
            topic = self.rng.choice(PROJECT_TOPICS)
            project = Project.objects.create(
                student_class=turma,
                title=f'Projeto {topic}',
                description='Projeto cooperativo exemplo para demonstração.',
                state=self.rng.choice(['active', 'completed']),
                start_date=date.today() - timedelta(days=20),
                end_date=date.today() + timedelta(days=30),
                product_description='Apresentação multimédia e protótipo simples.',
            )
            members = list(turma.students.all()[:4]) + [turma.teachers.first()]
            project.members.set(members)
            self.mark(project, 'Projeto demo')
            tasks = []
            for order, task_label in enumerate([
                'Pesquisa inicial',
                'Planeamento do protótipo',
                'Construção e testes',
                'Apresentação final',
            ], start=1):
                tasks.append(
                    ProjectTask(
                        project=project,
                        description=task_label,
                        responsible=self.rng.choice(members),
                        due_date=date.today() + timedelta(days=order * 5),
                        state=self.rng.choice(['todo', 'in_progress', 'done']),
                        order=order,
                    )
                )
            created_tasks = ProjectTask.objects.bulk_create(tasks)
            for task in created_tasks:
                self.mark(task, 'Projeto tarefa')
            self.summary['projects'] += 1
        self.stdout.write('  Projetos cooperativos preenchidos com tarefas.')

    def create_council_records(self):
        for turma in self.demo_classes:
            for text in self.rng.sample(COUNCIL_DECISIONS, k=3):
                decision = CouncilDecision.objects.create(
                    student_class=turma,
                    date=date.today() - timedelta(days=self.rng.randint(1, 20)),
                    description=text,
                    category=self.rng.choice([choice[0] for choice in CouncilDecision.Category.choices]),
                    status=self.rng.choice([choice[0] for choice in CouncilDecision.Status.choices]),
                    responsible=self.rng.choice(list(turma.students.all()) + [turma.teachers.first()]),
                )
                self.mark(decision, 'Decisão conselho')
                self.summary['council_decisions'] += 1
            for text in self.rng.sample(COUNCIL_PROPOSALS, k=2):
                proposal = StudentProposal.objects.create(
                    student_class=turma,
                    author=self.rng.choice(list(turma.students.all())),
                    text=text,
                    status=self.rng.choice([choice[0] for choice in StudentProposal.ProposalStatus.choices]),
                )
                self.mark(proposal, 'Proposta conselho')
                self.summary['council_proposals'] += 1
        self.stdout.write('  Conselho de turma povoado com decisões e propostas.')

    def create_diary_entries(self):
        for turma in self.demo_classes:
            session = DiarySession.objects.create(
                turma=turma,
                start_date=date.today() - timedelta(days=7),
                status='ACTIVE',
            )
            self.mark(session, 'Diário sessão')
            entries = []
            for column in ['GOSTEI', 'NAO_GOSTEI', 'FIZEMOS', 'QUEREMOS']:
                author = self.rng.choice(list(turma.students.all()) + [turma.teachers.first()])
                entries.append(
                    DiaryEntry(
                        session=session,
                        column=column,
                        content=f'Registo {column.lower()} da {turma.name}.',
                        author=author,
                    )
                )
            created = DiaryEntry.objects.bulk_create(entries)
            for entry in created:
                self.mark(entry, 'Diário entrada')
            self.summary['diary_entries'] += len(created)
        self.stdout.write('  Diário de turma preparado.')

    def create_ai_traces(self):
        # Pequena simulação para demonstrar histórico IA no admin
        for student in self.demo_students[: min(5, len(self.demo_students))]:
            turma = student.classes_attended.first()
            session = AIInteractionSession.objects.create(
                user=student,
                persona='student',
                origin_app='checklists',
                class_context=turma,
                context_descriptor='Demo IA',
                context_payload={'demo': True},
            )
            self.mark(session, 'Sessão IA demo')
            request = AIRequest.objects.create(
                session=session,
                user=student,
                persona='student',
                origin_app='checklists',
                raw_query='O que posso estudar a seguir?',
                optimized_prompt='Ajuda o aluno a escolher próximo objetivo.',
                optimizer_trace={'demo': True},
                intent_label='orientacao',
                target_model='gpt-5-mini',
                resolved_model='gpt-5-mini',
                status='completed',
                input_tokens=120,
                output_tokens=180,
                cost_estimate=0.00045,
                latency_ms=820,
            )
            self.mark(request, 'Pedido IA demo')
            response = AIResponseLog.objects.create(
                request=request,
                response_text='Sugiro rever frações e praticar leitura expressiva.',
                model_metadata={'demo': True},
                guardrail_decision={'allow': True},
                used_cache=False,
                user_feedback=self.rng.choice(['helpful', 'neutral', 'not_helpful']),
            )
            self.mark(response, 'Resposta IA demo')
            quota = AIUsageQuota.objects.create(
                scope=AIUsageQuota.SCOPE_USER,
                user=student,
                class_context=turma,
                period_start=date.today(),
                period_end=date.today(),
                max_requests=12,
                requests_made=2,
                max_cost=0.005,
                cost_accumulated=0.0012,
            )
            self.mark(quota, 'Quota IA demo')
            snapshot = LearnerContextSnapshot.objects.create(
                student=student,
                class_context=turma,
                summary='Aluno demonstra curiosidade e progressos em leitura.',
                strengths=['Leitura expressiva', 'Participação em grupo'],
                needs=['Consolidar frações'],
                mem_competencies={'autonomia': 'a desenvolver', 'cooperação': 'muito bom'},
            )
            self.mark(snapshot, 'Snapshot aprendizagem demo')
        if self.demo_classes:
            focus = TeacherFocusArea.objects.create(
                teacher=self.demo_teachers[0],
                class_context=self.demo_classes[0],
                focus_text='Acompanhar os alunos com dificuldades em cálculo mental.',
                priority='high',
            )
            self.mark(focus, 'Foco pedagógico demo')
        self.stdout.write('  Registos de IA simulados para auditoria.')


class Command(BaseCommand):
    help = 'Cria ou remove dados demo para o Infantinho 3.0.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Limpa e volta a criar dados demo.')
        parser.add_argument('--clean', action='store_true', help='Remove dados demo sem recriar.')
        parser.add_argument('--classes', type=int, default=DEFAULT_CLASSES, help='Número de turmas demo a criar (default: %(default)s).')
        parser.add_argument('--alunos', type=int, default=DEFAULT_STUDENTS, help='Número de alunos por turma (default: %(default)s).')
        parser.add_argument('--seed', type=int, default=DEFAULT_SEED, help='Seed de aleatoriedade (default: %(default)s).')

    def handle(self, *args, **options):
        if options['reset'] and options['clean']:
            raise CommandError('Use apenas uma opção entre --reset e --clean.')

        if not settings.DEBUG and os.environ.get('ALLOW_DEMO_SEED') != '1':
            raise CommandError('Comando disponível apenas em DEBUG ou com ALLOW_DEMO_SEED=1.')

        if options['classes'] < 1:
            raise CommandError('Indique pelo menos 1 turma.')
        if options['alunos'] < 1:
            raise CommandError('Indique pelo menos 1 aluno por turma.')

        if options['clean']:
            self.clean_demo_data()
            self.ensure_database_ready()
            return

        if options['reset']:
            self.clean_demo_data()
            self.ensure_database_ready()
        elif DemoRecord.objects.exists():
            self.stdout.write(self.style.WARNING('Já existem dados demo. Use --reset para recriar ou --clean para remover.'))
            return
        else:
            self.ensure_database_ready()

        rng = random.Random(options['seed'])
        batch = DemoBatch.objects.create(description=f"{options['classes']} turmas × {options['alunos']} alunos")
        self.stdout.write(self.style.SUCCESS(f'Batch demo {batch.id} criado.'))

        seeder = DemoSeeder(
            batch=batch,
            classes=options['classes'],
            students_per_class=options['alunos'],
            rng=rng,
            stdout=self.stdout,
        )

        with transaction.atomic():
            seeder.seed()
            seeder.persist_records()

        self.print_summary(seeder)

    # -------------------------------------------------
    def clean_demo_data(self):
        records = DemoRecord.objects.select_related('content_type', 'batch').order_by('-created_at')
        if not records.exists():
            self.stdout.write('Não há dados demo para remover.')
            return

        counts = Counter()
        with transaction.atomic():
            for record in records:
                model = record.content_type.model_class()
                label = model.__name__ if model else 'Desconhecido'
                try:
                    obj = record.content_object
                    if obj is not None:
                        obj.delete()
                        counts[label] += 1
                except Exception as exc:  # pragma: no cover
                    self.stdout.write(self.style.WARNING(f'  Falha ao remover {label}#{record.object_id}: {exc}'))
                record.delete()
            DemoBatch.objects.filter(records__isnull=True).delete()

        self.stdout.write(self.style.SUCCESS('Dados demo removidos.'))
        for label, total in counts.items():
            self.stdout.write(f'  {label}: {total}')

    def ensure_database_ready(self):
        default_db = settings.DATABASES['default']
        engine = default_db.get('ENGINE', '')

        if engine.endswith('sqlite3'):
            db_name = default_db.get('NAME')
            if db_name:
                if not os.path.isabs(db_name):
                    db_name = os.path.join(settings.BASE_DIR, db_name)
                os.makedirs(os.path.dirname(db_name) or '.', exist_ok=True)

        connections.close_all()
        self.stdout.write('> A garantir estrutura de base de dados…')
        call_command('migrate', interactive=False, verbosity=0)

    def print_summary(self, seeder: DemoSeeder):
        self.stdout.write(self.style.MIGRATE_HEADING('Resumo dos dados demo'))
        for key, value in sorted(seeder.summary.items()):
            self.stdout.write(f'  {key}: {value}')

        self.stdout.write('\nLogins demo disponíveis:')
        self.stdout.write('  Email | Palavra-passe | Papel')
        for email, password, role in seeder.login_rows:
            self.stdout.write(f'  {email:40s} {password:12s} {role}')
