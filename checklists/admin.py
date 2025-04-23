from django.contrib import admin
from .models import ChecklistTemplate, ChecklistItem, ChecklistStatus, ChecklistMark

# Register your models here.
admin.site.register(ChecklistTemplate)
admin.site.register(ChecklistItem)
admin.site.register(ChecklistStatus)
admin.site.register(ChecklistMark)
