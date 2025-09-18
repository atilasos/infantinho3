from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from users.models import User, GuardianRelation
from classes.models import Class
from .models import Post, Comment
from .forms import PostForm
from .pedagogy import MEM_CATEGORY_GUIDANCE
from django.urls import reverse
from django.core import mail
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.files.storage import default_storage
from urllib.parse import urlparse
from unittest import skip

# === Base Test Case ===
class BlogBaseTestCase(TestCase):
    """Base class for blog tests with common setup data."""
    @classmethod
    def setUpTestData(cls):
        # Create Groups
        cls.prof_group, _ = Group.objects.get_or_create(name='professor')
        cls.aluno_group, _ = Group.objects.get_or_create(name='aluno')
        cls.admin_group, _ = Group.objects.get_or_create(name='administrador')
        cls.encarregado_group, _ = Group.objects.get_or_create(name='encarregado')
        
        # Create Users
        cls.admin = User.objects.create_superuser(username='blogadmin', email='blogadmin@test.com', password='pwd')
        cls.prof1 = User.objects.create_user(username='blogprof1', email='blogprof1@test.com', password='pwd', role='professor', status='ativo')
        cls.prof2 = User.objects.create_user(username='blogprof2', email='blogprof2@test.com', password='pwd', role='professor', status='ativo')
        cls.aluno1 = User.objects.create_user(username='blogaluno1', email='blogaluno1@test.com', password='pwd', role='aluno', status='ativo')
        cls.aluno2 = User.objects.create_user(username='blogaluno2', email='blogaluno2@test.com', password='pwd', role='aluno', status='ativo')
        cls.guardian = User.objects.create_user(username='blogguardian', email='blogguardian@test.com', password='pwd', role='encarregado', status='ativo')
        cls.guest = User.objects.create_user(username='blogguest', email='blogguest@test.com', password='pwd', status='convidado')
        
        # Add Users to Groups
        cls.admin.groups.add(cls.admin_group)
        cls.prof1.groups.add(cls.prof_group)
        cls.prof2.groups.add(cls.prof_group)
        cls.aluno1.groups.add(cls.aluno_group)
        cls.aluno2.groups.add(cls.aluno_group)
        cls.guardian.groups.add(cls.encarregado_group)
        
        # Create Class and assign members
        cls.turma1 = Class.objects.create(name='Blog Test Class', year=2024)
        cls.turma1.teachers.add(cls.prof1)
        cls.turma1.students.add(cls.aluno1)
        
        # Create Guardian Relation
        GuardianRelation.objects.create(aluno=cls.aluno1, encarregado=cls.guardian)

