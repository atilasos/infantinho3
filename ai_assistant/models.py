from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class Conversation(models.Model):
    """
    Represents a conversation between a user and the AI assistant.
    Optionally linked to a specific class context.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        verbose_name=_('user')
    )
    class_instance = models.ForeignKey(
        'classes.Class',
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        verbose_name=_('class'),
        blank=True,
        null=True,
        help_text=_('Optional class context for this conversation.')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('Conversation')
        verbose_name_plural = _('Conversations')
        ordering = ['-updated_at']

    def __str__(self):
        class_info = f" - {self.class_instance.name}" if self.class_instance else ""
        return f"Conversation {self.id} - {self.user.get_full_name() or self.user.username}{class_info}"


class Message(models.Model):
    """
    Represents a single message within a conversation.
    """
    ROLE_CHOICES = [
        ('user', _('User')),
        ('assistant', _('Assistant')),
        ('system', _('System')),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('conversation')
    )
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='user'
    )
    content = models.TextField(
        _('content'),
        help_text=_('The message content.')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    tokens_used = models.IntegerField(
        _('tokens used'),
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text=_('Number of tokens used for this message (if tracked).')
    )

    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class AIConfig(models.Model):
    """
    Singleton model for AI assistant configuration.
    Only one instance should exist - stores global AI settings.
    """
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('google', 'Google'),
        ('anthropic', 'Anthropic'),
        ('local', 'Local/Custom'),
    ]

    # Singleton pattern - only one instance allowed
    id = models.AutoField(primary_key=True)

    provider = models.CharField(
        _('provider'),
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='openai',
        help_text=_('AI provider to use.')
    )
    model = models.CharField(
        _('model'),
        max_length=100,
        default='gpt-4o-mini',
        help_text=_('Model name (e.g., gpt-4o-mini, gemini-pro).')
    )
    max_tokens = models.IntegerField(
        _('max tokens'),
        default=2048,
        validators=[MinValueValidator(1), MaxValueValidator(8192)],
        help_text=_('Maximum tokens per response.')
    )
    temperature = models.FloatField(
        _('temperature'),
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
        help_text=_('Sampling temperature (0.0 = deterministic, 2.0 = very creative).')
    )
    system_prompt = models.TextField(
        _('system prompt'),
        blank=True,
        default='',
        help_text=_('Default system prompt for the AI assistant.')
    )
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether AI assistant is enabled.')
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('AI Configuration')
        verbose_name_plural = _('AI Configuration')

    def __str__(self):
        return f"AI Config: {self.provider} - {self.model}"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Get or create the singleton config instance."""
        config, created = cls.objects.get_or_create(pk=1)
        return config

    @classmethod
    def is_enabled(cls):
        """Check if AI assistant is enabled."""
        config = cls.get_config()
        return config.is_active
