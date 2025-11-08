from django.urls import path
from . import views as course_views

urlpatterns = [
    path('', course_views.course_detail, name='course-detail'),
    path('create-course/', course_views.create_course, name='create-course'),
    path('course/<slug:slug>/', course_views.course_detail, name='course_detail'),
    path('courses_list/', course_views.course_detail_all, name='course_detail_all'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/', course_views.lesson_detail, name='lesson_detail'),
    path('course/<slug:course_slug>/create-lesson/', course_views.create_lesson, name='create_lesson'),
    path('course/<slug:slug>/delete/', course_views.delete_course, name='delete_course'),
    path('lesson/<int:lesson_id>/delete/', course_views.delete_lesson, name='delete_lesson'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/complete/', course_views.complete_lesson, name='complete_lesson'),
    path('course/<slug:slug>/edit/', course_views.edit_course, name='edit_course'),
    path('lesson/<int:lesson_id>/edit/', course_views.edit_lesson, name='edit_lesson'),
    path('course/<slug:course_slug>/redir_to_quiz/', course_views.redir_to_quiz, name='redir_to_quiz')
]
