from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from users.decorators import group_required
from users.permissions import can_access_class, can_moderate_class
from classes.models import Class
from users.models import User, PreApprovedStudent # Adicionado PreApprovedStudent
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Avg, Count, Q, Prefetch, Max, F
from django.db import models
from django.db import IntegrityError # Para tratar emails duplicados
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse # Para redirecionamento

# Importar o novo formulário e o modelo PreApprovedStudent
from .forms import PreapproveStudentsForm, AssignChecklistForm # Adicionado AssignChecklistForm
from users.models import PreApprovedStudent # Modelo está na app users
from .models import Class # Modelo da turma local

import logging # Para logging
logger = logging.getLogger(__name__)

# Create your views here.

# --- Import models from other apps (handle potential ImportError if apps don't exist yet) ---
try:
    from diary.models import Post
    DIARY_APP_EXISTS = True
except ImportError:
    Post = None
    DIARY_APP_EXISTS = False

try:
    from checklists.models import ChecklistTemplate, ChecklistStatus, ChecklistItem, ChecklistMark
    CHECKLISTS_APP_EXISTS = True
except ImportError:
    ChecklistTemplate, ChecklistStatus, ChecklistItem, ChecklistMark = None, None, None, None
    CHECKLISTS_APP_EXISTS = False

@login_required
def class_list(request):
    user = request.user
    is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
    
    if is_admin:
        # Admins see all classes
        turmas = Class.objects.all().order_by('name')
    elif hasattr(user, 'role') and user.role == 'professor':
        # Teachers see classes they teach
        turmas = Class.objects.filter(teachers=user).order_by('name')
    else:
        # Students/Others see classes they attend
        turmas = Class.objects.filter(students=user).order_by('name') # Show classes attended
        
    return render(request, 'classes/class_list.html', {'turmas': turmas})

@login_required
def class_detail(request, class_id):
    turma = get_object_or_404(Class.objects.prefetch_related('teachers', 'students'), id=class_id)
    user = request.user
    
    # --- Permission Checks --- 
    can_view_class = can_access_class(user, turma) or (hasattr(user, 'role') and user.role == 'professor')
    can_create_post = can_moderate_class(user, turma)
    can_add_student = can_moderate_class(user, turma)

    if not can_view_class:
        messages.error(request, _("You do not have permission to view this class page."))
        return redirect('classes:class_list') # Redirect to class list or home
        
    # --- Prepare Context Data ---
    students = turma.students.all().order_by('last_name', 'first_name', 'username')
    student_count = students.count()

    # --- General Statistics ---
    stats = {
        'student_count': student_count,
        'recent_posts_count': 0,
        'checklist_template_count': 0,
        # Add more stats here later, e.g., average completion
    }

    if DIARY_APP_EXISTS and Post:
        one_week_ago = timezone.now() - timezone.timedelta(days=7)
        stats['recent_posts_count'] = Post.objects.filter(
            classe=turma,
            publish_date__gte=one_week_ago
        ).count()

    if CHECKLISTS_APP_EXISTS and ChecklistTemplate:
        # Option A: Count all available templates
        stats['checklist_template_count'] = ChecklistTemplate.objects.count()
        # Option B (alternative): Count templates actively used in this class
        # stats['checklist_template_count'] = ChecklistStatus.objects.filter(student_class=turma).values('template').distinct().count()

    # --- Student Progress Summary Data ---
    # This will be a list of dictionaries, one per student
    student_progress_list = []

    # Pre-fetch last post dates for efficiency if Diary app exists
    last_post_dates = {}
    if DIARY_APP_EXISTS and Post and student_count > 0:
        latest_posts = Post.objects.filter(classe=turma, author__in=students).values(
            'author_id'
        ).annotate(
            latest_date=Max('publish_date')
        ).order_by()
        last_post_dates = {item['author_id']: item['latest_date'] for item in latest_posts}

    # Prepare checklist data if Checklists app exists
    checklist_progress_data = {}
    if CHECKLISTS_APP_EXISTS and ChecklistStatus and ChecklistItem and student_count > 0:
        # Get all status records for students in THIS specific class
        class_statuses = ChecklistStatus.objects.filter(
            student_class=turma,
            student__in=students # Redundant due to student_class filter, but safe
        ).select_related('student', 'template').prefetch_related(
            Prefetch('marks', queryset=ChecklistMark.objects.filter(Q(mark_status='COMPLETED') | Q(mark_status='VALIDATED')))
            # Removed item prefetch here, count comes from template
            # Prefetch('template__items') # Potential performance hit if many templates/items
        )

        # Get total item counts for templates used in this class
        template_ids_used = class_statuses.values_list('template_id', flat=True).distinct()
        template_item_counts = ChecklistTemplate.objects.filter(
            id__in=template_ids_used
        ).annotate(
            num_items=Count('items')
        ).values('id', 'num_items')
        
        item_counts_dict = {item['id']: item['num_items'] for item in template_item_counts}
        
        # Aggregate progress per student (average across their assigned templates in this class)
        student_agg_progress = {}
        for status in class_statuses:
            student_id = status.student_id
            template_id = status.template_id
            total_items = item_counts_dict.get(template_id, 0)

            if total_items > 0:
                # Use the pre-fetched completed/validated marks
                completed_count = status.marks.count() # Count the prefetched marks
                # Calculate percentage for THIS status record
                percentage = round((completed_count / total_items) * 100) 
            else:
                percentage = 0 # Template has no items

            # Store percentage for each student/template pair
            if student_id not in student_agg_progress:
                student_agg_progress[student_id] = []
            student_agg_progress[student_id].append(percentage)

        # Calculate the average percentage for each student across their templates
        for student_id, percentages in student_agg_progress.items():
            if percentages:
                checklist_progress_data[student_id] = round(sum(percentages) / len(percentages))
            else:
                checklist_progress_data[student_id] = 0 # No applicable checklists found


    for student in students:
        student_data = {
            'student': student,
            'last_post_date': last_post_dates.get(student.id),
            'checklist_progress': checklist_progress_data.get(student.id, 0) # Default to 0% if no data
            # Add PIT status here later if needed
        }
        student_progress_list.append(student_data)


    context = {
        'turma': turma,
        'can_create_post': can_create_post,
        'can_add_student': can_add_student,
        'students': students, # Keep original student list for simple iteration if needed elsewhere
        'general_stats': stats,
        'student_progress_list': student_progress_list,
        'checklist_app_enabled': CHECKLISTS_APP_EXISTS, # Pass flags to template
        'diary_app_enabled': DIARY_APP_EXISTS,
    }
    return render(request, 'classes/class_detail.html', context)

