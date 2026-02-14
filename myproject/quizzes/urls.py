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
    path('<int:quiz_id>/empty-warning/', views.quiz_empty_warning, name='quiz_empty_warning'),

    # API для управления вопросами и ответами (AJAX)
    path('<int:quiz_id>/api/question/add/', views.api_add_question, name='api_add_question'),
    path('<int:quiz_id>/api/question/<int:question_id>/update/', views.api_update_question, name='api_update_question'),
    path('<int:quiz_id>/api/question/<int:question_id>/delete/', views.api_delete_question, name='api_delete_question'),
    path('<int:quiz_id>/api/question/<int:question_id>/answer/add/', views.api_add_answer, name='api_add_answer'),
    path('<int:quiz_id>/api/answer/<int:answer_id>/update/', views.api_update_answer, name='api_update_answer'),
    path('<int:quiz_id>/api/answer/<int:answer_id>/delete/', views.api_delete_answer, name='api_delete_answer'),
]