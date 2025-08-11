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
from django.views.decorators.http import require_POST, require_GET
from collections import OrderedDict
import itertools
from django.utils.translation import gettext_lazy as _
from django.db import models # Import models for Q objects
from django.contrib.auth.decorators import login_required
import os
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

# App-specific imports
from .models import Post, Comment, ModerationLog
from .forms import PostForm, CommentForm
# Use the new/updated permission decorators
from .permissions import (
    turma_member_required,  # manter para views específicas da app
    turma_post_create_required,
    post_edit_permission_required,
    post_remove_permission_required,
    comment_remove_permission_required,
)
from users.permissions import class_teacher_required
from classes.models import Class
from users.models import GuardianRelation
from users.decorators import group_required # Assuming this exists for teacher/admin checks

@turma_member_required
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

def post_detail(request, post_id): # Removed class_id
    """Displays a single post and its comments, checking visibility."""
    # Fetch post using only post_id, include related fields
    post = get_object_or_404(Post.objects.select_related('autor', 'turma', 'removido_por'), id=post_id)
    turma = post.turma # Get turma from the post
    user = request.user

    # Explicit visibility check using the model method
    if not post.is_visible_to(user):
        messages.error(request, _("You do not have permission to view this post."))
        return redirect('blog:post_list_public') 
        
    # --- Pre-calculate permissions to avoid N+1 in template ---
    can_approve = False # Default to False
    if user.is_authenticated:
        is_admin_or_superuser = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
        is_teacher_of_class = False
        if hasattr(user, 'role') and user.role == 'professor':
            is_teacher_of_class = user.classes_taught.filter(id=turma.id).exists()
        
        # User can approve if admin/superuser OR teacher of this class
        can_approve = is_admin_or_superuser or is_teacher_of_class
        
        can_edit_post = is_admin_or_superuser or (not post.removido and post.autor == user and post.status == 'PENDING') # Edit only pending
        can_remove_post = is_admin_or_superuser or is_teacher_of_class
        can_remove_comments = is_admin_or_superuser or is_teacher_of_class # Same logic for comments
        can_restore_post = post.removido and (is_admin_or_superuser or is_teacher_of_class)
    else: # Anonymous user permissions
        is_admin_or_superuser = False
        is_teacher_of_class = False
        can_edit_post = False
        can_remove_post = False
        can_restore_post = False

    # Fetch non-removed comments for the post, optimizing author fetch
    comentarios = post.comments.filter(removido=False).select_related('autor').order_by('publicado_em')
    
    # Prepare context for template
    context = {
        'turma': turma, # Still useful context
        'post': post,
        'comentarios': comentarios,
        # Pass pre-calculated permission flags to the template
        'can_approve': can_approve, # Add the new flag
        'can_edit_post': can_edit_post,
        'can_remove_post': can_remove_post,
        'can_remove_comments': can_remove_comments,
        'can_restore_post': can_restore_post,
        'comment_form': CommentForm() # Include blank comment form
    }
    return render(request, 'blog/post_detail.html', context)

@turma_post_create_required
def post_create(request, class_id):
    """Handles the creation of a new post."""
    turma = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        # Pass initial= request.user to form if needed, or set author after save(commit=False)
        # Also pass initial files if the form handles them
        form = PostForm(request.POST, request.FILES) 
        if form.is_valid():
            post = form.save(commit=False)
            post.turma = turma
            post.autor = request.user
            
            # --- Set Initial Status based on Author Role --- 
            if request.user.role in ['professor', 'admin'] or request.user.is_superuser:
                post.status = 'PUBLISHED'
                post.approved_by = request.user # Auto-approved by author
                post.approved_at = timezone.now()
            else: # Student post
                post.status = 'PENDING'
                post.approved_by = None
                post.approved_at = None
            # ------------------------------------------------
                
            post.save() # Save the post with status and potentially files
            form.save_m2m() # Needed if form has M2M fields (none currently)
            
            if post.status == 'PUBLISHED':
                messages.success(request, _("Post published successfully."))
                _send_post_notification(request, post) # Notify only if published
            else:
                messages.success(request, _("Post submitted for approval."))
                # Notify moderators? (Optional - implement later)
                # _send_pending_post_notification(request, post)
                
            # Redirect to detail page (works for published or pending due to is_visible_to logic)
            return redirect('blog:post_detail', post_id=post.id)
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

