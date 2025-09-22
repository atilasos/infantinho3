from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Class, ClassMembership

User = get_user_model()

try:
    from checklists.models import ChecklistTemplate, ChecklistStatus
    CHECKLISTS_APP_EXISTS = True
except ImportError:
    ChecklistTemplate, ChecklistStatus = None, None
    CHECKLISTS_APP_EXISTS = False


def _sync_memberships(instance, role, pk_set, action):
    if action == 'post_add' and pk_set:
        for user_id in pk_set:
            ClassMembership.objects.get_or_create(
                class_instance=instance,
                user_id=user_id,
                defaults={'role': role},
            )
    elif action == 'post_remove' and pk_set:
        ClassMembership.objects.filter(
            class_instance=instance,
            user_id__in=pk_set,
            role=role,
        ).delete()
    elif action == 'post_clear':
        ClassMembership.objects.filter(
            class_instance=instance,
            role=role,
        ).delete()


@receiver(m2m_changed, sender=Class.students.through)
def students_changed(sender, instance, action, pk_set, **kwargs):
    """Sync class memberships and checklist status when students change."""
    if action not in {'post_add', 'post_remove', 'post_clear'}:
        return

    _sync_memberships(instance, ClassMembership.Roles.STUDENT, pk_set, action)

    if CHECKLISTS_APP_EXISTS and action == "post_add":
        turma = instance
        templates_for_class = turma.checklist_templates.all()

        if not templates_for_class.exists():
            return

        added_students = User.objects.filter(id__in=pk_set, role='aluno')

        for student in added_students:
            for template in templates_for_class:
                ChecklistStatus.objects.get_or_create(
                    student=student,
                    template=template,
                    student_class=turma
                )


@receiver(m2m_changed, sender=Class.teachers.through)
def teachers_changed(sender, instance, action, pk_set, **kwargs):
    """Sync memberships when teachers are added or removed."""
    if action not in {'post_add', 'post_remove', 'post_clear'}:
        return

    _sync_memberships(instance, ClassMembership.Roles.TEACHER, pk_set, action)
