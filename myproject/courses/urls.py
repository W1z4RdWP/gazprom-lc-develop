from django.urls import path
from . import views as course_views

app_name = 'courses'

urlpatterns = [
    path('create_course/', course_views.CreateCourseView.as_view(), name='create_course'),
    path('create_lesson/', course_views.CreateLessonView.as_view(), name='create_lesson'),
    path('course/<slug:slug>/', course_views.CourseDetailView.as_view(), name='course_detail'),
    path('courses_list/', course_views.CourseListView.as_view(), name='course_detail_all'),
    path('lesson/<int:lesson_id>/', course_views.lesson_detail, name='lesson_detail_standalone'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/', course_views.lesson_detail, name='lesson_detail'),
    path('course/<slug:course_slug>/create-lesson/', course_views.CreateLessonView.as_view(), name='create_lesson_for_course'),
    path('course/<slug:slug>/delete/', course_views.delete_course, name='delete_course'),
    path('course/<int:user_id>/<slug:slug>/cancel_assignment/', course_views.cancel_course_assignment, name='cancel_course_assignment'),
    path('lesson/<int:lesson_id>/delete/', course_views.delete_lesson, name='delete_lesson'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/complete/', course_views.complete_lesson, name='complete_lesson'),
    path('course/<slug:slug>/edit/', course_views.edit_course, name='edit_course'),
    path('lesson/<int:lesson_id>/edit/', course_views.edit_lesson, name='edit_lesson'),
    path('course/<slug:course_slug>/redir_to_quiz/', course_views.redir_to_quiz, name='redir_to_quiz'),
    path('course/<slug:course_slug>/available-lessons/', course_views.get_available_lessons, name='get_available_lessons'),
    path('course/<slug:course_slug>/add-lesson/', course_views.add_lesson_to_course, name='add_lesson_to_course'),
    path('course/<slug:course_slug>/available-quizzes/', course_views.get_available_quizzes, name='get_available_quizzes'),
    path('course/<slug:course_slug>/add-quiz/', course_views.add_quiz_to_course, name='add_quiz_to_course'),
    path('attachment/<int:attachment_id>/delete/', course_views.delete_attachment, name='delete_attachment'),
]
