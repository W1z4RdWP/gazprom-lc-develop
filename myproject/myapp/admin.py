from django.contrib import admin
from .models import UserCourse, QuizResult, UserAnswer

admin.site.site_header = "Kupryazha"
admin.site.site_title = "Администрирование сайта"
admin.site.index_title = "Панель управления"

@admin.register(UserCourse)
class UserCourseAdmin(admin.ModelAdmin):
    list_display = ('user', 'course',)
    list_filter = ('course',)
    search_fields = ('user__username', 'course__title')

admin.site.register(QuizResult)
admin.site.register(UserAnswer)