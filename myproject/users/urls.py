from django.urls import path
from . import views as user_views

app_name = 'users'

urlpatterns = [
    path('progress/', user_views.get_user_progress, name='user_progress'),
    path('profile/', user_views.profile, name='profile'),
    path('login/', user_views.CustomLoginView.as_view(), name='login'),
]
