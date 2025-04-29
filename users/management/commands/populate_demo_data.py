# users/management/commands/populate_demo_data.py
import random
import os # Import os for path joining
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.conf import settings # Import settings
from django.core.files import File # Import File

# Import your models
from classes.models import Class
from blog.models import Post
from diary.models import DiarySession, DiaryEntry # Import Diary models
from checklists.models import ChecklistTemplate, ChecklistStatus, ChecklistItem, ChecklistMark # Import checklist models

# Get the custom User model
User = get_user_model()

# Define roles - ensure these match your User model choices if applicable
# Standardize Group names to lowercase to match role keys and decorator usage
ROLES = {
    'admin': 'administrador',   # Changed value to lowercase
    'professor': 'professor',     # Changed value to lowercase
    'aluno': 'aluno',           # Kept as is
    'encarregado': 'encarregado', # Changed value to lowercase
}

# --- Define sample file paths relative to MEDIA_ROOT ---
SAMPLE_IMAGE_DIR = os.path.join(settings.MEDIA_ROOT, 'sample_files')
SAMPLE_IMAGES = ['1.jpg', '2.jpg', '3.jpg', '4.jpg']
SAMPLE_PDF = '5.pdf'

class Command(BaseCommand):
    help = 'Populates the database with demo data for Infantinho 3.0'

    @transaction.atomic # Ensure all operations succeed or fail together
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting demo data population...'))

        # --- 1. Ensure Groups Exist ---
        self.stdout.write('Ensuring user groups exist...')
        groups = {}
        for role_key, role_name in ROLES.items():
            group, created = Group.objects.get_or_create(name=role_name)
            groups[role_key] = group
            if created:
                self.stdout.write(f'  Group "{role_name}" created.')
            else:
                self.stdout.write(f'  Group "{role_name}" already exists.')

        # --- 2. Create Demo Users (if they don't exist) ---
        self.stdout.write('Creating demo users...')
        users = {}

        # Admin/Superuser (ensure one exists, assumes you might have created one)
        admin_user, created = User.objects.get_or_create(
            username='admin@infantinho.demo',
            defaults={
                'email': 'admin@infantinho.demo',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin', # Set role field directly
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if not created and not admin_user.is_superuser:
             admin_user.is_staff = True
             admin_user.is_superuser = True
             admin_user.role = 'admin'
             admin_user.save()
        admin_user.groups.add(groups['admin']) # Add to group
        users['admin'] = admin_user
        self.stdout.write(f'  Admin User: {admin_user.username} {"created" if created else "retrieved"}.')

        # Teachers
        teacher_data = [
            {'username': 'prof.ana@infantinho.demo', 'first_name': 'Ana', 'last_name': 'Santos'},
            {'username': 'prof.rui@infantinho.demo', 'first_name': 'Rui', 'last_name': 'Martins'},
        ]
        users['teachers'] = []
        for data in teacher_data:
            teacher, created = User.objects.get_or_create(
                username=data['username'],
                defaults={**data, 'email': data['username'], 'role': 'professor'}
            )
            teacher.groups.add(groups['professor'])
            users['teachers'].append(teacher)
            self.stdout.write(f'  Teacher: {teacher.username} {"created" if created else "retrieved"}.')

        # Students
        student_data = [
            {'username': 'aluno.joao@infantinho.demo', 'first_name': 'João', 'last_name': 'Silva'},
            {'username': 'aluno.maria@infantinho.demo', 'first_name': 'Maria', 'last_name': 'Pereira'},
            {'username': 'aluno.pedro@infantinho.demo', 'first_name': 'Pedro', 'last_name': 'Costa'},
            {'username': 'aluno.sofia@infantinho.demo', 'first_name': 'Sofia', 'last_name': 'Ferreira'},
            {'username': 'aluno.tiago@infantinho.demo', 'first_name': 'Tiago', 'last_name': 'Oliveira'},
        ]
        users['students'] = []
        for data in student_data:
            student, created = User.objects.get_or_create(
                username=data['username'],
                defaults={**data, 'email': data['username'], 'role': 'aluno'}
            )
            student.groups.add(groups['aluno'])
            users['students'].append(student)
            self.stdout.write(f'  Student: {student.username} {"created" if created else "retrieved"}.')

        # Guardian
        guardian, created = User.objects.get_or_create(
            username='enc.maria.p@infantinho.demo', # Example: guardian of Maria Pereira
            defaults={
                'email': 'enc.maria.p@infantinho.demo',
                'first_name': 'Carla',
                'last_name': 'Pereira',
                'role': 'encarregado'
            }
        )
        guardian.groups.add(groups['encarregado'])
        users['guardian'] = guardian
        self.stdout.write(f'  Guardian: {guardian.username} {"created" if created else "retrieved"}.')
        
        # TODO: Link guardian to student using GuardianRelation model if it exists

        # --- 3. Clear existing Demo Classes, Posts, Diaries (Optional) ---
        self.stdout.write('Clearing existing demo posts, classes, diaries, checklist statuses/marks...')
        # Also clear ChecklistStatus and ChecklistMark linked to demo users
        ChecklistMark.objects.filter(status_record__student__username__endswith='@infantinho.demo').delete()
        ChecklistStatus.objects.filter(student__username__endswith='@infantinho.demo').delete()
        DiaryEntry.objects.filter(session__turma__name__contains='Demo').delete()
        DiarySession.objects.filter(turma__name__contains='Demo').delete()
        Post.objects.filter(autor__username__endswith='@infantinho.demo').delete()
        Class.objects.filter(name__contains='Demo').delete()

        # --- 4. Create Demo Classes (Update name) ---
        self.stdout.write('Creating demo classes...')
        classes = {}
        class_data = [
            {'name': '5º A Demo', 'year': 2025, 'teachers': [users['teachers'][0]]},
            {'name': '6º B Demo', 'year': 2025, 'teachers': [users['teachers'][1]]}, # Renamed 7B to 6B
        ]
        for data in class_data:
            class_obj = Class.objects.create(name=data['name'], year=data['year'])
            class_obj.teachers.set(data['teachers'])
            classes[data['name']] = class_obj
            self.stdout.write(f'  Class "{class_obj.name}" created.')

        # --- 5. Assign Students to Classes ---
        self.stdout.write('Assigning students to classes...')
        # Assign first 3 students to 5º A, next 2 to 6º B
        classes['5º A Demo'].students.add(*users['students'][0:3])
        classes['6º B Demo'].students.add(*users['students'][3:5]) # Updated class name
        self.stdout.write('  Students assigned.')

        # --- 6. Create Demo Blog Posts (Update class names) ---
        self.stdout.write('Creating demo blog posts...')
        lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
        
        post_data = [
            {'turma': classes['5º A Demo'], 'autor': users['teachers'][0], 'titulo': 'Bem-vindos ao 5ºA!', 'conteudo': f'... {lorem}', 'categoria': 'AVISO', 'image': SAMPLE_IMAGES[0], 'status': 'PUBLISHED'},
            {'turma': classes['5º A Demo'], 'autor': users['students'][0], 'titulo': 'O meu primeiro dia', 'conteudo': f'... {lorem}', 'categoria': 'OUTRO', 'status': 'PENDING'},
            {'turma': classes['6º B Demo'], 'autor': users['teachers'][1], 'titulo': 'Projeto Ciências - Semana 1', 'conteudo': f'... {lorem}', 'categoria': 'PROJETO', 'attachment': SAMPLE_PDF, 'status': 'PUBLISHED'},
            {'turma': classes['6º B Demo'], 'autor': users['students'][3], 'titulo': 'Reflexão Matemática', 'conteudo': f'... {lorem}', 'categoria': 'TRABALHO', 'image': SAMPLE_IMAGES[1], 'status': 'PENDING'},
            {'turma': classes['5º A Demo'], 'autor': users['teachers'][0], 'titulo': 'Resumo da Semana', 'conteudo': f'Esta semana fizemos jogos de apresentação. {lorem}', 'categoria': 'OUTRO', 'image': SAMPLE_IMAGES[2], 'status': 'PUBLISHED'},
            {'turma': classes['6º B Demo'], 'autor': users['teachers'][1], 'titulo': 'Material de Apoio - Frações', 'conteudo': f'... {lorem}', 'categoria': 'OUTRO', 'image': SAMPLE_IMAGES[3], 'status': 'PUBLISHED'},
        ]

        for data in post_data:
            # Prepare fields, set approval details if published directly
            post_fields = {
                'turma': data['turma'],
                'autor': data['autor'],
                'titulo': data.get('titulo', ''),
                'conteudo': data['conteudo'],
                'categoria': data.get('categoria', 'OUTRO'),
                'status': data.get('status', 'PENDING')
            }
            if post_fields['status'] == 'PUBLISHED':
                post_fields['approved_by'] = data['autor']
                post_fields['approved_at'] = timezone.now()
                
            post = Post.objects.create(**post_fields)
            
            # --- Attach Files --- 
            image_name = data.get('image')
            pdf_name = data.get('attachment')
            
            if image_name:
                image_path = os.path.join(SAMPLE_IMAGE_DIR, image_name)
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as f:
                        post.image.save(image_name, File(f), save=True)
                        self.stdout.write(f'    Attached image {image_name} to post "{post.titulo}"')
                else:
                    self.stdout.write(self.style.WARNING(f'    Sample image not found: {image_path}'))
            
            if pdf_name:
                pdf_path = os.path.join(SAMPLE_IMAGE_DIR, pdf_name) # Assuming PDF is in same dir
                if os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as f:
                        post.attachment.save(pdf_name, File(f), save=True)
                        self.stdout.write(f'    Attached PDF {pdf_name} to post "{post.titulo}"')
                else:
                     self.stdout.write(self.style.WARNING(f'    Sample PDF not found: {pdf_path}'))
                         
            self.stdout.write(f'  Post created: "{post.titulo}" (Status: {post.status}) in class {post.turma.name}')

        # --- 7. Create Demo Diary Sessions and Entries --- 
        self.stdout.write('Creating demo diary sessions and entries...')
        
        for class_name, class_obj in classes.items():
            # Ensure only ONE active session exists per class initially for demo
            # Archive any existing active sessions first
            active_sessions = DiarySession.objects.filter(turma=class_obj, status='ACTIVE')
            for session in active_sessions:
                session.status = 'ARCHIVED'
                session.end_date = session.start_date # Or timezone.localdate()?
                session.save()
                self.stdout.write(f'  Archived existing active session for {class_name}.')

            # Create one new active session for today
            diary_session = DiarySession.objects.create(
                turma=class_obj,
                status='ACTIVE',
                start_date=timezone.localdate() # Start today
            )
            self.stdout.write(f'  New ACTIVE diary session created for {class_name} starting {diary_session.start_date}.')
            
            # Add some entries to this new session
            teacher = class_obj.teachers.first()
            students_in_class = list(class_obj.students.all())
            
            diary_entries_data = [
                {'column': 'GOSTEI', 'content': 'Gostei da aula de matemática hoje!', 'author': random.choice(students_in_class) if students_in_class else teacher},
                {'column': 'GOSTEI', 'content': 'A colaboração no projeto foi excelente.', 'author': teacher},
                {'column': 'NAO_GOSTEI', 'content': 'Achei o exercício X um pouco confuso.', 'author': random.choice(students_in_class) if students_in_class else teacher},
                {'column': 'FIZEMOS', 'content': 'Terminámos a leitura do capítulo 3.', 'author': teacher},
                {'column': 'FIZEMOS', 'content': 'Apresentámos o trabalho de grupo.', 'author': random.choice(students_in_class) if students_in_class else teacher},
                {'column': 'QUEREMOS', 'content': 'Mais tempo para o projeto de ciências.', 'author': random.choice(students_in_class) if students_in_class else teacher},
                {'column': 'QUEREMOS', 'content': 'Rever a matéria das equações na próxima aula.', 'author': teacher},
            ]
            
            for entry_data in diary_entries_data:
                DiaryEntry.objects.create(
                    session=diary_session,
                    column=entry_data['column'],
                    content=entry_data['content'],
                    author=entry_data['author']
                )
            self.stdout.write(f'    Added {len(diary_entries_data)} entries to the new diary session for {class_name}.')

        # --- 8. Create Demo Checklist Status & Marks --- 
        self.stdout.write('Creating demo checklist statuses and marks...')
        try:
            # Trying to get specific templates based on names assumed from load_checklists
            template_5ano = ChecklistTemplate.objects.get(name__iexact='Português 5º Ano') # Use iexact for safety
            template_6ano = ChecklistTemplate.objects.get(name__iexact='Português 6º Ano')
        except ChecklistTemplate.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Demo Checklist templates (Português 5º/6º Ano) not found: {e}. Run load_checklists first?'))
            template_5ano = None
            template_6ano = None
        except ChecklistTemplate.MultipleObjectsReturned as e:
            self.stdout.write(self.style.ERROR(f'Multiple demo checklist templates found: {e}. Ensure unique names.'))
            template_5ano = None # Avoid proceeding with ambiguity
            template_6ano = None

        if template_5ano:
            items_5ano = list(template_5ano.items.all())
            class_5a = classes.get('5º A Demo') # Use get to avoid KeyError
            if class_5a and items_5ano:
                for student in class_5a.students.all():
                    # Get or create the ChecklistStatus for this student/template/class
                    status_obj, created = ChecklistStatus.objects.get_or_create(
                        student=student,
                        template=template_5ano,
                        student_class=class_5a
                    )
                    if created:
                        self.stdout.write(f'  Created ChecklistStatus for {student.username} - {template_5ano.name} in {class_5a.name}')
                    else:
                        # Clear existing marks for this status before adding new random ones
                        ChecklistMark.objects.filter(status_record=status_obj).delete()

                    # Add some random marks LINKED TO THE STATUS RECORD
                    for item in random.sample(items_5ano, k=min(5, len(items_5ano))): # Mark up to 5 items randomly
                        # Use new field name 'mark_status'
                        mark_status_choice = random.choice(['IN_PROGRESS', 'COMPLETED'])
                        # Create mark linked via status_record
                        ChecklistMark.objects.update_or_create(
                            status_record=status_obj, # Link to the status object
                            item=item,
                            defaults={
                                'mark_status': mark_status_choice, 
                                'marked_by': student, # Assume student marks initially
                                'teacher_validated': False # Initially not validated
                            } 
                        )
                    # Explicitly trigger percentage update after adding marks for this status
                    status_obj.update_percent_complete() 
                    self.stdout.write(f'    Added random marks for {student.username} on {template_5ano.name}')
            elif not class_5a:
                 self.stdout.write(self.style.WARNING(f'  Class 5º A Demo not found, skipping checklist data.'))
            elif not items_5ano:
                 self.stdout.write(self.style.WARNING(f'  No items found for {template_5ano.name}, skipping marks.'))
                        
        if template_6ano:
            items_6ano = list(template_6ano.items.all())
            class_6b = classes.get('6º B Demo') # Use get
            if class_6b and items_6ano:
                for student in class_6b.students.all():
                    # Get or create the ChecklistStatus
                    status_obj, created = ChecklistStatus.objects.get_or_create(
                        student=student,
                        template=template_6ano,
                        student_class=class_6b
                    )
                    if created:
                         self.stdout.write(f'  Created ChecklistStatus for {student.username} - {template_6ano.name} in {class_6b.name}')
                    else:
                        # Clear existing marks
                        ChecklistMark.objects.filter(status_record=status_obj).delete()
                        
                    # Add some random marks LINKED TO THE STATUS RECORD
                    for item in random.sample(items_6ano, k=min(7, len(items_6ano))): # Mark up to 7 items randomly
                        # Use new field name 'mark_status'
                        mark_status_choice = random.choice(['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED'])
                         # Create mark linked via status_record
                        ChecklistMark.objects.update_or_create(
                            status_record=status_obj, # Link to the status object
                            item=item,
                            defaults={
                                'mark_status': mark_status_choice, 
                                'marked_by': student,
                                'teacher_validated': False
                            }
                        )
                    # Explicitly trigger percentage update
                    status_obj.update_percent_complete()
                    self.stdout.write(f'    Added random marks for {student.username} on {template_6ano.name}')
            elif not class_6b:
                 self.stdout.write(self.style.WARNING(f'  Class 6º B Demo not found, skipping checklist data.'))
            elif not items_6ano:
                 self.stdout.write(self.style.WARNING(f'  No items found for {template_6ano.name}, skipping marks.'))

        self.stdout.write(self.style.SUCCESS('Demo data population finished successfully!')) 