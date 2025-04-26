# blog/models.py
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField

# Assuming User and Class models are defined elsewhere as specified
from users.models import User
from classes.models import Class 

class Post(models.Model):
    """
    Represents a blog post or diary entry within a specific class (turma).
    """
    # Foreign Key linking to the class this post belongs to.
    turma = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        related_name='posts',
        verbose_name=_('class')
    )
    # Foreign Key linking to the user who authored the post.
    autor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='posts',
        verbose_name=_('author')
    )
    # Optional title for the post.
    titulo = models.CharField(
        _('title'),
        max_length=200, 
        blank=True,
        help_text=_('Optional title for the post.')
    )
    # Main content of the post, using a rich text editor.
    conteudo = RichTextField(
        _('content')
    )
    # Timestamp when the post was created.
    publicado_em = models.DateTimeField(
        _('published at'),
        default=timezone.now # Use default=timezone.now for more flexibility than auto_now_add
    )

    # Choices for the main category of the post.
    CATEGORIA_CHOICES = [
        ('DIARIO', _('Class Diary')),       # Standard class diary entry
        ('AVISO', _('Announcement')),        # Teacher announcement
        ('PROJETO', _('Project Update')),    # Related to a specific project
        ('TRABALHO', _('Student Work')),    # Specific student work/output
        ('OUTRO', _('Other')),             # General category
    ]
    # Choices specific to 'DIARIO' category (MEM specific reflections).
    CATEGORIA_DIARIO_CHOICES = [
        ('GOSTEI', _('Liked')),
        ('NAO_GOSTEI', _('Disliked')),
        ('QUEREMOS', _('We Want')),
        ('FIZEMOS', _('We Did')),
    ]

    # Main category of the post.
    categoria = models.CharField(
        _('category'),
        max_length=20, 
        choices=CATEGORIA_CHOICES, 
        default='OUTRO', # Changed default, DIARIO might require subcategory
        help_text=_('The main category of the post.')
    )
    # Subcategory, specifically used if categoria is 'DIARIO'.
    subcategoria_diario = models.CharField(
        _('diary subcategory'),
        max_length=20, 
        choices=CATEGORIA_DIARIO_CHOICES, 
        blank=True,
        null=True, # Allow null if not DIARIO
        help_text=_('Specific subcategory if the main category is Class Diary.')
    )

    # Visibility settings for the post.
    VISIBILIDADE_CHOICES = [
        ('INTERNA', _('Internal (Class Members Only)')),
        # ('PUBLICA', _('Public (Future Use)')), # Keep internal-only for MVP
    ]
    visibilidade = models.CharField(
        _('visibility'),
        max_length=10, 
        choices=VISIBILIDADE_CHOICES, 
        default='INTERNA',
        help_text=_('Controls who can view the post.')
    )

    # Fields for soft deletion / moderation.
    removido = models.BooleanField(
        _('removed'),
        default=False, 
        help_text=_('Indicates if the post has been removed by moderation.')
    )
    removido_por = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='posts_removidos',
        verbose_name=_('removed by'),
        help_text=_('User who removed the post.')
    )
    removido_em = models.DateTimeField(
        _('removed at'),
        null=True, 
        blank=True,
        help_text=_('Timestamp when the post was removed.')
    )
    motivo_remocao = models.CharField(
        _('reason for removal'),
        max_length=255, 
        blank=True,
        help_text=_('Reason provided for removing the post.')
    )

    class Meta:
        ordering = ['-publicado_em'] # Show newest posts first by default
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __str__(self):
        """Returns a string representation of the post."""
        return self.titulo or f"Post #{self.pk} by {self.autor.username}"

    def get_category_display_full(self):
        """Returns the display name for the category and subcategory if applicable."""
        display = self.get_categoria_display()
        if self.categoria == 'DIARIO' and self.subcategoria_diario:
            display += f" - {self.get_subcategoria_diario_display()}"
        return display

    def is_editable_by(self, user: User) -> bool:
        """
        Checks if a given user has permission to edit this post.
        Follows MEM principles: Authors edit their own work, teachers moderate.
        """
        if not user or not user.is_authenticated:
            return False
        # Admins can edit anything
        if user.is_superuser or (hasattr(user, 'role') and user.role == 'admin'):
            return True
        # Author can edit their own non-removed posts
        if not self.removido and self.autor == user:
            return True
        # Teachers do NOT get general edit permission here; they should use comments or removal.
        return False

    def is_removable_by(self, user: User) -> bool:
        """Checks if a given user has permission to remove this post."""
        if not user or not user.is_authenticated:
            return False
        # Admins can remove anything
        if user.is_superuser or (hasattr(user, 'role') and user.role == 'admin'):
            return True
        # Teachers of the class can remove posts for moderation
        if hasattr(user, 'role') and user.role == 'professor':
            if self.turma in user.classes_taught.all():
                return True
        # Authors generally shouldn't remove their own posts after publishing?
        # Or maybe allow author removal? For now, restrict to teacher/admin.
        # if self.autor == user:
        #    return True 
        return False

    def is_visible_to(self, user: User) -> bool:
        """Checks if a given user has permission to view this post."""
        if self.removido and not (user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')):
            # Only admins can see removed posts (for potential restoration)
            # TODO: Maybe allow authors/teachers to see their removed posts?
            return False
            
        if not user or not user.is_authenticated:
            # If we had public posts, logic would differ here
            return False
            
        # Admins can see everything
        if user.is_superuser or (hasattr(user, 'role') and user.role == 'admin'):
            return True
            
        # Members of the class (students and teachers) can see internal posts
        if self.visibilidade == 'INTERNA':
            is_student_in_class = self.turma in user.classes_attended.all()
            is_teacher_in_class = self.turma in user.classes_taught.all()
            # Check if guardian is associated with a student in this class
            is_guardian_for_student_in_class = False
            if hasattr(user, 'role') and user.role == 'encarregado':
                # Check if any student this user is guardian for is in the post's class
                is_guardian_for_student_in_class = self.turma.students.filter(
                    encarregados_relations__encarregado=user
                ).exists()
                
            return is_student_in_class or is_teacher_in_class or is_guardian_for_student_in_class
        
        # Default deny if no condition met (e.g., future visibility types)
        return False

    def clean(self):
        """Model validation rules."""
        super().clean()
        # Ensure diary subcategory is only set if category is DIARIO
        if self.categoria == 'DIARIO' and not self.subcategoria_diario:
            # Make subcategory required for DIARIO? Or just allow it?
            # For now, allow DIARIO without subcategory, but clear sub if not DIARIO
            pass # Let's not make it mandatory for now
        if self.categoria != 'DIARIO' and self.subcategoria_diario:
            # Clear subcategory if the main category is not DIARIO
            self.subcategoria_diario = None 

    def save(self, *args, **kwargs):
        self.clean() # Ensure validation runs on save
        super().save(*args, **kwargs)

    def remover(self, user: User, motivo: str = None):
        """Marks the post as removed and logs the action. Requires permission check before calling."""
        if self.removido:
            return # Avoid multiple removals / overwriting original remover
            
        self.removido = True
        self.removido_por = user
        self.removido_em = timezone.now()
        self.motivo_remocao = motivo or ""
        self.save()
        
        # Log the moderation action
        ModerationLog.objects.create(
            acao='REMOVER_POST',
            user=user,
            post=self,
            motivo=self.motivo_remocao,
            # Fixed Syntax: Use triple quotes for multi-line f-string
            conteudo_snapshot=f"""Title: {self.titulo}

{self.conteudo}""" # Store snapshot
        )
        print(f"Post {self.pk} marked as removed by {user.username}")

class Comment(models.Model):
    """
    Represents a comment made on a blog Post.
    """
    # Foreign Key to the Post this comment belongs to.
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name=_('post')
    )
    # Foreign Key to the User who authored the comment.
    autor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name=_('author')
    )
    # Content of the comment.
    conteudo = models.TextField(
        _('content')
    )
    # Timestamp when the comment was created.
    publicado_em = models.DateTimeField(
        _('published at'),
        default=timezone.now
    )

    # Fields for soft deletion / moderation.
    removido = models.BooleanField(
        _('removed'),
        default=False, 
        help_text=_('Indicates if the comment has been removed by moderation.')
    )
    removido_por = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='comments_removidos',
        verbose_name=_('removed by'),
        help_text=_('User who removed the comment.')
    )
    removido_em = models.DateTimeField(
        _('removed at'),
        null=True, 
        blank=True,
        help_text=_('Timestamp when the comment was removed.')
    )
    motivo_remocao = models.CharField(
        _('reason for removal'),
        max_length=255, 
        blank=True,
        help_text=_('Reason provided for removing the comment.')
    )

    class Meta:
        ordering = ['publicado_em'] # Show oldest comments first within a post
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')

    def __str__(self):
        """Returns a string representation of the comment."""
        if self.removido:
            return str(_("Comment removed by moderation"))
        # Truncate content for display
        truncated_content = (self.conteudo[:75] + '...') if len(self.conteudo) > 75 else self.conteudo
        return str(_(f"Comment by {self.autor.username} on Post {self.post_id}: '{truncated_content}'"))

    def is_removable_by(self, user: User) -> bool:
        """Checks if a given user has permission to remove this comment."""
        if not user or not user.is_authenticated:
            return False
        # Admins can remove anything
        if user.is_superuser or (hasattr(user, 'role') and user.role == 'admin'):
            return True
        # Teachers of the class where the post is can remove comments
        if hasattr(user, 'role') and user.role == 'professor':
            if self.post.turma in user.classes_taught.all():
                return True
        # Authors generally shouldn't remove their own comments after publishing?
        # Allow authors to remove their own comments? For now, restrict to teacher/admin.
        # if self.autor == user:
        #     return True
        return False

    def remover(self, user: User, motivo: str = None):
        """Marks the comment as removed and logs the action. Requires permission check before calling."""
        if self.removido:
            return
            
        self.removido = True
        self.removido_por = user
        self.removido_em = timezone.now()
        self.motivo_remocao = motivo or ""
        self.save()

        # Log the moderation action
        ModerationLog.objects.create(
            acao='REMOVER_COMMENT',
            user=user,
            comment=self,
            motivo=self.motivo_remocao,
            conteudo_snapshot=self.conteudo # Store snapshot
        )
        print(f"Comment {self.pk} marked as removed by {user.username}")

    # Add permission checks if needed (e.g., is_visible_to, is_editable_by)
    # Generally, comment visibility follows post visibility.
    # Editing might be limited to author for a short time, or disabled.
    # Removal is usually done by moderators (teachers/admins).


