# blog/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden # Use Forbidden for permission errors
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.html import strip_tags # For plain text email snippet
from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from collections import OrderedDict
import itertools
from django.utils.translation import gettext_lazy as _

# App-specific imports
from .models import Post, Comment, ModerationLog
from .forms import PostForm, CommentForm
# Use the new/updated permission decorators
from .permissions import (
    turma_member_required, 
    turma_post_create_required, 
    post_edit_permission_required, 
    post_remove_permission_required, 
    comment_remove_permission_required
)
from classes.models import Class
from users.models import GuardianRelation

@turma_member_required # Checks user is authenticated and related to the class
def post_list(request, class_id):
    """Displays a list of non-removed posts for a specific class, with filtering and pagination."""
    turma = get_object_or_404(Class, id=class_id)
    # Fetch non-removed posts for the class
    posts_qs = Post.objects.filter(turma=turma, removido=False).order_by('-publicado_em')

    # --- Filtering --- 
    categoria_atual = request.GET.get('categoria', '')
    data_atual = request.GET.get('data', '')

    if categoria_atual:
        posts_qs = posts_qs.filter(categoria=categoria_atual)
    if data_atual:
        try:
            # Ensure correct date parsing
            data = timezone.datetime.strptime(data_atual, '%Y-%m-%d').date()
            posts_qs = posts_qs.filter(publicado_em__date=data)
        except ValueError:
            messages.warning(request, _("Invalid date format for filtering."))
            pass # Ignore invalid date format

    # --- Pagination --- 
    # Consider making page size configurable
    paginator = Paginator(posts_qs, 15) # Show 15 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- Grouping (Optional, can be complex with pagination) ---
    # Grouping by month/year only for the current page
    def group_key(post):
        return post.publicado_em.strftime('%Y-%m') # Year-Month key
    posts_grouped = OrderedDict()
    for key, group in itertools.groupby(page_obj.object_list, key=group_key):
        try:
            ano, mes = key.split('-')
            # Store as tuple key (year, month)
            posts_grouped[(int(ano), int(mes))] = list(group)
        except ValueError: # Should not happen with YYYY-MM format
            pass 
            
    context = {
        'turma': turma,
        'posts': page_obj, # Pass the page object for pagination controls
        'posts_grouped': posts_grouped, # Grouped posts for display
        'categorias': Post.CATEGORIA_CHOICES, # For filter dropdown
        'categoria_atual': categoria_atual,
        'data_atual': data_atual,
    }
    return render(request, 'blog/post_list.html', context)

@turma_member_required # Checks user is authenticated and related to the class
def post_detail(request, class_id, post_id):
    """Displays a single post and its comments, checking visibility."""
    turma = get_object_or_404(Class, id=class_id)
    # Use select_related to optimize fetching author
    post = get_object_or_404(Post.objects.select_related('autor'), id=post_id, turma=turma)

    # Explicit visibility check using the model method
    if not post.is_visible_to(request.user):
        messages.error(request, _("You do not have permission to view this post."))
        # Redirect to list or appropriate page
        return redirect('blog:post_list', class_id=class_id)
        
    # Fetch non-removed comments for the post, optimizing author fetch
    comentarios = post.comments.filter(removido=False).select_related('autor').order_by('publicado_em')
    
    # Prepare context for template
    context = {
        'turma': turma,
        'post': post,
        'comentarios': comentarios,
        # Pass permission flags to the template for conditional rendering (e.g., edit/remove buttons)
        'can_edit_post': post.is_editable_by(request.user),
        'can_remove_post': post.is_removable_by(request.user),
        'comment_form': CommentForm() # Include blank comment form
    }
    return render(request, 'blog/post_detail.html', context)

@turma_post_create_required # Checks user role (student/teacher/admin) and class membership
def post_create(request, class_id):
    """Handles the creation of a new post."""
    turma = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.turma = turma
            post.autor = request.user
            post.save() # Save the post
            messages.success(request, _("Post created successfully."))
            
            # --- Send Notifications --- 
            _send_post_notification(request, post)
            
            # Redirect using the correct namespace
            return redirect('blog:post_detail', class_id=class_id, post_id=post.id)
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        form = PostForm()
        
    context = {
        'turma': turma,
        'form': form,
        'edit_mode': False, # Indicate create mode
    }
    return render(request, 'blog/post_form.html', context)

