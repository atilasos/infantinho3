from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Conversation, Message, AIConfig


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'class_instance', 'created_at', 'updated_at', 'message_count']
    list_filter = ['created_at', 'class_instance']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user', 'class_instance']

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = _('Messages')


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['created_at']
    fields = ['role', 'content', 'tokens_used', 'created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'role', 'content_preview', 'created_at', 'tokens_used']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'conversation__user__username']
    date_hierarchy = 'created_at'
    raw_id_fields = ['conversation']

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = _('Content')


@admin.register(AIConfig)
class AIConfigAdmin(admin.ModelAdmin):
    list_display = ['provider', 'model', 'max_tokens', 'temperature', 'is_active', 'updated_at']
    list_editable = ['is_active']
    fieldsets = (
        (_('Provider Settings'), {
            'fields': ('provider', 'model')
        }),
        (_('Generation Parameters'), {
            'fields': ('max_tokens', 'temperature')
        }),
        (_('System Configuration'), {
            'fields': ('system_prompt', 'is_active')
        }),
    )

    def has_add_permission(self, request):
        # Only allow one instance
        if AIConfig.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the singleton
        return False
