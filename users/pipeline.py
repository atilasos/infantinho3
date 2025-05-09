from django.utils import timezone
from django.db import transaction
from social_core.exceptions import AuthException # Para potencialmente parar o pipeline

# Importar os modelos necessários
from .models import PreApprovedStudent, User 
# from classes.models import Class # Não precisamos de importar Class diretamente aqui

import logging # Para logging

logger = logging.getLogger(__name__)

def assign_class_on_signup(backend, user, response, *args, **kwargs):
    """
    Pipeline step for social-auth-app-django.
    Checks if the user's email exists in PreApprovedStudent list upon first login/signup.
    If found and pending, assigns the user to the class, sets role to 'aluno',
    and updates the PreApprovedStudent record.
    """
    # Este pipeline corre depois do utilizador ser criado ou obtido
    if not user:
        logger.warning("assign_class_on_signup: User object not found in pipeline.")
        return # Não podemos fazer nada sem um utilizador

    # Verifica se é uma nova associação ou um utilizador que já existia mas era convidado
    is_new_association = kwargs.get('is_new', False) 
    was_guest = user.is_guest() # Usa a propriedade do modelo User

    # Corre apenas para novas associações OU utilizadores que eram convidados
    # e agora estão a fazer login (podem ter sido criados manualmente antes)
    if not is_new_association and not was_guest:
         logger.debug(f"assign_class_on_signup: Skipping for existing non-guest user {user.email}.")
         return # Não faz nada para utilizadores ativos existentes que fazem login novamente

    user_email = user.email
    if not user_email:
        logger.warning(f"assign_class_on_signup: User {user.username} has no email.")
        return # Precisa do email para verificar

    logger.info(f"assign_class_on_signup: Checking pre-approval for email {user_email} (User: {user.id}, New: {is_new_association}, Was Guest: {was_guest})")

    try:
        # Usar transaction.atomic para garantir consistência
        with transaction.atomic():
            pre_approval = PreApprovedStudent.objects.select_for_update().filter(
                email__iexact=user_email, 
                status='Pending'
            ).first()

            if pre_approval:
                logger.info(f"Found pending pre-approval for {user_email} for class {pre_approval.class_instance.id}")
                
                target_class = pre_approval.class_instance

                # 1. Atribuir o papel 'aluno' e status 'ativo'
                # Usar o método existente no modelo User, se possível
                if hasattr(user, 'promote_to_role'):
                    try:
                        user.promote_to_role('aluno') 
                        logger.info(f"Promoted user {user.email} to role 'aluno'.")
                    except Exception as e:
                        logger.error(f"Error promoting user {user.email} to role 'aluno': {e}", exc_info=True)
                        # Decide se quer parar o pipeline aqui ou continuar
                        # raise AuthException(backend, f"Failed to promote user role: {e}") 
                        # Por agora, vamos logar e continuar, o utilizador pode ficar sem role/class
                        pass # Permite continuar, mas regista o erro
                else:
                    # Fallback se promote_to_role não existir (improvável baseado no seu user model)
                    user.role = 'aluno'
                    user.status = 'ativo'
                    user.save(update_fields=['role', 'status'])
                    logger.info(f"Manually set user {user.email} role to 'aluno' and status to 'ativo'.")


                # 2. Adicionar o aluno à turma (M2M relationship)
                try:
                    target_class.students.add(user)
                    target_class.save() # Salvar a instância da turma pode não ser necessário, mas não faz mal
                    logger.info(f"Added user {user.email} to class '{target_class.name}'.")
                except Exception as e:
                    logger.error(f"Error adding user {user.email} to class {target_class.id}: {e}", exc_info=True)
                    # Considerar se deve parar aqui. Por agora, logar e continuar.
                    pass 

                # 3. Atualizar o registo PreApprovedStudent
                pre_approval.status = 'Claimed'
                pre_approval.claimed_by = user
                pre_approval.date_claimed = timezone.now()
                pre_approval.save()
                logger.info(f"Updated pre-approval record for {user_email} to 'Claimed'.")

                # Retorna um dicionário vazio ou None para continuar o pipeline
                return {'assigned_via_pre_approval': True}

            else:
                 logger.info(f"No pending pre-approval found for {user_email}. Proceeding with default flow.")
                 # Se não encontrou pré-aprovação, o utilizador continua como 'convidado' (o comportamento padrão do pipeline deve tratar disso)
                 return {'assigned_via_pre_approval': False}

    except Exception as e:
        # Logar qualquer erro inesperado durante o processo
        logger.error(f"Unexpected error in assign_class_on_signup for user {user_email}: {e}", exc_info=True)
        # Pode querer parar o pipeline em caso de erro grave
        # raise AuthException(backend, f"Error during pre-approval check: {e}")
        return # Permite que o pipeline continue, apesar do erro

    # Se não entrou no if pre_approval, retorna None implicitamente ou explicitamente
    return None 