from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from blog.models import Post
from classes.models import Class

def turma_member_required(view_func):
    """Permite acesso apenas a membros da turma (alunos, professores, encarregados) e admin."""
    @wraps(view_func)
    def _wrapped_view(request, class_id, *args, **kwargs):
        turma = get_object_or_404(Class, id=class_id)
        user = request.user
        if not user.is_authenticated:
            messages.error(request, 'É necessário autenticação.')
            return redirect('landing_page')
        if hasattr(user, 'role') and user.role == 'admin':
            return view_func(request, class_id, *args, **kwargs)
        # Verifica se user é aluno ou professor da turma
        if (turma in user.classes_attended.all()) or (turma in user.classes_taught.all()):
            return view_func(request, class_id, *args, **kwargs)
        # TODO: permitir encarregado se for responsável por aluno da turma
        messages.error(request, 'Acesso restrito à turma.')
        return redirect('landing_page')
    return _wrapped_view

def turma_post_create_required(view_func):
    """Permite criar posts apenas a professores e alunos da turma (ou admin)."""
    @wraps(view_func)
    def _wrapped_view(request, class_id, *args, **kwargs):
        turma = get_object_or_404(Class, id=class_id)
        user = request.user
        if not user.is_authenticated:
            messages.error(request, 'É necessário autenticação.')
            return redirect('landing_page')
        if hasattr(user, 'role') and user.role == 'admin':
            return view_func(request, class_id, *args, **kwargs)
        if ((turma in user.classes_attended.all()) and user.role == 'aluno') or ((turma in user.classes_taught.all()) and user.role == 'professor'):
            return view_func(request, class_id, *args, **kwargs)
        messages.error(request, 'Apenas professores e alunos da turma podem criar posts.')
        return redirect('blog_post_list', class_id=class_id)
    return _wrapped_view

def post_edit_permission_required(view_func):
    """Permite editar/remover posts conforme regras: professores da turma ou autor (aluno)."""
    @wraps(view_func)
    def _wrapped_view(request, class_id, post_id, *args, **kwargs):
        post = get_object_or_404(Post, id=post_id, turma_id=class_id)
        user = request.user
        if not user.is_authenticated:
            messages.error(request, 'É necessário autenticação.')
            return redirect('landing_page')
        if post.is_editable_by(user):
            return view_func(request, class_id, post_id, *args, **kwargs)
        messages.error(request, 'Sem permissão para editar/remover este post.')
        return redirect('blog_post_detail', class_id=class_id, post_id=post_id)
    return _wrapped_view 