@login_required # Use basic login check; more specific checks inside
def post_edit(request, post_id): # Removed class_id
    """Handles editing an existing post."""
    post = get_object_or_404(Post.objects.select_related('turma', 'autor'), id=post_id)
    turma = post.turma
    user = request.user

    # --- Permission Check --- 
    # Check if user is author or admin/superuser
    if not (user == post.autor or user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')):
        messages.error(request, _("You do not have permission to edit this post."))
        return redirect('blog:post_detail', post_id=post_id)
        
    # Cannot edit removed posts directly (should restore first)
    if post.removido:
        messages.error(request, _("Cannot edit a removed post. Please restore it first."))
        return redirect('blog:post_detail', post_id=post_id)
        
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, _("Post updated successfully."))
            # Log edit action? (Optional)
            # ModerationLog.objects.create(acao='EDITAR_POST', user=request.user, post=post)
            return redirect('blog:post_detail', post_id=post_id) # Redirect without class_id
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        form = PostForm(instance=post)
        
    context = {
        'turma': turma, # Still pass turma for context if needed by form/template
        'form': form,
        'post': post,
        'edit_mode': True, # Indicate edit mode
    }
    return render(request, 'blog/post_form.html', context)

# Use the new decorator and require POST
@require_POST 
@login_required
def post_remove(request, post_id): # Removed class_id
    """Handles removing (soft deleting) a post via POST request."""
    post = get_object_or_404(Post.objects.select_related('turma'), id=post_id)
    turma = post.turma
    user = request.user
    
    # --- Permission Check --- 
    is_admin_or_superuser = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
    is_teacher_of_class = False
    if hasattr(user, 'role') and user.role == 'professor':
        is_teacher_of_class = user.classes_taught.filter(id=turma.id).exists()
        
    if not (is_admin_or_superuser or is_teacher_of_class):
        messages.error(request, _("You do not have permission to remove this post."))
        # Redirect back to post or maybe public list?
        return redirect('blog:post_detail', post_id=post_id) 
        
    motivo = request.POST.get('motivo', '') # Get reason from POST data
    post.remover(request.user, motivo=motivo) # Call the model method
    messages.success(request, _("Post removed successfully."))
    
    # Redirect to the public blog list after removal
    return redirect('blog:post_list_public')

# Use require_POST for comment creation
@require_POST
@login_required
def post_comment(request, post_id): # Removed class_id
    """Handles the submission of a new comment on a post."""
    post = get_object_or_404(Post.objects.select_related('turma'), id=post_id)
    # turma = post.turma # Not strictly needed here unless for complex permission

    # Check if user can view the post (implicitly allows commenting)
    # The is_visible_to method should handle this
    if not post.is_visible_to(request.user):
        messages.error(request, _("You cannot comment on this post."))
        return redirect('blog:post_list_public')

    form = CommentForm(request.POST)
    if form.is_valid():
        comentario = form.save(commit=False)
        comentario.post = post
        comentario.autor = request.user
        comentario.save()
        messages.success(request, _("Comment added successfully."))
        # --- Send Notification to post author --- 
        # _send_comment_notification needs update if it used class_id
        _send_comment_notification(request, comentario) 
    else:
        # Handle invalid form - maybe display errors on the detail page?
        # For simplicity, just show a generic error for now.
        messages.error(request, _("Could not add comment. Please check your input."))
        # Optionally, re-render the detail page with the form errors:
        # context = { ... post_detail context ... , 'comment_form': form}
        # return render(request, 'blog/post_detail.html', context)

    # Redirect back to the post detail page regardless of success/failure for now
    return redirect('blog:post_detail', post_id=post_id)

