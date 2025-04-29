from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db import models

# Import models to clear
from blog.models import Post # Assuming Post is linked to User
from classes.models import Class # Assuming Class is linked to User
from diary.models import DiaryEntry, DiarySession # Import Diary models
from checklists.models import ChecklistMark, ChecklistStatus # Import checklist models
# from users.models import GuardianRelation # Uncomment if GuardianRelation exists

User = get_user_model()

class Command(BaseCommand):
    help = 'Clears demo data created by populate_demo_data command.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting demo data cleanup...'))
        
        demo_user_suffix = '@infantinho.demo'
        demo_class_tag = 'Demo'

        # --- 1. Delete Demo Checklist Marks --- 
        deleted_marks_count, _ = ChecklistMark.objects.filter(status_record__student__username__endswith=demo_user_suffix).delete()
        self.stdout.write(f'  Deleted {deleted_marks_count} demo checklist marks.')
        
        # --- 2. Delete Demo Checklist Statuses --- 
        deleted_statuses_count, _ = ChecklistStatus.objects.filter(student__username__endswith=demo_user_suffix).delete()
        self.stdout.write(f'  Deleted {deleted_statuses_count} demo checklist statuses.')
        
        # --- 3. Delete Demo Diary Entries ---
        # Entries linked to sessions of demo classes OR authored by demo users
        deleted_diary_entries_count, _ = DiaryEntry.objects.filter(
            models.Q(session__turma__name__contains=demo_class_tag) |
            models.Q(author__username__endswith=demo_user_suffix)
        ).delete()
        self.stdout.write(f'  Deleted {deleted_diary_entries_count} demo diary entries.')

        # --- 4. Delete Demo Diary Sessions ---
        deleted_diary_sessions_count, _ = DiarySession.objects.filter(
            turma__name__contains=demo_class_tag
        ).delete()
        self.stdout.write(f'  Deleted {deleted_diary_sessions_count} demo diary sessions.')

        # --- 5. Delete Demo Blog Posts --- 
        deleted_posts_count, _ = Post.objects.filter(autor__username__endswith=demo_user_suffix).delete()
        self.stdout.write(f'  Deleted {deleted_posts_count} demo blog posts.')

        # --- 6. Delete Demo Classes --- 
        deleted_classes_count, _ = Class.objects.filter(name__contains=demo_class_tag).delete()
        self.stdout.write(f'  Deleted {deleted_classes_count} demo classes.')
        
        # --- 7. Delete Guardian Relations (if applicable) --- 
        # Uncomment and adapt if GuardianRelation model is implemented
        # try:
        #     deleted_relations_count, _ = GuardianRelation.objects.filter(
        #         models.Q(encarregado__username__endswith=demo_user_suffix) |
        #         models.Q(aluno__username__endswith=demo_user_suffix)
        #     ).delete()
        #     self.stdout.write(f'  Deleted {deleted_relations_count} demo guardian relations.')
        # except NameError:
        #     self.stdout.write(self.style.NOTICE('  GuardianRelation model not found, skipping relation cleanup.'))
        # except Exception as e:
        #     self.stdout.write(self.style.ERROR(f'  Error deleting guardian relations: {e}'))
            
        # --- 8. Delete Demo Users --- 
        # Be careful: This deletes ALL users matching the suffix!
        # Exclude potential non-demo superusers just in case, though demo admin should match
        demo_users_qs = User.objects.filter(username__endswith=demo_user_suffix)
        # Optionally, add more filters to prevent deleting essential users if needed
        # demo_users_qs = demo_users_qs.exclude(is_superuser=True, username!='admin@infantinho.demo') 
        deleted_users_count, _ = demo_users_qs.delete()
        self.stdout.write(f'  Deleted {deleted_users_count} demo users (ending with {demo_user_suffix}).')
        
        # Note: Groups are usually kept, as they are part of the base setup.

        self.stdout.write(self.style.SUCCESS('Demo data cleanup finished.')) 