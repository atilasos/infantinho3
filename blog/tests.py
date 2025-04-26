from django.test import TestCase
from django.utils import timezone
from users.models import User, GuardianRelation
from classes.models import Class
from .models import Post, Comment
from django.urls import reverse
from django.core import mail

class BlogModelTests(TestCase):
    def setUp(self):
        # Criar utilizadores
        self.admin = User.objects.create_user(username='admin', email='admin@escola.pt', password='admin', role='admin', status='ativo')
        self.prof = User.objects.create_user(username='prof', email='prof@escola.pt', password='prof', role='professor', status='ativo')
        self.aluno = User.objects.create_user(username='aluno', email='aluno@escola.pt', password='aluno', role='aluno', status='ativo')
        self.aluno2 = User.objects.create_user(username='aluno2', email='aluno2@escola.pt', password='aluno2', role='aluno', status='ativo')
        # Criar turma e associar
        self.turma = Class.objects.create(name='Turma A', year=2024)
        self.turma.students.add(self.aluno)
        self.turma.teachers.add(self.prof)
        # Garantir relações ManyToMany corretas
        self.prof.refresh_from_db()
        self.aluno.refresh_from_db()
        self.admin.refresh_from_db()
        self.aluno2.refresh_from_db()

    def test_criacao_post_diario_com_subcategoria(self):
        post = Post.objects.create(
            turma=self.turma,
            autor=self.aluno,
            titulo='Diário',
            conteudo='Hoje fizemos...',
            categoria='DIARIO',
            subcategoria_diario='GOSTEI',
        )
        self.assertEqual(post.subcategoria_diario, 'GOSTEI')
        self.assertEqual(post.categoria, 'DIARIO')

    def test_criacao_post_diario_sem_subcategoria(self):
        post = Post(
            turma=self.turma,
            autor=self.aluno,
            titulo='Diário',
            conteudo='Hoje fizemos...',
            categoria='DIARIO',
        )
        with self.assertRaises(Exception):
            post.full_clean()  # subcategoria_diario deve ser obrigatória para DIARIO

    def test_criacao_post_nao_diario_com_subcategoria(self):
        post = Post.objects.create(
            turma=self.turma,
            autor=self.prof,
            titulo='Aviso',
            conteudo='Amanhã não há aula',
            categoria='AVISO',
            subcategoria_diario='',
        )
        self.assertEqual(post.subcategoria_diario, '')

    def test_is_editable_by(self):
        post = Post.objects.create(
            turma=self.turma,
            autor=self.aluno,
            titulo='Diário',
            conteudo='Hoje fizemos...',
            categoria='DIARIO',
            subcategoria_diario='FIZEMOS',
        )
        self.assertTrue(post.is_editable_by(self.aluno))
        self.assertTrue(post.is_editable_by(self.admin))
        self.assertFalse(post.is_editable_by(self.aluno2))
        self.assertFalse(post.is_editable_by(self.prof))  # Professor não pode editar diário de aluno

    def test_is_visible_to(self):
        post_diario = Post.objects.create(
            turma=self.turma,
            autor=self.aluno,
            titulo='Diário',
            conteudo='Hoje fizemos...',
            categoria='DIARIO',
            subcategoria_diario='FIZEMOS',
        )
        post_publico = Post.objects.create(
            turma=self.turma,
            autor=self.prof,
            titulo='Projeto',
            conteudo='Projeto aberto',
            categoria='PROJETO',
            visibilidade='PUBLICA',
        )
        self.assertTrue(post_diario.is_visible_to(self.aluno))
        self.assertTrue(post_diario.is_visible_to(self.prof))
        self.assertTrue(post_diario.is_visible_to(self.admin))
        self.assertFalse(post_diario.is_visible_to(self.aluno2))
        self.assertTrue(post_publico.is_visible_to(self.aluno2))

    def test_comentario_moderacao(self):
        post = Post.objects.create(
            turma=self.turma,
            autor=self.prof,
            titulo='Aviso',
            conteudo='Amanhã não há aula',
            categoria='AVISO',
        )
        comentario = Comment.objects.create(
            post=post,
            autor=self.aluno,
            conteudo='Mensagem inadequada',
        )
        self.assertFalse(comentario.removido)
        comentario.remover(self.prof, motivo='Inadequado')
        self.assertTrue(comentario.removido)
        self.assertEqual(comentario.removido_por, self.prof)
        self.assertEqual(comentario.motivo_remocao, 'Inadequado')
        self.assertIsNotNone(comentario.removido_em)
        # Não pode remover novamente
        comentario.remover(self.admin, motivo='Outro motivo')
        self.assertEqual(comentario.removido_por, self.prof)  # Não deve sobrescrever

    def test_str_internacionalizacao(self):
        post = Post.objects.create(
            turma=self.turma,
            autor=self.prof,
            titulo='Aviso',
            conteudo='Amanhã não há aula',
            categoria='AVISO',
        )
        comentario = Comment.objects.create(
            post=post,
            autor=self.aluno,
            conteudo='Mensagem',
        )
        self.assertIn('Comentário de', str(comentario))

    def test_envio_email_ao_criar_post(self):
        self.client.force_login(self.prof)
        url = reverse('blog_post_create', args=[self.turma.id])
        data = {
            'titulo': 'Novo Aviso',
            'conteudo': 'Conteúdo do aviso para a turma.',
            'categoria': 'AVISO',
            'subcategoria_diario': '',
            'visibilidade': 'INTERNA',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Verifica se email foi enviado
        self.assertGreaterEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Novo post no blog da turma', email.subject)
        self.assertIn(self.aluno.email, email.to)
        self.assertIn(self.prof.email, email.to)
        self.assertIn('Novo Aviso', email.body)
        self.assertIn('Conteúdo do aviso', email.body)

    def test_envio_email_para_encarregado_diario_aviso(self):
        # Cria encarregado para o aluno
        encarregado = User.objects.create_user(username='pai', email='pai@familia.pt', password='123', role='encarregado', status='ativo')
        GuardianRelation.objects.create(aluno=self.aluno, encarregado=encarregado, parentesco='Pai')
        self.client.force_login(self.prof)
        url = reverse('blog_post_create', args=[self.turma.id])
        data = {
            'titulo': 'Diário de Turma',
            'conteudo': 'Hoje fizemos...',
            'categoria': 'DIARIO',
            'subcategoria_diario': 'GOSTEI',
            'visibilidade': 'INTERNA',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Verifica se email foi enviado para encarregado
        emails = [email for m in mail.outbox for email in m.to]
        self.assertIn(encarregado.email, emails)

    def test_envio_email_para_autor_ao_comentar(self):
        post = Post.objects.create(
            turma=self.turma,
            autor=self.aluno,
            titulo='Diário',
            conteudo='Hoje fizemos...',
            categoria='DIARIO',
            subcategoria_diario='GOSTEI',
        )
        self.client.force_login(self.prof)
        url = reverse('blog_post_comment', args=[self.turma.id, post.id])
        data = {'conteudo': 'Parabéns pelo post!'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Verifica se email foi enviado para o autor do post
        emails = [email for m in mail.outbox for email in m.to]
        self.assertIn(self.aluno.email, emails)

    def test_post_moderacao_remocao(self):
        post = Post.objects.create(
            turma=self.turma,
            autor=self.prof,
            titulo='Aviso',
            conteudo='Amanhã não há aula',
            categoria='AVISO',
        )
        self.assertFalse(post.removido)
        post.remover(self.admin, motivo='Inadequado')
        self.assertTrue(post.removido)
        self.assertEqual(post.removido_por, self.admin)
        self.assertEqual(post.motivo_remocao, 'Inadequado')
        self.assertIsNotNone(post.removido_em)
        # Não pode remover novamente
        post.remover(self.prof, motivo='Outro motivo')
        self.assertEqual(post.removido_por, self.admin)  # Não deve sobrescrever
        # Verifica se log foi criado
        from blog.models import ModerationLog
        logs = ModerationLog.objects.filter(post=post, acao='REMOVER_POST')
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().user, self.admin)
        self.assertEqual(logs.first().motivo, 'Inadequado')

    def test_logs_moderacao_visiveis_para_admin_professor(self):
        post = Post.objects.create(
            turma=self.turma,
            autor=self.prof,
            titulo='Aviso',
            conteudo='Amanhã não há aula',
            categoria='AVISO',
        )
        post.remover(self.admin, motivo='Inadequado')
        url = reverse('blog_moderation_logs', args=[self.turma.id])
        # Admin pode ver
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Remover Post')
        # Professor da turma pode ver
        self.client.force_login(self.prof)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Aluno não pode ver
        self.client.force_login(self.aluno)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_restaurar_post_removido(self):
        post = Post.objects.create(
            turma=self.turma,
            autor=self.prof,
            titulo='Aviso',
            conteudo='Amanhã não há aula',
            categoria='AVISO',
        )
        post.remover(self.admin, motivo='Inadequado')
        url = reverse('blog_post_restore', args=[self.turma.id, post.id])
        # Professor pode restaurar
        self.client.force_login(self.prof)
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertFalse(post.removido)
        # Log de restauração criado
        from blog.models import ModerationLog
        logs = ModerationLog.objects.filter(post=post, acao='RESTAURAR_POST')
        self.assertEqual(logs.count(), 1)
        # Aluno não pode restaurar
        post.remover(self.admin, motivo='Inadequado')
        self.client.force_login(self.aluno)
        response = self.client.post(url, follow=True)
        post.refresh_from_db()
        self.assertTrue(post.removido)
        # Admin pode restaurar
        self.client.force_login(self.admin)
        response = self.client.post(url, follow=True)
        post.refresh_from_db()
        self.assertFalse(post.removido)
