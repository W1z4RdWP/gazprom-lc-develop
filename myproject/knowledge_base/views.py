from django.shortcuts import render
from django.views.generic import TemplateView



class KbHome(TemplateView):
    template_name = 'knowledge_base/kb_home.html'
