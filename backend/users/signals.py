from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction

# Assuming your models are in these locations. Adjust if necessary.
from .models import User, PreApprovedStudent 
# classes.models.Class will be referenced by PreApprovedStudent.class_instance
# from classes.models import Class # Not strictly needed here due to ForeignKey access

import logging
logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def auto_enroll_and_promote_pre_approved_student(sender, request, user: User, **kwargs):
    """
    Handles automatic enrollment and role promotion for pre-approved students upon login.

    1. Checks if the logged-in user's email is in the PreApprovedStudent list with 'Pending' status.
    2. If found:
        a. Promotes the user to the 'aluno' (student) role using user.promote_to_role('aluno').
           This also sets their status to 'ativo' and adds them to the 'aluno' group.
        b. Adds the user to the students list of the target_class from PreApprovedStudent.
        c. Updates the PreApprovedStudent record:
           - Sets status to 'Claimed'.
           - Sets claimed_by to the user.
           - Sets date_claimed to now.
    All database operations are wrapped in a transaction.
    """
    if not user.email:
        logger.warning(f"User {user.username} (ID: {user.id}) logged in without an email. Skipping pre-approved check.")
        return

    try:
        pre_approval = PreApprovedStudent.objects.select_related('class_instance').get(
            email__iexact=user.email, 
            status='Pending'
        )
    except PreApprovedStudent.DoesNotExist:
        # No pending pre-approval for this user, or email doesn't match.
        # This is a common case, so no error logging needed unless debugging.
        # logger.info(f"No pending pre-approval found for user {user.email} (ID: {user.id}).")
        return
    except PreApprovedStudent.MultipleObjectsReturned:
        # This shouldn't happen if email is unique for pending pre-approvals.
        logger.error(
            f"Multiple pending pre-approvals found for email {user.email}. "
            f"Manual intervention required for user {user.username} (ID: {user.id})."
        )
        return # Avoid processing to prevent incorrect assignments

    target_class = pre_approval.class_instance

    try:
        with transaction.atomic():
            # 1. Promote user to 'aluno' role (if not already)
            # The promote_to_role method handles status change and group assignment.
            if user.role != 'aluno':
                user.promote_to_role('aluno') # This also saves the user
                logger.info(f"User {user.email} (ID: {user.id}) promoted to 'aluno' role.")
            elif user.status == 'convidado': # Already 'aluno' role but still guest status
                user.status = 'ativo'
                user.save(update_fields=['status'])
                logger.info(f"User {user.email} (ID: {user.id}) status updated to 'ativo'.")


            # 2. Add user to the class's student list
            # The Class.students field has limit_choices_to={'role': 'aluno'},
            # so user must have 'aluno' role before this.
            if user not in target_class.students.all():
                target_class.students.add(user)
                logger.info(f"User {user.email} (ID: {user.id}) added to class '{target_class}'.")

            # 3. Update PreApprovedStudent record
            pre_approval.status = 'Claimed'
            pre_approval.claimed_by = user
            pre_approval.date_claimed = timezone.now()
            pre_approval.save()
            logger.info(f"Pre-approval for {user.email} (ID: {user.id}) in class '{target_class}' claimed.")

            # Optional: Send a notification or message to the user/teacher

    except Exception as e:
        logger.error(
            f"Error during auto-enrollment process for user {user.email} (ID: {user.id}) "
            f"with pre-approval ID {pre_approval.id}: {e}",
            exc_info=True # Includes stack trace in logs
        )
        # Depending on the error, you might want to revert parts of the transaction
        # or leave it to `transaction.atomic()` to roll back.
        # For instance, if promote_to_role succeeded but adding to class failed,
        # it might be an inconsistent state. Transaction atomicity helps here. 