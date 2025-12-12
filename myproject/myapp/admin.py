from django.contrib import admin
from .models import UserCourse, QuizResult, UserAnswer

@admin.register(UserCourse)
class UserCourseAdmin(admin.ModelAdmin):
    fields = ['user', 'course', 'end_date', 'is_completed']
    readonly_fields = ['end_date']
    list_display = ('user', 'course',)
    list_filter = ('course',)
    search_fields = ('user__username', 'course__title')

admin.site.register(QuizResult)
admin.site.register(UserAnswer)