# Use the new decorator and require POST
@require_POST
@login_required
def comment_remove(request, comment_id): # Removed class_id, post_id
    """Handles removing (soft deleting) a comment via POST request."""
    comment = get_object_or_404(Comment.objects.select_related('post__turma'), id=comment_id)
    post = comment.post # Get post from comment
    turma = post.turma
    user = request.user
    
    # --- Permission Check --- 
    is_admin_or_superuser = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
    is_teacher_of_class = False
    if hasattr(user, 'role') and user.role == 'professor':
        is_teacher_of_class = user.classes_taught.filter(id=turma.id).exists()
        
    # Permission: Admin/Superuser OR Teacher of the post's class
    if not (is_admin_or_superuser or is_teacher_of_class):
        messages.error(request, _("You do not have permission to remove this comment."))
        return redirect('blog:post_detail', post_id=post.id)
    
    motivo = request.POST.get('motivo', '') # Reason from POST
    comment.remover(request.user, motivo=motivo) # Call model method
    messages.success(request, _("Comment removed successfully."))
    
    # Redirect back to the post detail page
    return redirect('blog:post_detail', post_id=post.id)


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
        return redirect('class_blog:post_list', class_id=class_id)
        
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
def post_restore(request, post_id): # Removed class_id
    """Restores a previously removed post (restricted to teachers/admins)."""
    # Fetch post even if removed, include turma
    post = get_object_or_404(Post.objects.select_related('turma'), pk=post_id)
    turma = post.turma
    user = request.user

    # --- Permission Check --- 
    is_admin_or_superuser = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
    is_teacher_of_class = False
    if hasattr(user, 'role') and user.role == 'professor':
        is_teacher_of_class = user.classes_taught.filter(id=turma.id).exists()

    if not (is_admin_or_superuser or is_teacher_of_class):
        messages.error(request, _('You do not have permission to restore this post.'))
        return redirect('blog:post_detail', post_id=post_id)

    if not post.removido:
        messages.info(request, _('This post is already active.'))
        return redirect('blog:post_detail', post_id=post_id)

    # --- Restore Post --- 
    post.removido = False
    post.removido_por = None
    post.removido_em = None
    post.motivo_remocao = ''
    # Also set status back to published (assuming it should be visible after restore)
    # If it was pending before removal, moderator might need to approve again?
    # For now, let's restore to Published directly.
    if post.status != 'PUBLISHED': # Avoid unnecessary status change if already published
        post.status = 'PUBLISHED'
        # Reset approval info if restoring makes sense?
        # post.approved_by = user # Or keep original approver?
        # post.approved_at = timezone.now()
        
    # Combine fields to update
    update_fields = ['removido', 'removido_por', 'removido_em', 'motivo_remocao']
    if post.status == 'PUBLISHED': # Only include status if it was changed
        update_fields.append('status')
        # update_fields.extend(['approved_by', 'approved_at']) # If resetting approval info
        
    post.save(update_fields=update_fields)
    
    # --- Log Restoration --- 
    ModerationLog.objects.create(
        acao='RESTAURAR_POST',
        user=user,
        post=post,
        motivo=_('Restored by moderation'),
        # No content snapshot needed for restore usually
    )
    messages.success(request, _('Post restored successfully.'))
    return redirect('blog:post_detail', post_id=post_id)

# Helper function for sending post notifications
def _send_post_notification(request, post):
    """Sends email notifications about a new post to class members and guardians."""
    turma = post.turma
    # Get students and teachers emails, excluding the author
    recipients = list(turma.students.exclude(id=post.autor.id).values_list('email', flat=True)) + \
                 list(turma.teachers.exclude(id=post.autor.id).values_list('email', flat=True))
    recipients = [email for email in recipients if email] # Filter out empty emails

    try:
        # Use reverse with only post_id for the new URL structure
        post_url = request.build_absolute_uri(reverse('blog:post_detail', args=[post.id]))
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

    # Notify guardians only for AVISO (announcements)
    if post.categoria in ['AVISO']:
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
            # Use reverse with only post_id for the new URL structure
            post_url = request.build_absolute_uri(
                reverse('blog:post_detail', args=[post.id])
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

# --- New View for Public Blog Listing --- 

@require_GET # Only allow GET requests
def post_list_public(request):
    """
    Displays a public list of recent blog posts.
    This view will serve as the new site landing page.
    """
    # Fetch only PUBLISHED, non-removed posts
    all_posts = Post.objects.filter(
        status='PUBLISHED',
        removido=False
    ).select_related('autor', 'turma').order_by('-publicado_em') 

    # Optional filtering
    categoria_atual = request.GET.get('categoria', '')
    data_atual = request.GET.get('data', '')

    if categoria_atual:
        all_posts = all_posts.filter(categoria=categoria_atual)
    if data_atual:
        try:
            data = timezone.datetime.strptime(data_atual, '%Y-%m-%d').date()
            all_posts = all_posts.filter(publicado_em__date=data)
        except ValueError:
            messages.warning(request, _("Invalid date format for filtering."))

    # Pagination
    paginator = Paginator(all_posts, 10) # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj, # Pass the page object to the template
        'categorias': Post.CATEGORIA_CHOICES,
        'categoria_atual': categoria_atual,
        'data_atual': data_atual,
    }
    # Render a new template specifically for the public list
    return render(request, 'blog/post_list_public.html', context)

# --- Approval Workflow Views ---

@require_POST
@login_required
# @group_required('professor', 'admin') # Use inline check for more specific class context
def post_approve(request, post_id):
    """Approves a pending post for publication."""
    post = get_object_or_404(Post.objects.select_related('turma'), id=post_id)
    user = request.user
    
    # --- Permission Check --- 
    is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
    is_teacher_of_class = False
    if hasattr(user, 'role') and user.role == 'professor':
        is_teacher_of_class = post.turma in getattr(user, 'classes_taught', Class.objects.none()).all()

    if not (is_admin or is_teacher_of_class):
        messages.error(request, _('You do not have permission to approve this post.'))
        # Redirect to detail or pending list? Detail is safer.
        return redirect('blog:post_detail', post_id=post_id)
        
    if post.status == 'PENDING':
        post.approve(user)
        messages.success(request, _('Post approved and published.'))
        _send_post_notification(request, post) # Notify now that it's published
    else:
        messages.info(request, _('This post is not pending approval.'))
        
    return redirect('blog:post_detail', post_id=post_id)