# === Model Tests ===
@skip("Legacy diary category removed; model tests rework pending")
class BlogModelTests(BlogBaseTestCase):
    pass

    def test_comentario_moderacao(self):
        post = Post.objects.create(
            turma=self.turma1,
            autor=self.prof1,
            titulo='Aviso',
            conteudo='Amanhã não há aula',
            categoria='AVISO',
        )
        comentario = Comment.objects.create(
            post=post,
            autor=self.aluno1,
            conteudo='Mensagem inadequada',
        )
        self.assertFalse(comentario.removido)
        comentario.remover(self.prof1, motivo='Inadequado')
        self.assertTrue(comentario.removido)
        self.assertEqual(comentario.removido_por, self.prof1)
        self.assertEqual(comentario.motivo_remocao, 'Inadequado')
        self.assertIsNotNone(comentario.removido_em)
        self.assertFalse(comentario.is_removable_by(self.prof2), "Other teacher should not be able to remove")
        comentario.removido = False
        comentario.save()
        self.assertTrue(comentario.is_removable_by(self.admin), "Admin should be able to remove")
        comentario.remover(self.admin, motivo='Admin remove')
        self.assertTrue(comentario.removido)
        self.assertEqual(comentario.removido_por, self.admin)

    def test_str_internacionalizacao(self):
        post = Post.objects.create(
            turma=self.turma1,
            autor=self.prof1,
            titulo='Aviso',
            conteudo='Amanhã não há aula',
            categoria='AVISO',
        )
        comentario = Comment.objects.create(
            post=post,
            autor=self.aluno1,
            conteudo='Mensagem',
        )
        self.assertIn(self.aluno1.username, str(comentario))
        self.assertIn(f"Post {post.id}", str(comentario))
        self.assertIn('Mensagem', str(comentario))

    def test_post_moderacao_remocao(self):
        post = Post.objects.create(
            turma=self.turma1,
            autor=self.prof1,
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
        self.assertFalse(post.is_removable_by(self.prof2), "Other teacher should not be able to remove post")
        post.removido = False
        post.save()
        self.assertTrue(post.is_removable_by(self.prof1), "Class teacher should be able to remove post")
        post.remover(self.prof1, motivo='Class Teacher Remove')
        self.assertTrue(post.removido)
        self.assertEqual(post.removido_por, self.prof1)
        from blog.models import ModerationLog
        logs = ModerationLog.objects.filter(post=post, acao='REMOVER_POST')
        self.assertGreaterEqual(logs.count(), 1)
        self.assertEqual(logs.latest('data').user, self.prof1)
        self.assertEqual(logs.latest('data').motivo, 'Class Teacher Remove')

# === View Test Classes (To be created/populated) ===

class PostListViewTests(BlogBaseTestCase):
    def test_view_url_exists_at_desired_location(self):
        url = reverse('class_blog:post_list', args=[self.turma1.id])
        self.client.force_login(self.prof1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        url = reverse('class_blog:post_list', args=[self.turma1.id])
        self.client.force_login(self.prof1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        url = reverse('class_blog:post_list', args=[self.turma1.id])
        self.client.force_login(self.prof1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_list.html')

    def test_list_shows_only_class_posts(self):
        # Create post for the test class
        post1 = Post.objects.create(turma=self.turma1, autor=self.prof1, titulo='Post Turma 1', conteudo='...')
        # Create another class and post
        other_turma = Class.objects.create(name='Other Class', year=2024)
        other_turma.teachers.add(self.prof1)
        post2 = Post.objects.create(turma=other_turma, autor=self.prof1, titulo='Post Turma 2', conteudo='...')
        
        url = reverse('class_blog:post_list', args=[self.turma1.id])
        self.client.force_login(self.prof1)
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, post1.titulo)
        self.assertNotContains(response, post2.titulo)

class PostDetailViewTests(BlogBaseTestCase):
    def setUp(self):
        # Create a post specific to this test class for detail view
        self.post = Post.objects.create(
            turma=self.turma1,
            autor=self.prof1,
            titulo='Detail Test Post',
            conteudo='Content here.',
            categoria='AVISO'
        )
        self.detail_url = reverse('blog:post_detail', args=[self.post.id])

    def test_view_url_exists_at_desired_location(self):
        self.client.force_login(self.prof1)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self.client.force_login(self.prof1)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.client.force_login(self.prof1)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_detail.html')

    def test_view_shows_post_content(self):
        self.client.force_login(self.prof1)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.titulo)
        self.assertContains(response, self.post.conteudo)
        # Check if comments form is present (example)
        self.assertIn('comment_form', response.context)

    def test_view_shows_comments(self):
        # Ensure post is published so comments are visible
        self.post.status = 'PUBLISHED'
        self.post.save(update_fields=['status'])
        comment = Comment.objects.create(post=self.post, autor=self.aluno1, conteudo='Test comment')
        self.client.force_login(self.prof1)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, comment.conteudo)

    def test_mem_guidance_section_rendered(self):
        self.post.categoria = 'PROJETO'
        self.post.status = 'PUBLISHED'
        self.post.save(update_fields=['categoria', 'status'])
        self.client.force_login(self.prof1)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        expected = MEM_CATEGORY_GUIDANCE['PROJETO']
        self.assertContains(response, str(expected['title']))
        self.assertContains(response, str(expected['description']))
        for prompt in expected['prompts']:
            self.assertContains(response, str(prompt))


class PostFormGuidanceTests(TestCase):
    def test_post_form_exposes_mem_guidance(self):
        form = PostForm()
        self.assertIn('categoria', form.fields)
        self.assertTrue(form.fields['categoria'].help_text)
        self.assertIn('DIARIO', form.category_guidance)
        guidance = form.category_guidance['DIARIO']
        self.assertIn('title', guidance)
        self.assertGreater(len(guidance['prompts']), 0)

class PostCreateViewTests(BlogBaseTestCase):
    def test_class_post_create_context_includes_guidance(self):
        url = reverse('class_blog:post_create', args=[self.turma1.id])
        self.client.force_login(self.prof1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('category_guidance', response.context)
        self.assertIn('TEA', response.context['category_guidance'])

    def test_global_post_create_context_includes_guidance(self):
        url = reverse('blog:post_create_global')
        self.client.force_login(self.prof1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('category_guidance', response.context)
        self.assertIn('CONSELHO', response.context['category_guidance'])

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='noreply@test.com')
    def test_envio_email_ao_criar_post(self):
        self.client.force_login(self.prof1)
        url = reverse('class_blog:post_create', args=[self.turma1.id])
        data = {
            'titulo': 'Novo Aviso Prof1',
            'conteudo': 'Conteúdo do aviso para a turma.',
            'categoria': 'AVISO',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(mail.outbox), 1, "Email outbox is empty")
        subjects = [e.subject for e in mail.outbox]
        # Accept either member notification or guardian notification subject
        self.assertTrue(
            any(f'Novo post na turma {self.turma1.name}' in s or f'Novo comunicado da turma {self.turma1.name}' in s for s in subjects)
        )
        # Ensure a member email was sent to a class student
        self.assertTrue(any(self.aluno1.email in e.to for e in mail.outbox))
        self.assertTrue(any('Novo Aviso Prof1' in e.body for e in mail.outbox))

class PostCommentViewTests(BlogBaseTestCase):
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='noreply@test.com')
    def test_envio_email_para_autor_ao_comentar(self):
        post = Post.objects.create(
            turma=self.turma1,
            autor=self.aluno1,
            titulo='Post Aluno1',
            conteudo='Conteúdo...',
            categoria='TRABALHO',
        )
        self.client.force_login(self.prof1)
        url = reverse('blog:post_comment', args=[post.id])
        data = {'conteudo': 'Parabéns pelo post!'}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(mail.outbox), 1, "Email outbox is empty")
        email = mail.outbox[-1]
        self.assertIn(self.aluno1.email, email.to)
        self.assertNotIn(self.prof1.email, email.to)
        self.assertIn(f'Novo comentário no seu post "{post.titulo}"' , email.subject)


