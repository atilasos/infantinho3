# blog/permissions.py
from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import Http404, HttpResponseForbidden
from django.utils.translation import gettext_lazy as _

# Assuming models are defined
from .models import Post, Comment 
from classes.models import Class

def turma_member_required(view_func):
    """
    Decorator: Allows access only to authenticated users who are members of the class 
    (student, teacher, associated guardian) or administrators.
    Redirects unauthenticated users or non-members.
    Assumes 'class_id' is a keyword argument in the view.
    """
    @wraps(view_func)
    def _wrapped_view(request, class_id, *args, **kwargs):
        turma = get_object_or_404(Class, id=class_id)
        user = request.user

        # Check authentication
        if not user.is_authenticated:
            messages.error(request, _('Authentication is required.'))
            # Correct the redirect URL for unauthenticated users
            login_url = reverse('users:login_choice')
            return redirect(f'{login_url}?next={request.path}') 

        # Check permissions
        allowed = False
        if user.is_superuser or (hasattr(user, 'role') and user.role == 'admin'):
            allowed = True
        else:
            # Optimized checks using exists()
            is_student = getattr(user, 'classes_attended', Class.objects.none()).filter(pk=turma.pk).exists()
            is_teacher = getattr(user, 'classes_taught', Class.objects.none()).filter(pk=turma.pk).exists()
            is_guardian = False
            if hasattr(user, 'role') and user.role == 'encarregado':
                is_guardian = turma.students.filter(encarregados_relations__encarregado=user).exists()
            
            if is_student or is_teacher or is_guardian:
                allowed = True

        if allowed:
            return view_func(request, class_id, *args, **kwargs)
        else:
            # Return 403 Forbidden for authenticated users who are not members
            # messages.error(request, _('Access restricted to this class members.'))
            # return redirect('landing_page') # Old redirect
            return HttpResponseForbidden(_('Access restricted to members of this class.'))
    return _wrapped_view

def turma_post_create_required(view_func):
    """
    Decorator: Allows post creation only by authenticated students or teachers 
    of the class, or administrators.
    Assumes 'class_id' is a keyword argument in the view.
    """
    @wraps(view_func)
    def _wrapped_view(request, class_id, *args, **kwargs):
        turma = get_object_or_404(Class, id=class_id)
        user = request.user

        # Check authentication
        if not user.is_authenticated:
            messages.error(request, _('Authentication is required.'))
            # Redirect to login choice, not landing page
            login_url = reverse('users:login_choice')
            return redirect(f'{login_url}?next={request.path}')

        # Check permissions
        allowed = False
        if user.is_superuser or (hasattr(user, 'role') and user.role == 'admin'):
            allowed = True
        elif hasattr(user, 'role'):
            is_student_in_class = user.role == 'aluno' and turma in getattr(user, 'classes_attended', Class.objects.none()).all()
            is_teacher_in_class = user.role == 'professor' and turma in getattr(user, 'classes_taught', Class.objects.none()).all()
            if is_student_in_class or is_teacher_in_class:
                allowed = True

        if allowed:
            return view_func(request, class_id, *args, **kwargs)
        else:
            # Return 403 Forbidden instead of redirecting
            # messages.error(request, _('Only teachers and students of this class can create posts.'))
            # return redirect('blog:post_list', class_id=class_id)
            return HttpResponseForbidden(_('Only teachers and students of this class can create posts.'))
    return _wrapped_view

def post_edit_permission_required(view_func):
    """
    Decorator: Allows editing a post only by its author or an administrator.
    Checks Post.is_editable_by() method.
    Assumes 'class_id' and 'post_id' are keyword arguments in the view.
    """
    @wraps(view_func)
    def _wrapped_view(request, class_id, post_id, *args, **kwargs):
        post = get_object_or_404(Post, id=post_id, turma_id=class_id)
        user = request.user

        if not user.is_authenticated:
            messages.error(request, _('Authentication is required.'))
            # Redirect to login choice, not landing page
            login_url = reverse('users:login_choice')
            return redirect(f'{login_url}?next={request.path}')

        # Use the model's method to check edit permission
        if post.is_editable_by(user):
            return view_func(request, class_id, post_id, *args, **kwargs)
        else:
            # Return 403 Forbidden instead of redirecting
            # messages.error(request, _('You do not have permission to edit this post.'))
            # return redirect('blog:post_detail', class_id=class_id, post_id=post_id)
            return HttpResponseForbidden(_('You do not have permission to edit this post.'))
    return _wrapped_view

def post_remove_permission_required(view_func):
    """
    Decorator: Allows removing a post only by a teacher of the class or an administrator.
    Checks Post.is_removable_by() method.
    Assumes 'class_id' and 'post_id' are keyword arguments in the view.
    """
    @wraps(view_func)
    def _wrapped_view(request, class_id, post_id, *args, **kwargs):
        post = get_object_or_404(Post, id=post_id, turma_id=class_id)
        user = request.user

        if not user.is_authenticated:
            messages.error(request, _('Authentication is required.'))
            # Redirect to login choice, not landing page
            login_url = reverse('users:login_choice')
            return redirect(f'{login_url}?next={request.path}')

        # Use the model's method to check removal permission
        if post.is_removable_by(user):
            return view_func(request, class_id, post_id, *args, **kwargs)
        else:
            # Return 403 Forbidden instead of redirecting
            # messages.error(request, _('You do not have permission to remove this post.'))
            # return redirect('blog:post_detail', class_id=class_id, post_id=post_id)
            return HttpResponseForbidden(_('You do not have permission to remove this post.'))
    return _wrapped_view

def comment_remove_permission_required(view_func):
    """
    Decorator: Allows removing a comment only by a teacher of the post's class or an administrator.
    Checks Comment.is_removable_by() method.
    Assumes 'class_id', 'post_id', and 'comment_id' are keyword arguments.
    """
    @wraps(view_func)
    def _wrapped_view(request, class_id, post_id, comment_id, *args, **kwargs):
        # Ensure the post exists and belongs to the class first
        post = get_object_or_404(Post, id=post_id, turma_id=class_id)
        comment = get_object_or_404(Comment, id=comment_id, post=post)
        user = request.user

        if not user.is_authenticated:
            messages.error(request, _('Authentication is required.'))
            # Redirect to login choice, not landing page
            login_url = reverse('users:login_choice')
            return redirect(f'{login_url}?next={request.path}')

        # Use the model's method to check removal permission
        if comment.is_removable_by(user):
            return view_func(request, class_id, post_id, comment_id, *args, **kwargs)
        else:
            # Return 403 Forbidden instead of redirecting
            # messages.error(request, _('You do not have permission to remove this comment.'))
            # return redirect('blog:post_detail', class_id=class_id, post_id=post_id)
            return HttpResponseForbidden(_('You do not have permission to remove this comment.'))
    return _wrapped_view