@login_required
# @group_required('professor') # REMOVIDO - Verificação interna é suficiente
def add_student(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    # Check if request.user is one of the teachers of this specific class OR is an admin
    is_admin = request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin')
    is_teacher_of_class = turma.teachers.filter(id=request.user.id).exists()

    # Esta verificação interna é suficiente e correta para ambos os papéis
    if not (is_teacher_of_class or is_admin):
        messages.error(request, _('Only teachers of this class or administrators can add students.'))
        return redirect('classes:class_detail', class_id=class_id)

    # Find users eligible to be added (Guests without a role)
    # Note: Might need adjustment based on exact user flow (e.g., allowing selection from existing students not in *any* class?)
    convidados = User.objects.filter(role__isnull=True, status='convidado').exclude(classes_attended=turma).order_by('email')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if not user_id:
             messages.error(request, _('No user selected.'))
             return redirect('classes:add_student', class_id=class_id)

        user_to_add = get_object_or_404(User, id=user_id, role__isnull=True, status='convidado')

        # Promote user to 'aluno' role (assuming this method exists on User model)
        # This might involve setting user.role = 'aluno', user.status = 'ativo', user.save()
        try:
            # Ideal: Use a method on the User model if it exists
            user_to_add.promote_to_role('aluno') # Assumes this method sets role, status, and saves.
        except AttributeError:
            # Fallback: Manually set fields
            user_to_add.role = 'aluno'
            user_to_add.status = 'ativo'
            user_to_add.save()
        except CommandError as e: # Capturar erro se o grupo 'aluno' não existir
             logger.error(f"Erro ao promover utilizador {user_to_add.username} para aluno na turma {turma.id}: {e}", exc_info=True)
             messages.error(request, _("Erro ao atribuir o papel de aluno. Verifique se o grupo 'aluno' existe no sistema."))
             # Não adicionar à turma se a promoção falhou
             return redirect('classes:add_student', class_id=class_id)
        except Exception as e: # Capturar outros erros inesperados na promoção
             logger.error(f"Erro inesperado ao promover utilizador {user_to_add.username} para aluno na turma {turma.id}: {e}", exc_info=True)
             messages.error(request, _("Ocorreu um erro inesperado ao promover o utilizador."))
             # Não adicionar à turma se a promoção falhou
             return redirect('classes:add_student', class_id=class_id)

        # Add student to the class only if promotion was successful
        turma.students.add(user_to_add)
        # Mensagem em PT-PT conforme esperado nos testes
        messages.success(request, _('{user_name} promovido a aluno e adicionado à turma.').format(user_name=user_to_add.get_full_name() or user_to_add.username))
        return redirect('classes:class_detail', class_id=class_id) # Redirect back to class detail

    return render(request, 'classes/add_student.html', {'turma': turma, 'convidados': convidados})

class ClassCreateForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'year', 'teachers']
        widgets = {
            # Added placeholder and improved help text if possible via attrs
            'teachers': forms.SelectMultiple(attrs={'size': 8, 'data-placeholder': _('Select Teachers')}),
        }
        help_texts = {
            'teachers': _('Select one or more teachers for this class.'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the queryset for teachers is limited to actual professors
        self.fields['teachers'].queryset = User.objects.filter(role='professor').order_by('username')

@login_required
@group_required('professor', 'administrador')
def manage_classes(request):
    if request.method == 'POST':
        form = ClassCreateForm(request.POST)
        if form.is_valid():
            turma = form.save()
            messages.success(request, _('Class "{class_name}" created successfully!').format(class_name=turma.name))
            return redirect('classes:manage_classes')
        else:
             messages.error(request, _('Please correct the errors below.'))
    else:
        form = ClassCreateForm()
        # Queryset is already set in form's __init__

    turmas = Class.objects.all().order_by('-year', 'name').prefetch_related('teachers') # Prefetch teachers for efficiency
    return render(request, 'classes/manage_classes.html', {'form': form, 'turmas': turmas})

def landing_page(request):
    # Currently, it just renders the same template for everyone.
    # Future: Could fetch public blog posts for guests, redirect logged-in users, etc.
    return render(request, 'classes/landing.html')

# Updated student detail view
@login_required
def student_detail(request, class_id, student_id):
    turma = get_object_or_404(Class, id=class_id)
    student = get_object_or_404(User, id=student_id)
    user = request.user

    # --- Basic Permission Checks (Common for GET and POST) ---
    if student.role != 'aluno':
        messages.error(request, _("The requested user is not a student."))
        return redirect('classes:class_detail', class_id=class_id)
    if not turma.students.filter(id=student.id).exists():
        messages.error(request, _("This student is not enrolled in this class."))
        return redirect('classes:class_detail', class_id=class_id)

    is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
    is_teacher_of_class = turma.teachers.filter(id=user.id).exists()
    is_the_student_themselves = (user.id == student.id)
    can_view_student_detail = is_admin or is_teacher_of_class or is_the_student_themselves
    can_mark_checklist = is_admin or is_teacher_of_class # Only teachers/admins can mark items via POST

    if not can_view_student_detail:
        messages.error(request, _("You do not have permission to view this student's details."))
        return redirect('/') # Redirect non-viewers to home

    # --- POST Request Handling (Marking Checklist Item) ---
    if request.method == 'POST' and CHECKLISTS_APP_EXISTS:
        if not can_mark_checklist:
            messages.error(request, _("You do not have permission to mark checklist items."))
            return redirect('classes:student_detail', class_id=class_id, student_id=student_id)

        mark_id = request.POST.get('mark_id')
        item_id = request.POST.get('item_id')
        status_id = request.POST.get('status_id') # ID of the ChecklistStatus record
        new_mark_status = request.POST.get('new_mark_status')

        if not (item_id and status_id and new_mark_status):
            messages.error(request, _("Missing data to update checklist status."))
            return redirect('classes:student_detail', class_id=class_id, student_id=student_id)

        try:
            status_record = get_object_or_404(ChecklistStatus, id=status_id, student=student, student_class=turma)
            item = get_object_or_404(ChecklistItem, id=item_id, template=status_record.template)
            
            # Validate the new status
            valid_statuses = [choice[0] for choice in ChecklistMark.STATUS_CHOICES]
            if new_mark_status not in valid_statuses:
                 raise forms.ValidationError(_("Invalid status provided."))

            # Find existing mark or create a new one
            mark, created = ChecklistMark.objects.get_or_create(
                status_record=status_record,
                item=item,
                defaults={
                    'mark_status': new_mark_status,
                    'marked_by': user,
                    'marked_at': timezone.now(),
                    'teacher_validated': (new_mark_status in ['COMPLETED', 'VALIDATED'])
                }
            )

            if not created:
                # Update existing mark
                mark.mark_status = new_mark_status
                mark.marked_by = user
                mark.marked_at = timezone.now() # Update timestamp
                # Teacher marking as COMPLETED or VALIDATED sets validation flag
                if new_mark_status in ['COMPLETED', 'VALIDATED']:
                    mark.teacher_validated = True
                elif mark.mark_status != 'COMPLETED': # Unset validation if moving away from completed
                    mark.teacher_validated = False
                mark.save() # Let the model's save method handle percentage update

            messages.success(request, _("Checklist item '{item_code}' updated to '{status}'.").format(
                item_code=item.code or f"Item {item.id}", status=mark.get_mark_status_display()
            ))

        except (ChecklistStatus.DoesNotExist, ChecklistItem.DoesNotExist, forms.ValidationError) as e:
            messages.error(request, _("Error updating checklist item: {}").format(str(e)))
        except Exception as e:
            # Catch unexpected errors
            messages.error(request, _("An unexpected error occurred: {}").format(str(e)))
            # Consider logging the error here
        
        # Redirect back to the same page after POST to avoid resubmission issues
        return redirect('classes:student_detail', class_id=class_id, student_id=student_id)

    # --- GET Request Data Fetching ---
    student_checklists_data = []
    if CHECKLISTS_APP_EXISTS and ChecklistStatus:
        # Fetch status records for this student/class
        statuses = ChecklistStatus.objects.filter(
            student=student,
            student_class=turma
        ).select_related('template').prefetch_related(
            # Prefetch ALL items for the template to display them all
            Prefetch('template__items', queryset=ChecklistItem.objects.order_by('order', 'code'), to_attr='all_items'),
            # Prefetch existing marks for this status record
            Prefetch('marks', queryset=ChecklistMark.objects.select_related('item'), to_attr='existing_marks')
        ).order_by('template__name')
        
        # Organize data for template (mapping marks to items)
        for status in statuses:
            marks_dict = {mark.item_id: mark for mark in status.existing_marks}
            student_checklists_data.append({
                'status_record': status,
                'template': status.template,
                'items_with_marks': [
                    {
                        'item': item, 
                        'mark': marks_dict.get(item.id) # Get existing mark or None
                    } 
                    for item in status.template.all_items 
                ]
            })

    student_diary_posts = []
    if DIARY_APP_EXISTS and Post:
        student_diary_posts = Post.objects.filter(
            classe=turma,
            author=student
        ).order_by('-publish_date')[:10]

    # Prepare status choices for the form in the template
    checklist_mark_choices = []
    if CHECKLISTS_APP_EXISTS:
        checklist_mark_choices = ChecklistMark.STATUS_CHOICES
        # Optional: Filter choices based on user role (e.g., student can only mark up to COMPLETED)
        # if not can_mark_checklist: # i.e., if student is viewing
        #    checklist_mark_choices = [c for c in checklist_mark_choices if c[0] != 'VALIDATED']
        
    context = {
        'turma': turma,
        'student': student,
        'student_checklists_data': student_checklists_data, # Changed context variable name
        'student_diary_posts': student_diary_posts,
        'checklist_app_enabled': CHECKLISTS_APP_EXISTS,
        'diary_app_enabled': DIARY_APP_EXISTS,
        'pit_app_enabled': False,
        'projects_app_enabled': False,
        'checklist_mark_choices': checklist_mark_choices,
        'can_mark_checklist': can_mark_checklist, # Pass permission flag to template
    }

    return render(request, 'classes/student_detail.html', context)

# Helper para verificar permissão (professor da turma ou admin)
def user_is_teacher_or_admin_for_class(user, class_obj):
    if not user.is_authenticated:
        return False
    is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
    is_teacher = class_obj.teachers.filter(id=user.id).exists()
    return is_admin or is_teacher

@login_required
def preapprove_students(request, class_id):
    """
    View para professores/admins adicionarem emails de alunos pré-aprovados para uma turma.
    Permite colar lista ou fazer upload de ficheiro.
    """
    turma = get_object_or_404(Class, id=class_id)
    user = request.user

    # Verificar Permissões
    if not user_is_teacher_or_admin_for_class(user, turma):
        messages.error(request, "Não tem permissão para gerir alunos pré-aprovados para esta turma.")
        # Redirecionar para a página da turma ou lista de turmas
        return redirect('classes:class_detail', class_id=turma.id) 

    added_count = 0
    skipped_count = 0
    failed_emails = [] # Emails que não foram adicionados por erro inesperado
    existing_emails = [] # Emails que já estavam na BD (mesmo que Claimed)

    if request.method == 'POST':
        form = PreapproveStudentsForm(request.POST, request.FILES)
        if form.is_valid():
            valid_emails = form.cleaned_data['valid_emails']
            
            for email in valid_emails:
                # Verificar se já existe um registo para este email
                if PreApprovedStudent.objects.filter(email__iexact=email).exists():
                     existing_emails.append(email)
                     skipped_count += 1
                     continue # Passa para o próximo email

                # Tentar criar o novo registo
                try:
                    PreApprovedStudent.objects.create(
                        email=email, # Já está em minúsculas do formulário
                        class_instance=turma,
                        added_by=user,
                        status='Pending' # Default, mas explícito aqui
                    )
                    added_count += 1
                except IntegrityError: 
                    # Deveria ser apanhado pelo .exists() acima, mas segurança extra
                    existing_emails.append(email)
                    skipped_count += 1
                    logger.warning(f"IntegrityError ao tentar adicionar {email} para a turma {turma.id}, mas a verificação de existência falhou?")
                except Exception as e:
                    # Outro erro inesperado durante a criação
                    failed_emails.append(email)
                    skipped_count += 1
                    logger.error(f"Erro inesperado ao criar PreApprovedStudent para {email} na turma {turma.id}: {e}", exc_info=True)

            # Mensagens de feedback
            if added_count > 0:
                messages.success(request, f"{added_count} email(s) de aluno(s) pré-aprovado(s) adicionado(s) com sucesso.")
            if existing_emails:
                 messages.warning(request, f"{len(existing_emails)} email(s) não foram adicionados porque já existem no sistema: {', '.join(existing_emails)}")
            if failed_emails:
                 messages.error(request, f"Ocorreu um erro ao tentar adicionar os seguintes emails: {', '.join(failed_emails)}. Contacte o administrador.")
            
            # Limpar o formulário após sucesso parcial ou total
            form = PreapproveStudentsForm() 
            # Ou redirecionar para a mesma página com GET para evitar re-POST
            # return redirect('classes:preapprove_students', class_id=turma.id)
            
        # Se o formulário não for válido, os erros serão mostrados automaticamente pelo template
    
    else: # Método GET
        form = PreapproveStudentsForm()

    # Obter a lista de alunos já pré-aprovados (pendentes e reivindicados) para esta turma
    preapproved_list = PreApprovedStudent.objects.filter(class_instance=turma).select_related('added_by', 'claimed_by').order_by('-date_added')

    context = {
        'turma': turma,
        'form': form,
        'preapproved_list': preapproved_list,
    }
    return render(request, 'classes/preapprove_students_form.html', context)

@login_required
def add_checklist_to_class(request, pk):
    """View para adicionar um ChecklistTemplate existente a uma turma."""
    turma = get_object_or_404(Class, pk=pk)
    user = request.user

    # Verificar Permissões
    if not user_is_teacher_or_admin_for_class(user, turma):
        messages.error(request, _("You do not have permission to assign checklists to this class."))
        return redirect('classes:class_detail', class_id=turma.pk)

    # Verificar se a app checklists está ativa
    if not CHECKLISTS_APP_EXISTS:
        messages.error(request, _("Checklist functionality is currently disabled."))
        return redirect('classes:class_detail', class_id=turma.pk)

    if request.method == 'POST':
        form = AssignChecklistForm(request.POST, turma=turma)
        if form.is_valid():
            checklist_template = form.cleaned_data['checklist_template']
            
            # 1. Adicionar a turma à relação M2M do template
            checklist_template.classes.add(turma)
            
            # 2. Criar ChecklistStatus para os alunos atuais da turma (se não existir)
            students_in_class = turma.students.filter(role='aluno') # Filtrar apenas alunos
            created_count = 0
            for student in students_in_class:
                status, created = ChecklistStatus.objects.get_or_create(
                    student=student,
                    template=checklist_template,
                    student_class=turma
                )
                if created:
                    created_count += 1
            
            # Mensagem de sucesso
            messages.success(request, _("Checklist template '{template_name}' assigned to class '{class_name}'.").format(
                template_name=checklist_template.name, class_name=turma.name
            ))
            if created_count > 0:
                messages.info(request, _("{count} student checklist status records were created.").format(count=created_count))
            
            return redirect('classes:class_detail', class_id=turma.pk)
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        form = AssignChecklistForm(turma=turma)

    # Listar checklists já associados a esta turma para informação
    # Corrigir consulta para usar o related_name que definimos ('checklist_templates')
    associated_checklists = turma.checklist_templates.all()

    context = {
        'turma': turma,
        'form': form,
        'associated_checklists': associated_checklists,
    }
    return render(request, 'classes/add_checklist_to_class.html', context)
