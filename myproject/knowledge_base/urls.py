from django.urls import path
from . import views as kb_views

app_name = 'knowledge_base'

urlpatterns = [
    path('', kb_views.KbHome.as_view(), name='kb_home'),
    path('directory/<int:directory_id>/', kb_views.KbHome.as_view(), name='kb_directory'),
    path('directory/<int:directory_id>/edit-name/', kb_views.edit_directory_name, name='edit_directory_name'),
    path('directory/<int:directory_id>/delete/', kb_views.delete_directory, name='delete_directory'),
    path('directory/create/', kb_views.create_directory, name='create_directory'),
]