@post_edit_permission_required # Checks if user is author or admin
def post_edit(request, class_id, post_id):
    """Handles editing an existing post."""
    # Decorator already fetched post and checked permissions
    turma = get_object_or_404(Class, id=class_id)
    post = get_object_or_404(Post, id=post_id, turma=turma)

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, _("Post updated successfully."))
            # Log edit action? (Optional)
            # ModerationLog.objects.create(acao='EDITAR_POST', user=request.user, post=post)
            return redirect('blog:post_detail', class_id=class_id, post_id=post_id)
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        form = PostForm(instance=post)
        
    context = {
        'turma': turma,
        'form': form,
        'post': post,
        'edit_mode': True, # Indicate edit mode
    }
    return render(request, 'blog/post_form.html', context)

# Use the new decorator and require POST
@require_POST 
@post_remove_permission_required # Checks if user is teacher/admin of the class
def post_remove(request, class_id, post_id):
    """Handles removing (soft deleting) a post via POST request."""
    # Decorator already fetched post and checked permissions
    post = get_object_or_404(Post, id=post_id, turma_id=class_id)
    
    motivo = request.POST.get('motivo', '') # Get reason from POST data
    post.remover(request.user, motivo=motivo) # Call the model method
    messages.success(request, _("Post removed successfully."))
    
    return redirect('blog:post_list', class_id=class_id)

# Use require_POST for comment creation
@require_POST
@turma_member_required # Ensure user is related to the class to comment
def post_comment(request, class_id, post_id):
    """Handles the submission of a new comment on a post."""
    turma = get_object_or_404(Class, id=class_id)
    post = get_object_or_404(Post, id=post_id, turma=turma)

    # Check if user can view the post (implicitly allows commenting)
    if not post.is_visible_to(request.user):
        messages.error(request, _("You cannot comment on this post."))
        return redirect('blog:post_list', class_id=class_id)

    form = CommentForm(request.POST)
    if form.is_valid():
        comentario = form.save(commit=False)
        comentario.post = post
        comentario.autor = request.user
        comentario.save()
        messages.success(request, _("Comment added successfully."))
        # --- Send Notification to post author --- 
        _send_comment_notification(request, comentario)
    else:
        # Handle invalid form - maybe display errors on the detail page?
        # For simplicity, just show a generic error for now.
        messages.error(request, _("Could not add comment. Please check your input."))
        # Optionally, re-render the detail page with the form errors:
        # context = { ... post_detail context ... , 'comment_form': form}
        # return render(request, 'blog/post_detail.html', context)

    # Redirect back to the post detail page regardless of success/failure for now
    return redirect('blog:post_detail', class_id=class_id, post_id=post_id)

# Use the new decorator and require POST
@require_POST
@comment_remove_permission_required # Checks if user is teacher/admin for the comment
def comment_remove(request, class_id, post_id, comment_id):
    """Handles removing (soft deleting) a comment via POST request."""
    # Decorator has already fetched comment and checked permissions
    comment = get_object_or_404(Comment, id=comment_id)
    
    motivo = request.POST.get('motivo', '') # Reason from POST
    comment.remover(request.user, motivo=motivo) # Call model method
    messages.success(request, _("Comment removed successfully."))
    
    # Redirect back to the post detail page
    return redirect('blog:post_detail', class_id=class_id, post_id=post_id)


@login_required # Basic login check
def moderation_logs(request, class_id):
    """Displays moderation logs for a class (restricted to teachers/admins)."""
    turma = get_object_or_404(Class, id=class_id)
    user = request.user

    # Explicit permission check within the view
    # Consider creating a @class_moderator_required decorator later
    is_teacher_in_class = hasattr(user, 'role') and user.role == 'professor' and turma in getattr(user, 'classes_taught', Class.objects.none()).all()
    is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
    
    if not (is_admin or is_teacher_in_class):
        messages.error(request, _('Access restricted to class moderators.'))
        return redirect('blog:post_list', class_id=class_id)
        
    # Fetch logs related to posts or comments in this class
    logs = ModerationLog.objects.filter(
        models.Q(post__turma=turma) | models.Q(comment__post__turma=turma)
    ).select_related('user', 'post', 'comment').distinct().order_by('-data')[:100] # Limit & optimize
    
    context = {
        'turma': turma,
        'logs': logs,
    }
    return render(request, 'blog/moderation_logs.html', context)


