from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Post, ModerationLog
from .permissions import turma_member_required, turma_post_create_required, post_edit_permission_required
from classes.models import Class
from django.core.paginator import Paginator
from django.utils import timezone
from .forms import PostForm, CommentForm
from collections import OrderedDict
import itertools
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from users.models import GuardianRelation
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET

# Create your views here.

@turma_member_required
def post_list(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    posts = Post.objects.filter(turma=turma, removido=False).order_by('-publicado_em')

    categoria_atual = request.GET.get('categoria', '')
    data_atual = request.GET.get('data', '')

    if categoria_atual:
        posts = posts.filter(categoria=categoria_atual)
    if data_atual:
        try:
            data = timezone.datetime.strptime(data_atual, '%Y-%m-%d').date()
            posts = posts.filter(publicado_em__date=data)
        except ValueError:
            pass

    categorias = Post.CATEGORIA_CHOICES
    paginator = Paginator(posts, 50)  # Paginação maior para agrupar
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Agrupamento por mês/ano
    def group_key(post):
        return post.publicado_em.strftime('%Y-%m')
    posts_grouped = OrderedDict()
    for key, group in itertools.groupby(page_obj, key=group_key):
        ano, mes = key.split('-')
        posts_grouped[(int(ano), int(mes))] = list(group)

    context = {
        'turma': turma,
        'posts': page_obj,
        'posts_grouped': posts_grouped,
        'categorias': categorias,
        'categoria_atual': categoria_atual,
        'data_atual': data_atual,
    }
    return render(request, 'blog/post_list.html', context)

@turma_member_required
def post_detail(request, class_id, post_id):
    turma = get_object_or_404(Class, id=class_id)
    post = get_object_or_404(Post, id=post_id, turma=turma)
    comentarios = post.comments.filter(removido=False).order_by('publicado_em')
    post.is_editable_by_user = post.is_editable_by(request.user)
    context = {
        'turma': turma,
        'post': post,
        'comentarios': comentarios,
    }
    return render(request, 'blog/post_detail.html', context)

@turma_post_create_required
def post_create(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.turma = turma
            post.autor = request.user
            post.save()
            # Enviar email para alunos e professores da turma
            recipients = list(turma.students.values_list('email', flat=True)) + list(turma.teachers.values_list('email', flat=True))
            recipients = [email for email in recipients if email]  # Remove vazios
            if recipients:
                subject = f"Novo post no blog da turma {turma.name} ({turma.year})"
                post_url = request.build_absolute_uri(reverse('blog_post_detail', args=[turma.id, post.id]))
                message = f"Título: {post.titulo or '(sem título)'}\nAutor: {post.autor.get_full_name() or post.autor.username}\n\n{post.conteudo[:200]}...\n\nVer post completo: {post_url}"
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipients,
                    fail_silently=True,
                )
            # Notificar encarregados se categoria for DIARIO ou AVISO
            if post.categoria in ['DIARIO', 'AVISO']:
                alunos_ids = turma.students.values_list('id', flat=True)
                encarregados = GuardianRelation.objects.filter(aluno_id__in=alunos_ids).select_related('encarregado')
                encarregado_emails = list(set([rel.encarregado.email for rel in encarregados if rel.encarregado.email]))
                if encarregado_emails:
                    subject = f"Novo comunicado da turma {turma.name} ({turma.year})"
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        encarregado_emails,
                        fail_silently=True,
                    )
            return redirect('blog_post_list', class_id=class_id)
    else:
        form = PostForm()
    context = {
        'turma': turma,
        'form': form,
    }
    return render(request, 'blog/post_form.html', context)

@post_edit_permission_required
def post_edit(request, class_id, post_id):
    turma = get_object_or_404(Class, id=class_id)
    post = get_object_or_404(Post, id=post_id, turma=turma)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog_post_detail', class_id=class_id, post_id=post_id)
    else:
        form = PostForm(instance=post)
    context = {
        'turma': turma,
        'form': form,
        'post': post,
        'edit_mode': True,
    }
    return render(request, 'blog/post_form.html', context)

