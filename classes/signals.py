from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.conf import settings
from .models import Class
# É crucial importar os modelos da outra app aqui
try:
    from checklists.models import ChecklistTemplate, ChecklistStatus
    CHECKLISTS_APP_EXISTS = True
except ImportError:
    ChecklistTemplate, ChecklistStatus = None, None
    CHECKLISTS_APP_EXISTS = False

User = settings.AUTH_USER_MODEL

@receiver(m2m_changed, sender=Class.students.through)
def students_added_to_class(sender, instance, action, pk_set, **kwargs):
    """
    Listens for when students are added to a class's student list.
    If checklists are enabled, creates ChecklistStatus records for the added students
    for all ChecklistTemplates associated with that class.
    """
    # Apenas executar se a app checklists existir e a ação for adicionar alunos
    if CHECKLISTS_APP_EXISTS and action == "post_add":
        # instance é o objeto Class
        turma = instance 
        
        # Obter os templates associados a esta turma
        templates_for_class = turma.checklist_templates.all()
        
        if not templates_for_class.exists():
            return # Não há templates associados, nada a fazer

        # pk_set contém os IDs dos Users (alunos) que foram adicionados
        added_student_ids = pk_set
        
        # Obter os objetos User dos alunos adicionados
        added_students = User.objects.filter(id__in=added_student_ids, role='aluno')

        created_count = 0
        # Para cada aluno adicionado e cada template da turma, criar o Status
        for student in added_students:
            for template in templates_for_class:
                status, created = ChecklistStatus.objects.get_or_create(
                    student=student,
                    template=template,
                    student_class=turma
                )
                if created:
                    created_count += 1
        
        # Opcional: Log ou mensagem, embora sinais não devam interagir diretamente com requests/messages
        if created_count > 0:
            print(f"Created {created_count} ChecklistStatus records for students added to class {turma.name}.") 