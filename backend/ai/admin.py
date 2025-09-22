from django.contrib import admin

from ai.models import (
    AIInteractionSession,
    AIRequest,
    AIResponseLog,
    AIUsageQuota,
    LearnerContextSnapshot,
    TeacherFocusArea,
)


@admin.register(AIInteractionSession)
class AIInteractionSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "user", "persona", "origin_app", "last_interaction_at", "is_active")
    list_filter = ("persona", "origin_app", "is_active")
    search_fields = ("session_id", "user__username", "user__email", "context_descriptor")
    readonly_fields = ("session_id", "created_at", "last_interaction_at")


@admin.register(AIRequest)
class AIRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "origin_app",
        "intent_label",
        "resolved_model",
        "status",
        "cost_estimate",
        "created_at",
    )
    list_filter = ("origin_app", "persona", "status", "resolved_model")
    search_fields = ("raw_query", "optimized_prompt", "user__username")
    readonly_fields = ("created_at", "completed_at", "optimizer_trace", "meta_context")


@admin.register(AIResponseLog)
class AIResponseLogAdmin(admin.ModelAdmin):
    list_display = ("request", "used_cache", "user_feedback", "created_at")
    list_filter = ("used_cache", "user_feedback")
    search_fields = ("response_text", "request__user__username")
    readonly_fields = ("created_at", "model_metadata", "guardrail_decision")


@admin.register(AIUsageQuota)
class AIUsageQuotaAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "class_context",
        "period_start",
        "requests_made",
        "max_requests",
        "cost_accumulated",
    )
    list_filter = ("scope", "period_start")
    search_fields = ("user__username", "class_context__name")


@admin.register(LearnerContextSnapshot)
class LearnerContextSnapshotAdmin(admin.ModelAdmin):
    list_display = ("student", "class_context", "source", "refreshed_at")
    list_filter = ("source",)
    search_fields = ("student__username", "class_context__name")
    readonly_fields = ("generated_at", "refreshed_at")


@admin.register(TeacherFocusArea)
class TeacherFocusAreaAdmin(admin.ModelAdmin):
    list_display = ("teacher", "class_context", "priority", "active", "created_at")
    list_filter = ("priority", "active")
    search_fields = ("teacher__username", "focus_text")
    readonly_fields = ("created_at",)
