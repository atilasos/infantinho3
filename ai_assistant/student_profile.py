"""
Student Profile System for AI Personalization

Implements ZDP (Zone of Proximal Development) tracking and 
socio-constructivist learning support for the MEM pedagogy.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import json
from typing import Dict, List, Optional


class StudentProfile(models.Model):
    """
    Learning profile for each student - used by AI to personalize support.
    Based on Vygotsky's ZDP and MEM socio-constructivism.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_profile'
    )
    
    # ZDP Tracking
    current_zdp_level = models.CharField(
        _('nível ZDP atual'),
        max_length=20,
        choices=[
            ('autonomo', _('Autónomo - trabalha sozinho')),
            ('apoio_minimo', _('Com apoio mínimo - pistas')),
            ('apoio_moderado', _('Com apoio moderado - exemplos')),
            ('apoio_intenso', _('Com apoio intenso - guiação')),
        ],
        default='apoio_minimo',
        help_text=_('Nível de apoio que o aluno precisa atualmente')
    )
    
    # Learning Preferences (detected over time)
    learns_best_with = models.JSONField(
        _('aprende melhor com'),
        default=dict,
        help_text=_('Preferências: exemplos, imagens, passo-a-passo, colegas, etc.')
    )
    
    # Collaboration tracking (MEM socio-constructivism)
    preferred_collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='collaborates_with',
        verbose_name=_('colegas preferidos para trabalho')
    )
    
    collaboration_success_rate = models.FloatField(
        _('taxa de sucesso em colaboração'),
        default=0.0,
        help_text=_('0-1, calculado automaticamente')
    )
    
    # Strengths and Growth Areas
    strengths = models.JSONField(
        _('pontos fortes'),
        default=list,
        help_text=_('Domínios onde o aluno é autónomo')
    )
    
    growth_areas = models.JSONField(
        _('áreas de crescimento'),
        default=list,
        help_text=_('Domínios que precisam de mais apoio')
    )
    
    # Interaction History with AI
    ai_interaction_count = models.PositiveIntegerField(
        _('número de interações com IA'),
        default=0
    )
    
    last_ai_topics = models.JSONField(
        _('últimos tópicos com IA'),
        default=list,
        help_text=_('Temas recentes para contexto')
    )
    
    # Autonomy Progress
    autonomy_progress = models.JSONField(
        _('progresso de autonomia'),
        default=dict,
        help_text=_('Por domínio: {dominio: {data: valor, ...}}')
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Perfil de Aprendizagem')
        verbose_name_plural = _('Perfis de Aprendizagem')
    
    def get_ai_context(self) -> str:
        """Generate context string for AI assistant."""
        context_parts = []
        
        # ZDP level
        zdp_map = {
            'autonomo': 'trabalha bem sozinho, dá-lhe desafios',
            'apoio_minimo': 'precisa de pistas e sugestões',
            'apoio_moderado': 'beneficia de exemplos e analogias',
            'apoio_intenso': 'precisa de guiação passo a passo',
        }
        context_parts.append(f"Nível de apoio: {zdp_map.get(self.current_zdp_level, 'padrão')}")
        
        # Collaboration
        if self.collaboration_success_rate > 0.6:
            context_parts.append("Trabalha bem com colegas - sugere colaboração")
        
        # Strengths
        if self.strengths:
            context_parts.append(f"Pontos fortes: {', '.join(self.strengths[:3])}")
        
        # Growth areas (be sensitive)
        if self.growth_areas:
            context_parts.append(f"Áreas a desenvolver: {', '.join(self.growth_areas[:2])}")
        
        # Recent topics
        if self.last_ai_topics:
            context_parts.append(f"Temas recentes: {', '.join(self.last_ai_topics[-3:])}")
        
        return " | ".join(context_parts)
    
    def update_from_interaction(self, topic: str, success: bool, 
                                help_level: str, used_collaboration: bool = False):
        """Update profile based on AI interaction."""
        self.ai_interaction_count += 1
        
        # Track topics
        self.last_ai_topics.append(topic)
        self.last_ai_topics = self.last_ai_topics[-10:]  # Keep last 10
        
        # Update ZDP based on success and help level
        if success and help_level == 'nivel_1':
            # Doing well with minimal help - might increase autonomy
            if self.current_zdp_level == 'apoio_intenso':
                self.current_zdp_level = 'apoio_moderado'
            elif self.current_zdp_level == 'apoio_moderado':
                self.current_zdp_level = 'apoio_minimo'
        elif not success and help_level == 'nivel_3':
            # Still struggling even with intensive help
            pass  # Keep current level
        
        # Track collaboration success
        if used_collaboration:
            # Update success rate with exponential moving average
            self.collaboration_success_rate = (
                0.7 * self.collaboration_success_rate + 0.3 * (1.0 if success else 0.0)
            )
        
        self.save()


class InteractionLog(models.Model):
    """
    Log of AI interactions for analysis and improvement.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_interactions'
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    question_topic = models.CharField(
        _('tema da pergunta'),
        max_length=200
    )
    
    help_level_used = models.CharField(
        _('nível de apoio usado'),
        max_length=20,
        choices=[
            ('nivel_1', _('Nível 1 - Pista/estratégia')),
            ('nivel_2', _('Nível 2 - Exemplo análogo')),
            ('nivel_3', _('Nível 3 - Resposta guiada')),
        ]
    )
    
    student_success = models.BooleanField(
        _('aluno conseguiu'),
        default=False
    )
    
    used_collaboration = models.BooleanField(
        _('usou colaboração'),
        default=False
    )
    
    conversation_excerpt = models.TextField(
        _('excerto da conversa'),
        blank=True
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Log de Interação')
        verbose_name_plural = _('Logs de Interações')


def get_or_create_student_profile(user) -> StudentProfile:
    """Get or create profile for a user."""
    profile, created = StudentProfile.objects.get_or_create(user=user)
    return profile


def get_personalized_system_prompt(user, base_prompt: str) -> str:
    """
    Enhance base prompt with student-specific context.
    """
    try:
        profile = user.learning_profile
        context = profile.get_ai_context()
        
        return f"""{base_prompt}

PERFIL DO ALUNO (para personalização):
{context}

ADAPTA A TUA RESPOSTA:
- Usa o nível de apoio adequado ao perfil
- Sugere colegas para colaboração quando apropriado
- Reforça pontos fortes, apoia áreas de crescimento
- Conecta com temas recentes se relevante
"""
    except StudentProfile.DoesNotExist:
        return base_prompt
