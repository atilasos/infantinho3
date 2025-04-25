from django.test import TestCase
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from .models import ChecklistTemplate, ChecklistItem, ChecklistStatus, ChecklistMark
from classes.models import Class
from unittest.mock import patch

User = get_user_model()

class ChecklistMVPTests(TestCase):
    def setUp(self):
        # Criar users
        self.admin = User.objects.create_user(username='admin', email='admin@escola.pt', password='admin', role='admin', status='ativo')
        self.prof = User.objects.create_user(username='prof', email='prof@escola.pt', password='prof', role='professor', status='ativo')
        self.aluno = User.objects.create_user(username='aluno', email='aluno@escola.pt', password='aluno', role='aluno', status='ativo')
        # Criar turma
        self.turma = Class.objects.create(name='5A', year=2025)
        self.turma.teachers.add(self.prof)
        self.turma.students.add(self.aluno)
        # Criar template e itens
        self.template = ChecklistTemplate.objects.create(nome='Português 5.º ano', ano='5.º ano', disciplina='Português')
        self.item1 = ChecklistItem.objects.create(template=self.template, descricao='Ler textos', ordem=1)
        self.item2 = ChecklistItem.objects.create(template=self.template, descricao='Escrever textos', ordem=2, contratualizado_em_conselho=True)
        # Criar status
        self.status = ChecklistStatus.objects.create(template=self.template, aluno=self.aluno, classe=self.turma)

    def test_criacao_e_edicao_templates_itens_status(self):
        self.assertEqual(ChecklistTemplate.objects.count(), 1)
        self.assertEqual(ChecklistItem.objects.count(), 2)
        self.assertEqual(ChecklistStatus.objects.count(), 1)
        # Editar item
        self.item1.descricao = 'Ler textos narrativos'
        self.item1.save()
        self.assertEqual(ChecklistItem.objects.get(id=self.item1.id).descricao, 'Ler textos narrativos')

    def test_fluxo_marcacao_e_validacao(self):
        self.client.force_login(self.aluno)
        url = reverse('checklists:checklist_detail', args=[self.template.id])
        # Marcar item1 como concluído
        resp = self.client.post(url, {'item_id': self.item1.id, 'estado': 'concluido', 'comentario': 'Terminei'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        mark = ChecklistMark.objects.filter(item=self.item1, status=self.status).latest('criado_em')
        self.assertEqual(mark.estado, 'concluido')
        self.assertEqual(mark.comentario, 'Terminei')
        self.assertFalse(mark.validacao_professor)
        # Professor valida
        self.client.force_login(self.prof)
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        resp2 = self.client.post(turma_url, {'aluno_id': self.aluno.id, 'item_id': self.item1.id, 'estado': 'concluido', 'comentario': 'Validado'}, follow=True)
        self.assertEqual(resp2.status_code, 200)
        mark2 = ChecklistMark.objects.filter(item=self.item1, status=self.status, validacao_professor=True).latest('criado_em')
        self.assertEqual(mark2.comentario, 'Validado')
        self.assertEqual(mark2.estado, 'concluido')

    def test_permissoes_aluno_so_altera_proprio_status(self):
        outro = User.objects.create_user(username='outro', email='outro@escola.pt', password='outro', role='aluno', status='ativo')
        self.client.force_login(outro)
        url = reverse('checklists:checklist_detail', args=[self.template.id])
        resp = self.client.post(url, {'item_id': self.item1.id, 'estado': 'concluido', 'comentario': 'Fake'}, follow=True)
        # Não deve conseguir criar marcação para status de outro aluno
        self.assertNotIn('Objetivo atualizado com sucesso!', resp.content.decode())
        self.assertEqual(ChecklistMark.objects.filter(item=self.item1, comentario='Fake').count(), 0)

    def test_permissoes_professor_so_valida_na_turma(self):
        outro_prof = User.objects.create_user(username='prof2', email='prof2@escola.pt', password='prof2', role='professor', status='ativo')
        self.client.force_login(outro_prof)
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        resp = self.client.post(turma_url, {'aluno_id': self.aluno.id, 'item_id': self.item1.id, 'estado': 'concluido', 'comentario': 'Fake'}, follow=True)
        # Não deve conseguir validar se não for professor da turma
        self.assertNotIn('validada/retificada', resp.content.decode())
        self.assertEqual(ChecklistMark.objects.filter(item=self.item1, comentario='Fake').count(), 0)

    @patch('checklists.views.send_mail')
    def test_notificacao_professor_e_aluno(self, mock_send_mail):
        # Aluno marca item -> professores notificados
        self.client.force_login(self.aluno)
        url = reverse('checklists:checklist_detail', args=[self.template.id])
        self.client.post(url, {'item_id': self.item1.id, 'estado': 'concluido', 'comentario': 'Terminei'}, follow=True)
        self.assertTrue(mock_send_mail.called)
        args, kwargs = mock_send_mail.call_args
        self.assertIn(self.prof.email, args[3])
        # Professor valida -> aluno notificado
        self.client.force_login(self.prof)
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        self.client.post(turma_url, {'aluno_id': self.aluno.id, 'item_id': self.item1.id, 'estado': 'concluido', 'comentario': 'Validado'}, follow=True)
        self.assertTrue(mock_send_mail.called)
        args2, kwargs2 = mock_send_mail.call_args
        self.assertIn(self.aluno.email, args2[3])

    def test_seeds_scripts_nao_afetam_producao(self):
        # Simula ambiente de produção (não executa seeds)
        import os
        os.environ['DJANGO_SETTINGS_MODULE'] = 'infantinho3.settings'
        # Os scripts seed_checklists_5ano.py e 6ano.py só devem rodar se ambiente for dev/test
        # Aqui apenas garantimos que não há duplicação se rodar de novo
        from checklists.models import ChecklistTemplate
        n_templates = ChecklistTemplate.objects.count()
        # Simula rodar seed (deve abortar se já existe)
        from seed_checklists_5ano import main as seed5
        seed5()
        self.assertEqual(ChecklistTemplate.objects.count(), n_templates)