@login_required
# @group_required('professor', 'admin') # Use inline check for more specific class context
def post_pending_list(request):
    """Lists posts pending approval, accessible by teachers/admins."""
    user = request.user
    # --- Permission Check --- 
    is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
    is_teacher = hasattr(user, 'role') and user.role == 'professor'

    if not (is_admin or is_teacher):
        messages.error(request, _('Access restricted to teachers and administrators.'))
        return redirect('blog:post_list_public') # Redirect non-mods away
        
    # Admins see all pending posts
    if is_admin:
        pending_posts = Post.objects.filter(status='PENDING', removido=False).select_related('autor', 'turma').order_by('publicado_em')
    # Teachers see pending posts only from their classes
    elif is_teacher:
        teacher_classes = getattr(user, 'classes_taught', Class.objects.none()).all()
        pending_posts = Post.objects.filter(
            status='PENDING', 
            removido=False, 
            turma__in=teacher_classes
        ).select_related('autor', 'turma').order_by('publicado_em')
    else: # Should not happen due to initial check, but good practice
        pending_posts = Post.objects.none()
        
    context = {
        'pending_posts': pending_posts
    }
    return render(request, 'blog/post_pending_list.html', context)

# --- New Global Post Creation View ---
@login_required
def post_create_global(request):
    """Handles the creation of a new post via the global form (with class selection)."""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            # Turma is selected in the form
            # post.turma = form.cleaned_data['turma'] # Already handled by ModelForm
            post.autor = request.user
            
            # Set Initial Status based on Author Role
            if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role in ['admin', 'professor']):
                post.status = 'PUBLISHED'
                post.approved_by = request.user
                post.approved_at = timezone.now()
            else: # Student post
                post.status = 'PENDING'
                post.approved_by = None
                post.approved_at = None
                
            post.save()
            # form.save_m2m() # If using M2M fields later
            
            if post.status == 'PUBLISHED':
                messages.success(request, _("Post published successfully."))
                # _send_post_notification(request, post) # Requires check/update
            else:
                messages.success(request, _("Post submitted for approval."))
                # _send_pending_post_notification(request, post) # Optional
                
            return redirect('blog:post_detail', post_id=post.id)
        else:
            messages.error(request, _("Please correct the errors below."))
    else:
        form = PostForm()
        # TODO: Potentially limit the 'turma' queryset in the form 
        # based on the request.user's role/memberships here for GET request?
        # Example (restrict students/teachers):
        # if not request.user.is_superuser and not request.user.role == 'admin':
        #    allowed_classes = Class.objects.filter(models.Q(teachers=request.user) | models.Q(students=request.user)).distinct()
        #    form.fields['turma'].queryset = allowed_classes
        
    context = {
        'form': form,
        'edit_mode': False,
    }
    # Use a generic form template, maybe rename post_form.html?
    return render(request, 'blog/post_form_global.html', context)

# --- TinyMCE Image Upload View ---
@csrf_exempt # TinyMCE might not send CSRF token
@login_required # Ensure only logged-in users can upload
@require_POST # Only accept POST requests
def tinymce_image_upload(request):
    """
    Receives an image upload from TinyMCE, saves it, and returns the URL.
    """
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded.'}, status=400)

    uploaded_file = request.FILES['file']

    # Basic validation (optional, enhance as needed)
    allowed_content_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if uploaded_file.content_type not in allowed_content_types:
        return JsonResponse({'error': f'Invalid file type: {uploaded_file.content_type}. Allowed: {", ".join(allowed_content_types)}'}, status=400)

    # Max size validation (e.g., 5MB)
    max_size = 5 * 1024 * 1024 # 5MB
    if uploaded_file.size > max_size:
        return JsonResponse({'error': f'File size exceeds limit ({max_size / 1024 / 1024}MB).'}, status=400)

    # Generate a unique filename with date structure
    today = datetime.now()
    file_ext = os.path.splitext(uploaded_file.name)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    # Define path within MEDIA_ROOT
    upload_path = os.path.join(
        'uploads',
        'posts',
        'images',
        today.strftime('%Y'),
        today.strftime('%m'),
        unique_filename
    )

    try:
        # Save the file using Django's default storage
        saved_path = default_storage.save(upload_path, uploaded_file)
        # Get the public URL for the saved file
        file_url = default_storage.url(saved_path)

        # TinyMCE expects a JSON response with a 'location' key
        return JsonResponse({'location': file_url})

    except Exception as e:
        # Log the error (consider proper logging setup)
        print(f"Error uploading file: {e}")
        return JsonResponse({'error': 'Failed to save uploaded file.'}, status=500)
