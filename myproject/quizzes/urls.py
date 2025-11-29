from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('', views.StartQuizView.as_view(), name='quizzes'),
    path('create/', views.CreateQuizView.as_view(), name='create_quiz'),
    path('<int:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('start-quiz/', views.start_quiz_handler, name='quiz_start_handler'),
    path('start/<int:quiz_id>/', views.get_questions, {'is_start': True}, name='quiz_start'),
    path('get-questions/start', views.get_questions, {'is_start': True}, name='get-questions'),
    path('get-questions', views.get_questions, {'is_start': False}, name='get-questions'),
    path('get-answer', views.get_answer, name='get-answer'),
    path('get-finish', views.get_finish, name='get-finish'),
]