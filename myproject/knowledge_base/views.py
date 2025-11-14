from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Directory



class KbHome(TemplateView):
    template_name = 'knowledge_base/kb_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        
        # Корневые папки
        root_dirs = Directory.objects.filter(parent__isnull=True)

        context['directories'] = [dir.id for dir in root_dirs]

        return context