@post_edit_permission_required
def post_remove(request, class_id, post_id):
    turma = get_object_or_404(Class, id=class_id)
    post = get_object_or_404(Post, id=post_id, turma=turma)
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        post.remover(request.user, motivo=motivo)
        return redirect('blog_post_list', class_id=class_id)
    context = {
        'turma': turma,
        'post': post,
    }
    return render(request, 'blog/post_confirm_remove.html', context)

@turma_member_required
def post_comment(request, class_id, post_id):
    turma = get_object_or_404(Class, id=class_id)
    post = get_object_or_404(Post, id=post_id, turma=turma)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.post = post
            comentario.autor = request.user
            comentario.save()
            # Notificar autor do post se não for o próprio autor do comentário
            if post.autor != request.user and post.autor.email:
                subject = f'Novo comentário no seu post "{post.titulo or post.get_category_display()}"'
                post_url = request.build_absolute_uri(reverse('blog_post_detail', args=[turma.id, post.id]))
                message = f"{request.user.get_full_name() or request.user.username} comentou no seu post.\n\nComentário: {comentario.conteudo[:200]}...\n\nVer post: {post_url}"
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [post.autor.email],
                    fail_silently=True,
                )
    return redirect('blog_post_detail', class_id=class_id, post_id=post_id)

@turma_member_required
def comment_remove(request, class_id, post_id, comment_id):
    turma = get_object_or_404(Class, id=class_id)
    post = get_object_or_404(Post, id=post_id, turma=turma)
    comentario = get_object_or_404(post.comments, id=comment_id)
    user = request.user
    pode_remover = False
    if hasattr(user, 'role') and user.role == 'admin':
        pode_remover = True
    elif hasattr(user, 'role') and user.role == 'professor' and turma in getattr(user, 'turmas', []):
        pode_remover = True
    elif post.autor == user:
        pode_remover = True
    if not pode_remover:
        from django.contrib import messages
        messages.error(request, 'Sem permissão para remover este comentário.')
        return redirect('blog_post_detail', class_id=class_id, post_id=post_id)
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        comentario.remover(user, motivo=motivo)
        return redirect('blog_post_detail', class_id=class_id, post_id=post_id)
    context = {
        'turma': turma,
        'post': post,
        'comentario': comentario,
    }
    return render(request, 'blog/comment_confirm_remove.html', context)

@login_required
def moderation_logs(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    user = request.user
    # Apenas admin ou professor da turma
    if not (user.role == 'admin' or (user.role == 'professor' and turma in user.classes_taught.all())):
        from django.contrib import messages
        messages.error(request, 'Acesso restrito à moderação da turma.')
        return redirect('blog_post_list', class_id=class_id)
    logs = ModerationLog.objects.filter(
        post__turma=turma
    ).order_by('-data')[:100]
    context = {
        'turma': turma,
        'logs': logs,
    }
    return render(request, 'blog/moderation_logs.html', context)

@require_POST
@login_required
def post_restore(request, class_id, post_id):
    turma = get_object_or_404(Class, id=class_id)
    post = get_object_or_404(Post, id=post_id, turma=turma)
    user = request.user
    if not (user.role == 'admin' or (user.role == 'professor' and turma in user.classes_taught.all())):
        from django.contrib import messages
        messages.error(request, 'Acesso restrito à restauração de posts.')
        return redirect('blog_post_detail', class_id=class_id, post_id=post_id)
    if not post.removido:
        from django.contrib import messages
        messages.info(request, 'O post já está ativo.')
        return redirect('blog_post_detail', class_id=class_id, post_id=post_id)
    # Restaurar
    post.removido = False
    post.removido_por = None
    post.removido_em = None
    post.motivo_remocao = ''
    post.save()
    from .models import ModerationLog
    ModerationLog.objects.create(
        acao='RESTAURAR_POST',
        user=user,
        post=post,
        motivo='Restaurado por moderação',
        conteudo_snapshot=post.conteudo,
    )
    from django.contrib import messages
    messages.success(request, 'Post restaurado com sucesso.')
    return redirect('blog_post_detail', class_id=class_id, post_id=post_id)

@require_GET
def blog_help(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    return render(request, 'blog/blog_help.html', {'turma': turma})