@require_POST
@login_required # Basic login check
def post_restore(request, class_id, post_id):
    """Restores a previously removed post (restricted to teachers/admins)."""
    turma = get_object_or_404(Class, id=class_id)
    # Fetch post even if removed
    post = get_object_or_404(Post.objects.filter(pk=post_id, turma=turma))
    user = request.user

    # Explicit permission check (similar to moderation logs)
    # Consider creating a @class_moderator_required decorator later
    is_teacher_in_class = hasattr(user, 'role') and user.role == 'professor' and turma in getattr(user, 'classes_taught', Class.objects.none()).all()
    is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')

    if not (is_admin or is_teacher_in_class):
        messages.error(request, _('Access restricted to class moderators.'))
        return redirect('blog:post_detail', class_id=class_id, post_id=post_id)

    if not post.removido:
        messages.info(request, _('This post is already active.'))
        return redirect('blog:post_detail', class_id=class_id, post_id=post_id)

    # --- Restore Post --- 
    post.removido = False
    post.removido_por = None
    post.removido_em = None
    post.motivo_remocao = ''
    post.save(update_fields=['removido', 'removido_por', 'removido_em', 'motivo_remocao']) # Be specific
    
    # --- Log Restoration --- 
    ModerationLog.objects.create(
        acao='RESTAURAR_POST',
        user=user,
        post=post,
        motivo=_('Restored by moderation'),
        # No content snapshot needed for restore usually
    )
    messages.success(request, _('Post restored successfully.'))
    return redirect('blog:post_detail', class_id=class_id, post_id=post_id)

# Helper function for sending post notifications
def _send_post_notification(request, post):
    """Sends email notifications about a new post to class members and guardians."""
    turma = post.turma
    # Get students and teachers emails, excluding the author
    recipients = list(turma.students.exclude(id=post.autor.id).values_list('email', flat=True)) + \
                 list(turma.teachers.exclude(id=post.autor.id).values_list('email', flat=True))
    recipients = [email for email in recipients if email] # Filter out empty emails

    try:
        post_url = request.build_absolute_uri(reverse('blog:post_detail', args=[turma.id, post.id]))
        subject = f"Novo post na turma {turma.name}: {post.titulo or '(sem título)'}"
        # Use triple quotes for multi-line f-string
        message = f"""Um novo post foi publicado na turma {turma.name}.

Autor: {post.autor.get_full_name() or post.autor.username}

Título: {post.titulo or '(sem título)'}

{strip_tags(post.conteudo)[:200]}...

Ver post completo: {post_url}"""
    except Exception:
         # Handle cases where request might not be available (e.g., background task)
         # Or reverse might fail if URLs not set up yet
         print("Error building post URL/message for notification")
         return 

    if recipients:
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
                fail_silently=False, # Set to False to see errors during dev
            )
        except Exception as e:
            # Log email sending failure
            print(f"Error sending post notification email to members: {e}")

    # Notify guardians if category is DIARIO or AVISO
    if post.categoria in ['DIARIO', 'AVISO']:
        encarregado_emails = list(set(
            GuardianRelation.objects.filter(aluno__in=turma.students.all())
            .values_list('encarregado__email', flat=True)
        ))
        encarregado_emails = [email for email in encarregado_emails if email] # Filter out empty
        if encarregado_emails:
            subject_guardian = f"Novo comunicado da turma {turma.name}: {post.titulo or '(sem título)'}"
            try:
                send_mail(
                    subject_guardian,
                    message, # Reuse same basic message
                    settings.DEFAULT_FROM_EMAIL,
                    encarregado_emails,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending guardian notification email: {e}")

# Helper function for sending comment notifications
def _send_comment_notification(request, comment):
    """Sends email notification about a new comment to the post author."""
    post = comment.post
    # Only notify if the commenter is not the post author and author has email
    if post.autor != comment.autor and post.autor.email:
        try:
            post_url = request.build_absolute_uri(
                reverse('blog:post_detail', args=[post.turma.id, post.id])
            )
            comment_url = f"{post_url}#comment-{comment.id}"
            subject = f'Novo comentário no seu post "{post.titulo or post.get_category_display()}"'
            # Use triple quotes for multi-line f-string
            message = f"""{comment.autor.get_full_name() or comment.autor.username} comentou no seu post.

Comentário: {comment.conteudo[:200]}...

Ver post e comentário: {comment_url}"""
        except Exception:
            print("Error building comment URL/message for notification")
            return
            
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [post.autor.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending comment notification email: {e}")


# Simple help page view
@require_GET
@turma_member_required
def blog_help(request, class_id):
    """Displays the help page for the blog module."""
    turma = get_object_or_404(Class, id=class_id)
    return render(request, 'blog/blog_help.html', {'turma': turma})
