from django.contrib import admin

from demo.models import DemoBatch, DemoRecord


class DemoRecordInline(admin.TabularInline):
    model = DemoRecord
    extra = 0
    readonly_fields = ('content_type', 'object_id', 'label', 'created_at')


@admin.register(DemoBatch)
class DemoBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'created_at', 'record_count')
    search_fields = ('description', 'id')
    inlines = [DemoRecordInline]

    def record_count(self, obj):  # pragma: no cover
        return obj.records.count()


@admin.register(DemoRecord)
class DemoRecordAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'object_id', 'batch', 'label', 'created_at')
    list_filter = ('content_type', 'batch')
    search_fields = ('object_id', 'label')
    readonly_fields = ('batch', 'content_type', 'object_id', 'label', 'created_at')