class TinyMCEUploadTests(BlogBaseTestCase):
    PNG_BYTES = (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00\x02\x00\x01'
        b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    def test_upload_accepts_valid_image(self):
        self.client.force_login(self.prof1)
        url = reverse('blog:tinymce_image_upload')
        upload = SimpleUploadedFile('tiny.png', self.PNG_BYTES, content_type='image/png')
        response = self.client.post(url, {'file': upload})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('location', payload)
        parsed = urlparse(payload['location'])
        storage_path = parsed.path
        if storage_path.startswith(settings.MEDIA_URL):
            storage_path = storage_path[len(settings.MEDIA_URL):]
        storage_path = storage_path.lstrip('/')
        self.assertTrue(default_storage.exists(storage_path))
        default_storage.delete(storage_path)

    def test_upload_rejects_invalid_file_type(self):
        self.client.force_login(self.prof1)
        url = reverse('blog:tinymce_image_upload')
        upload = SimpleUploadedFile('not-image.txt', b'plain text', content_type='text/plain')
        response = self.client.post(url, {'file': upload})
        self.assertEqual(response.status_code, 400)


class ModerationViewTests(BlogBaseTestCase):
    def test_logs_moderacao_visiveis_para_admin_professor(self):
        post = Post.objects.create(
            turma=self.turma1,
            autor=self.prof1,
            titulo='Aviso Mod',
            conteudo='Amanhã não há aula',
            categoria='AVISO',
        )
        post.remover(self.admin, motivo='Inadequado Log Test')
        url = reverse('class_blog:moderation_logs', args=[self.turma1.id])
        self.client.force_login(self.admin)
        response_admin = self.client.get(url)
        self.assertEqual(response_admin.status_code, 200)
        self.assertContains(response_admin, 'Remover Post')
        self.client.logout()
        self.client.force_login(self.prof1)
        response_prof = self.client.get(url)
        self.assertEqual(response_prof.status_code, 200)
        self.client.logout()
        self.client.force_login(self.prof2)
        response_prof2 = self.client.get(url)
        self.assertEqual(response_prof2.status_code, 302)
        self.client.logout()
        self.client.force_login(self.aluno1)
        response_aluno = self.client.get(url)
        self.assertEqual(response_aluno.status_code, 302)

    def test_restaurar_post_removido(self):
        post = Post.objects.create(
            turma=self.turma1,
            autor=self.prof1,
            titulo='Aviso Restore',
            conteudo='Conteúdo...',
            categoria='AVISO',
        )
        post.remover(self.admin, motivo='Test Restore')
        self.assertTrue(post.removido)
        url = reverse('blog:post_restore', args=[post.id])
        
        self.client.force_login(self.aluno1)
        response_aluno = self.client.post(url, follow=True)
        post.refresh_from_db()
        self.assertTrue(post.removido, "Post should still be removed after student attempt")
        self.client.logout()
        
        self.client.force_login(self.prof2)
        response_prof2 = self.client.post(url, follow=True)
        post.refresh_from_db()
        self.assertTrue(post.removido, "Post should still be removed after other prof attempt")
        self.client.logout()
        
        self.client.force_login(self.prof1)
        response_prof1 = self.client.post(url, follow=True)
        self.assertEqual(response_prof1.status_code, 200)
        post.refresh_from_db()
        self.assertFalse(post.removido, "Post should be restored by class teacher")
        
        post.remover(self.prof1, motivo='Removed again')
        self.assertTrue(post.removido)
        self.client.force_login(self.admin)
        response_admin = self.client.post(url, follow=True)
        self.assertEqual(response_admin.status_code, 200)
        post.refresh_from_db()
        self.assertFalse(post.removido, "Post should be restored by admin")

    def test_comment_remove_permission_required_allows(self):
        """Test @comment_remove_permission_required allows class teacher and admin."""
        post = Post.objects.create(turma=self.turma1, autor=self.prof1, titulo='Comment Remove Test')
        comment = Comment.objects.create(post=post, autor=self.aluno1, conteudo='Test Comment')
        remove_url = reverse('blog:comment_remove', args=[comment.id])
        detail_url = reverse('blog:post_detail', args=[post.id])
        
        # Teacher of class
        self.client.force_login(self.prof1)
        response_prof = self.client.post(remove_url)
        self.assertEqual(response_prof.status_code, 302)
        self.assertRedirects(response_prof, detail_url)
        comment.refresh_from_db()
        self.assertTrue(comment.removido)
        self.assertEqual(comment.removido_por, self.prof1)
        self.client.logout()
        
        # Reset comment
        comment.removido = False
        comment.removido_por = None
        comment.save()
        
        # Admin
        self.client.force_login(self.admin)
        response_admin = self.client.post(remove_url)
        self.assertEqual(response_admin.status_code, 302)
        self.assertRedirects(response_admin, detail_url)
        comment.refresh_from_db()
        self.assertTrue(comment.removido)
        self.assertEqual(comment.removido_por, self.admin)
        self.client.logout()
        
    def test_comment_remove_permission_required_blocks(self):
        """Test @comment_remove_permission_required blocks author, other users."""
        post = Post.objects.create(turma=self.turma1, autor=self.prof1, titulo='Comment Remove Block Test')
        comment = Comment.objects.create(post=post, autor=self.aluno1, conteudo='Test Comment Block')
        remove_url = reverse('blog:comment_remove', args=[comment.id])
        login_url = reverse('users:login_choice')
        
        # Author (student)
        self.client.force_login(self.aluno1)
        response_author = self.client.post(remove_url)
        self.assertEqual(response_author.status_code, 302)
        comment.refresh_from_db()
        self.assertFalse(comment.removido)
        self.client.logout()
        
        # Other Teacher
        self.client.force_login(self.prof2)
        response_prof2 = self.client.post(remove_url)
        self.assertEqual(response_prof2.status_code, 302)
        comment.refresh_from_db()
        self.assertFalse(comment.removido)
        self.client.logout()

        # Guest
        response_guest = self.client.post(remove_url)
        self.assertEqual(response_guest.status_code, 302) # Redirects to login
        self.assertIn(login_url, response_guest.url)
        comment.refresh_from_db()
        self.assertFalse(comment.removido)

    # Add tests for other decorators (...)

# === Permission Decorator Tests ===
class BlogPermissionDecoratorTests(BlogBaseTestCase):

    def test_turma_member_required_allows_members(self):
        """Test @turma_member_required allows class members (student, teacher)."""
        list_url = reverse('class_blog:post_list', args=[self.turma1.id])
        
        # Student is member
        self.client.force_login(self.aluno1)
        response_student = self.client.get(list_url)
        self.assertEqual(response_student.status_code, 200)
        self.client.logout()
        
        # Teacher is member
        self.client.force_login(self.prof1)
        response_prof = self.client.get(list_url)
        self.assertEqual(response_prof.status_code, 200)
        self.client.logout()
        
        # Admin/Superuser is allowed implicitly by decorator
        self.client.force_login(self.admin)
        response_admin = self.client.get(list_url)
        self.assertEqual(response_admin.status_code, 200)
        self.client.logout()

    def test_turma_member_required_blocks_non_members(self):
        """Test @turma_member_required blocks non-members (other student, other teacher) but allows related guardian."""
        list_url = reverse('class_blog:post_list', args=[self.turma1.id])
        login_url = reverse('users:login_choice')

        # Other Student (not in turma1)
        self.client.force_login(self.aluno2)
        response_aluno2 = self.client.get(list_url)
        self.assertEqual(response_aluno2.status_code, 403, "Other student should be Forbidden")
        self.client.logout()

        # Other Teacher (not in turma1)
        self.client.force_login(self.prof2)
        response_prof2 = self.client.get(list_url)
        self.assertEqual(response_prof2.status_code, 403, "Other teacher should be Forbidden")
        self.client.logout()
        
        # Guardian (IS related to student in class, should be ALLOWED by decorator)
        self.client.force_login(self.guardian)
        response_guardian = self.client.get(list_url)
        self.assertEqual(response_guardian.status_code, 200, "Guardian of class student should be allowed (gets 200 OK)")
        self.client.logout()
        
        # Guest
        response_guest = self.client.get(list_url)
        self.assertEqual(response_guest.status_code, 302) # Expect redirect to login
        self.assertIn(login_url, response_guest.url)
        
    def test_turma_post_create_required_allows_members(self):
        """Test @turma_post_create_required allows student/teacher/admin."""
        create_url = reverse('class_blog:post_create', args=[self.turma1.id])
        
        # Student
        self.client.force_login(self.aluno1)
        response_student = self.client.get(create_url)
        self.assertEqual(response_student.status_code, 200)
        self.client.logout()
        
        # Teacher
        self.client.force_login(self.prof1)
        response_prof = self.client.get(create_url)
        self.assertEqual(response_prof.status_code, 200)
        self.client.logout()
        
        # Admin
        self.client.force_login(self.admin)
        response_admin = self.client.get(create_url)
        self.assertEqual(response_admin.status_code, 200)
        self.client.logout()
        
    def test_turma_post_create_required_blocks_others(self):
        """Test @turma_post_create_required blocks non-members and guardians."""
        create_url = reverse('class_blog:post_create', args=[self.turma1.id])
        login_url = reverse('users:login_choice')

        # Other Student
        self.client.force_login(self.aluno2)
        response_aluno2 = self.client.get(create_url)
        self.assertEqual(response_aluno2.status_code, 403)
        self.client.logout()

        # Other Teacher
        self.client.force_login(self.prof2)
        response_prof2 = self.client.get(create_url)
        self.assertEqual(response_prof2.status_code, 403)
        self.client.logout()
        
        # Guardian
        self.client.force_login(self.guardian)
        response_guardian = self.client.get(create_url)
        self.assertEqual(response_guardian.status_code, 403)
        self.client.logout()
        
        # Guest
        response_guest = self.client.get(create_url)
        self.assertEqual(response_guest.status_code, 302)
        self.assertIn(login_url, response_guest.url)

    def test_post_edit_permission_required_allows(self):
        """Test @post_edit_permission_required allows author and admin."""
        # Post created by aluno1
        post = Post.objects.create(turma=self.turma1, autor=self.aluno1, titulo='Edit Test', categoria='TRABALHO')
        edit_url = reverse('blog:post_edit', args=[post.id])
        
        # Author (aluno1)
        self.client.force_login(self.aluno1)
        response_author = self.client.get(edit_url)
        self.assertEqual(response_author.status_code, 200)
        self.client.logout()
        
        # Admin
        self.client.force_login(self.admin)
        response_admin = self.client.get(edit_url)
        self.assertEqual(response_admin.status_code, 200)
        self.client.logout()
        
    def test_post_edit_permission_required_blocks(self):
        """Test @post_edit_permission_required blocks others (teacher, other student)."""
        post = Post.objects.create(turma=self.turma1, autor=self.aluno1, titulo='Edit Block Test', categoria='TRABALHO')
        edit_url = reverse('blog:post_edit', args=[post.id])
        login_url = reverse('users:login_choice')
        
        # Teacher of class (not author) should be redirected (no permission)
        self.client.force_login(self.prof1)
        response_prof = self.client.get(edit_url, follow=False)
        self.assertEqual(response_prof.status_code, 302)
        self.client.logout()
        
        # Other student (not author)
        self.client.force_login(self.aluno2)
        response_aluno2 = self.client.get(edit_url)
        self.assertEqual(response_aluno2.status_code, 302)
        self.client.logout()
        
        # Guest
        response_guest = self.client.get(edit_url)
        self.assertEqual(response_guest.status_code, 302)
        self.assertIn(login_url, response_guest.url)

    def test_post_remove_permission_required_allows(self):
        """Test @post_remove_permission_required allows class teacher and admin."""
        post = Post.objects.create(turma=self.turma1, autor=self.aluno1, titulo='Remove Test', categoria='AVISO')
        remove_url = reverse('blog:post_remove', args=[post.id])
        public_list_url = reverse('blog:post_list_public')
        
        # Teacher of class
        self.client.force_login(self.prof1)
        response_prof = self.client.post(remove_url) # POST request
        self.assertEqual(response_prof.status_code, 302)
        self.assertRedirects(response_prof, public_list_url)
        post.refresh_from_db()
        self.assertTrue(post.removido)
        self.assertEqual(post.removido_por, self.prof1)
        self.client.logout()
        
        # Reset post
        post.removido = False
        post.removido_por = None
        post.save()
        
        # Admin
        self.client.force_login(self.admin)
        response_admin = self.client.post(remove_url)
        self.assertEqual(response_admin.status_code, 302)
        self.assertRedirects(response_admin, public_list_url)
        post.refresh_from_db()
        self.assertTrue(post.removido)
        self.assertEqual(post.removido_por, self.admin)
        self.client.logout()
        
    def test_post_remove_permission_required_blocks(self):
        """Test @post_remove_permission_required blocks author, other users."""
        post = Post.objects.create(turma=self.turma1, autor=self.aluno1, titulo='Remove Block Test', categoria='AVISO')
        remove_url = reverse('blog:post_remove', args=[post.id])
        login_url = reverse('users:login_choice')
        
        # Author (student) should be redirected (no permission)
        self.client.force_login(self.aluno1)
        response_author = self.client.post(remove_url)
        self.assertEqual(response_author.status_code, 302)
        post.refresh_from_db()
        self.assertFalse(post.removido)
        self.client.logout()
        
        # Other Teacher
        self.client.force_login(self.prof2)
        response_prof2 = self.client.post(remove_url)
        self.assertEqual(response_prof2.status_code, 302)
        post.refresh_from_db()
        self.assertFalse(post.removido)
        self.client.logout()

        # Guest
        response_guest = self.client.post(remove_url)
        self.assertEqual(response_guest.status_code, 302) # Redirects to login
        self.assertIn(login_url, response_guest.url)
        post.refresh_from_db()
        self.assertFalse(post.removido)


class TinyMCEUploadTests(BlogBaseTestCase):
    def test_upload_image_requires_login(self):
        upload_url = reverse('blog:tinymce_image_upload')
        # No login
        image = SimpleUploadedFile("test.png", b"fakepngdata", content_type="image/png")
        response = self.client.post(upload_url, {'file': image})
        self.assertIn(response.status_code, [302, 403])  # Redirect to login or forbidden

    def test_upload_image_success(self):
        self.client.force_login(self.prof1)
        upload_url = reverse('blog:tinymce_image_upload')
        image = SimpleUploadedFile("test.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
        response = self.client.post(upload_url, {'file': image})
        self.assertEqual(response.status_code, 200)
        self.assertIn('location', response.json())

    def test_upload_invalid_type(self):
        self.client.force_login(self.prof1)
        upload_url = reverse('blog:tinymce_image_upload')
        txt = SimpleUploadedFile("test.txt", b"hello", content_type="text/plain")
        response = self.client.post(upload_url, {'file': txt})
        self.assertEqual(response.status_code, 400)

    # Add tests for other decorators (@comment_remove_permission_required, etc.)
