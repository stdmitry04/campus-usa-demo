# server/essays/admin.py
from django.contrib import admin
from .models import Essay

@admin.register(Essay)
class EssayAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'essay_type', 'word_count', 'created_at']
    list_filter = ['essay_type', 'ai_generated']
    search_fields = ['title', 'user__username']