class ModerationLog(models.Model):
    """
    Logs moderation actions taken on Posts or Comments.
    """
    # Choices for the type of moderation action performed.
    ACAO_CHOICES = [
        ('REMOVER_POST', _('Remove Post')),
        # ('EDITAR_POST', _('Edit Post')), # Maybe log edits implicitly or separately
        ('RESTAURAR_POST', _('Restore Post')),
        ('REMOVER_COMMENT', _('Remove Comment')),
        # ('EDITAR_COMMENT', _('Edit Comment')), 
        # ('RESTAURAR_COMMENT', _('Restore Comment')), # Add if restore needed
    ]
    acao = models.CharField(
        _('action'),
        max_length=20, 
        choices=ACAO_CHOICES,
        help_text=_('The type of moderation action performed.')
    )
    # The user who performed the action (moderator).
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, # Allow anonymous action? Or should always be logged in user?
        verbose_name=_('moderator'),
        help_text=_('The user who performed the moderation action.')
    )
    # Link to the Post, if the action relates to a Post.
    post = models.ForeignKey(
        Post, 
        on_delete=models.SET_NULL, # Keep log even if post is hard-deleted (unlikely)
        null=True, 
        blank=True,
        verbose_name=_('post')
    )
    # Link to the Comment, if the action relates to a Comment.
    comment = models.ForeignKey(
        Comment, 
        on_delete=models.SET_NULL, # Keep log even if comment is hard-deleted
        null=True, 
        blank=True,
        verbose_name=_('comment')
    )
    # Timestamp when the moderation action occurred.
    data = models.DateTimeField(
        _('timestamp'),
        default=timezone.now
    )
    # Optional reason provided by the moderator.
    motivo = models.CharField(
        _('reason'),
        max_length=255, 
        blank=True,
        help_text=_('Optional reason provided by the moderator.')
    )
    # Snapshot of the content at the time of moderation (e.g., before removal).
    conteudo_snapshot = models.TextField(
        _('content snapshot'),
        blank=True,
        help_text=_('A snapshot of the content at the time of the action.')
    )

    class Meta:
        ordering = ['-data'] # Show newest logs first
        verbose_name = _('Moderation Log Entry')
        verbose_name_plural = _('Moderation Log Entries')

    def __str__(self):
        """Returns a string representation of the log entry."""
        target = ""
        if self.post:
            target = f"Post {self.post_id}"
        elif self.comment:
            target = f"Comment {self.comment_id}"
        user_display = self.user.username if self.user else _('System')
        return f"{self.get_acao_display()} on {target} by {user_display} at {self.data.strftime('%Y-%m-%d %H:%M')}"
