from django.contrib import admin
from .models import UserCourse, QuizResult, UserAnswer

@admin.register(UserCourse)
class UserCourseAdmin(admin.ModelAdmin):
    fields = ['user', 'course', 'end_date', 'is_completed']
    readonly_fields = ['end_date']
    list_display = ('user', 'course',)
    list_filter = ('course',)
    search_fields = ('user__username', 'course__title')

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    fields = ['user', 'quiz_result', 'question', 'selected_answer', 'is_correct']
    readonly_fields = ['user', 'quiz_result', 'question', 'selected_answer', 'is_correct']


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    fields = ['user', 'quiz_title', 'score', 'total_questions', 'percent', 'completed_at', 'passed']
    readonly_fields = ['user', 'quiz_title', 'score', 'total_questions', 'percent', 'completed_at', 'passed']

