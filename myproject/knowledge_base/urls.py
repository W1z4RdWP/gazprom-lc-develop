from django.urls import path
from . import views as kb_views

app_name = 'knowledge_base'

urlpatterns = [
    path('', kb_views.KbHome.as_view(), name='kb_home'),
    path('directory/<int:directory_id>/', kb_views.KbHome.as_view(), name='kb_directory'),
]
