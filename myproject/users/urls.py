from django.urls import path
from . import views as user_views
from django.contrib.auth import views as auth_views


app_name = 'users'

urlpatterns = [
    path('profile/', user_views.profile, name='profile'),
    path('login/', user_views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('user_management/', user_views.UserManagementView.as_view(), name='user_management'),
    path('user_management/register/', user_views.RegisterUserView.as_view(), name='register'),
    path('user_management/<int:pk>/', user_views.user_detail, name='user_detail'),
    path('user_management/<int:pk>/edit/', user_views.user_edit, name='user_edit'),
]
