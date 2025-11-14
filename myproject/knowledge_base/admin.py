from django.contrib import admin
from .models import Directory


@admin.register(Directory)
class DirectoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'order', 'description']
    list_filter = ['parent']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']
    autocomplete_fields = ['parent']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'parent', 'order', 'description')
        }),
    )
