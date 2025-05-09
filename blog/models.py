# blog/models.py
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

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
        verbose_name=_('class'),
        null=True,
        blank=True
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
    conteudo = models.TextField(
        _('content')
    )
    # --- New Fields for Attachments ---
    image = models.ImageField(
        _("image"), 
        upload_to='blog_images/%Y/%m/', # Store in media/blog_images/YYYY/MM/
        null=True, 
        blank=True,
        help_text=_("Optional image associated with the post.")
    )
    attachment = models.FileField(
        _("attachment"), 
        upload_to='blog_attachments/%Y/%m/', # Store in media/blog_attachments/YYYY/MM/
        null=True, 
        blank=True,
        help_text=_("Optional file attachment (e.g., PDF).")
    )
    # --- End New Fields ---
    
    # Timestamp when the post was created.
    publicado_em = models.DateTimeField(
        _('published at'),
        default=timezone.now
    )
    
    # --- Status Field (Replaces Visibility) ---
    STATUS_CHOICES = [
        ('PENDING', _('Pending Approval')),
        ('PUBLISHED', _('Published')),
        # ('REMOVED', _('Removed')), # Combine with 'removido' field logic for simplicity
    ]
    status = models.CharField(
        _('status'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text=_('Publication status of the post.')
    )
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_posts',
        verbose_name=_('approved by'),
        help_text=_('User who approved the post for publication.')
    )
    approved_at = models.DateTimeField(
        _('approved at'),
        null=True,
        blank=True,
        help_text=_('Timestamp when the post was approved.')
    )
    # --- End Status Field ---

    # Choices for the main category of the post - REMOVED 'DIARIO'
    CATEGORIA_CHOICES = [
        # ('DIARIO', _('Class Diary')), 
        ('AVISO', _('Announcement')),
        ('PROJETO', _('Project Update')),
        ('TRABALHO', _('Student Work')),
        ('OUTRO', _('Other')),
    ]
    # REMOVED CATEGORIA_DIARIO_CHOICES
    # CATEGORIA_DIARIO_CHOICES = [...] 

    # Main category of the post.
    categoria = models.CharField(
        _('category'),
        max_length=20, 
        choices=CATEGORIA_CHOICES, 
        default='OUTRO', 
        help_text=_('The main category of the post.')
    )
    # REMOVED subcategoria_diario field
    # subcategoria_diario = models.CharField(...) 

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

    def is_editable_by(self, user: User) -> bool:
        """
        Checks if a given user has permission to edit this post.
        Allows author to edit if PENDING, or Admin anytime.
        Published posts generally shouldn't be directly edited by author.
        """
        if not user or not user.is_authenticated:
            return False
        # Admins can edit anything (careful with published posts?)
        if user.is_superuser or (hasattr(user, 'role') and user.role == 'admin'):
            return True # Maybe add condition !self.removido?
        # Author can edit their own PENDING posts
        if self.status == 'PENDING' and not self.removido and self.autor == user:
            return True
        # Teachers do NOT get general edit permission here.
        return False

    def is_removable_by(self, user: User) -> bool:
        """Checks if a given user has permission to remove this post."""
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or (hasattr(user, 'role') and user.role == 'admin'):
            return True
        if hasattr(user, 'role') and user.role == 'professor':
            # Check if user teaches the class associated with the post
            if self.turma in getattr(user, 'classes_taught', Class.objects.none()).all():
                return True
        # Maybe allow author to remove PENDING posts?
        # if self.status == 'PENDING' and self.autor == user:
        #     return True
        return False

    def is_visible_to(self, user) -> bool: # user can be AnonymousUser or User
        """Checks if a given user has permission to view this post."""
        # Rule 1: If published and not removed, visible to everyone.
        if self.status == 'PUBLISHED' and not self.removido:
            return True
            
        # Rule 2: If removed, only visible to moderators (teacher/admin).
        if self.removido:
            if not user or not user.is_authenticated: return False
            is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
            is_teacher_of_class = False
            if hasattr(user, 'role') and user.role == 'professor':
                is_teacher_of_class = self.turma in getattr(user, 'classes_taught', Class.objects.none()).all()
            return is_admin or is_teacher_of_class
            
        # Rule 3: If pending, only visible to author and moderators.
        if self.status == 'PENDING':
            if not user or not user.is_authenticated: return False
            is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
            is_teacher_of_class = False
            if hasattr(user, 'role') and user.role == 'professor':
                is_teacher_of_class = self.turma in getattr(user, 'classes_taught', Class.objects.none()).all()
            return self.autor == user or is_admin or is_teacher_of_class
            
        # Default deny if status is unexpected or no rule matched
        return False

    def save(self, *args, **kwargs):
        # self.clean() # Removed call to clean
        super().save(*args, **kwargs)

    def remover(self, user: User, motivo: str = None):
        """Marks the post as removed and logs the action. Requires permission check before calling."""
        if self.removido:
            return 
        self.removido = True
        self.removido_por = user
        self.removido_em = timezone.now()
        self.motivo_remocao = motivo or ""
        # Update status maybe? Or keep status and rely on removido flag?
        # Let's keep status as is for now, `is_visible_to` handles removed.
        # self.status = 'REMOVED' # If we add REMOVED status
        self.save(update_fields=['removido', 'removido_por', 'removido_em', 'motivo_remocao'])
        
        ModerationLog.objects.create(
            acao='REMOVER_POST',
            user=user,
            post=self,
            motivo=self.motivo_remocao,
            conteudo_snapshot=f"""Title: {self.titulo}

{self.conteudo}""" # Store snapshot
        )
        print(f"Post {self.pk} marked as removed by {user.username}")

    def approve(self, user: User):
        """Marks the post as published. Requires permission check before calling."""
        if self.status == 'PUBLISHED':
            return # Already published
            
        self.status = 'PUBLISHED'
        self.approved_by = user
        self.approved_at = timezone.now()
        # Also ensure it's not marked as removed if being approved
        self.removido = False
        self.removido_por = None
        self.removido_em = None
        self.motivo_remocao = ''
        self.save(update_fields=['status', 'approved_by', 'approved_at', 'removido', 'removido_por', 'removido_em', 'motivo_remocao'])
        
        # Log the action? (Optional)
        # ModerationLog.objects.create(acao='APPROVE_POST', user=user, post=self)
        print(f"Post {self.pk} approved by {user.username}")

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
