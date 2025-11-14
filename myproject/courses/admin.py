from django.contrib import admin
from django import forms
from .models import Course, Lesson, UserLessonTrajectory

class LessonInlineForm(forms.ModelForm):
    class Meta:
        model = UserLessonTrajectory.lessons.through
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and hasattr(self.instance, 'userlessontrajectory'):
            trajectory = self.instance.userlessontrajectory
            self.fields['lesson'].queryset = Lesson.objects.filter(course=trajectory.course)

class LessonInline(admin.TabularInline):
    model = UserLessonTrajectory.lessons.through
    form = LessonInlineForm
    extra = 1
    verbose_name = "Урок в траектории"
    verbose_name_plural = "Уроки в траектории"
    autocomplete_fields = ['lesson']

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            formset.form.base_fields['lesson'].queryset = Lesson.objects.filter(course=obj.course)
        return formset

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'directory', 'author', 'image', 'slug', 'final_quiz']
    list_filter = ['directory', 'author']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['final_quiz', 'directory']  # Для удобного поиска тестов и категорий



@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'course']
    list_filter = ['course']
    search_fields = ['title', 'course__title']


@admin.register(UserLessonTrajectory)
class UserLessonTrajectoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'get_lessons_count')
    list_filter = ('course', 'user')
    search_fields = ('user__username', 'course__title')
    inlines = [LessonInline]
    exclude = ('lessons',)
    autocomplete_fields = ['course', 'lessons']

    def get_lessons_count(self, obj):
        return obj.lessons.count()
    get_lessons_count.short_description = 'Кол-во уроков'





# from django.contrib import admin
# from django import forms
# from .models import Course, Lesson, UserLessonTrajectory
# from .forms import UserLessonTrajectoryForm




# class LessonInline(admin.TabularInline):
#     model = UserLessonTrajectory.lessons.through
#     extra = 1
#     verbose_name = "Урок в траектории"
#     verbose_name_plural = "Уроки в траектории"

# @admin.register(UserLessonTrajectory)
# class UserLessonTrajectoryAdmin(admin.ModelAdmin):
#     form = UserLessonTrajectoryForm
#     list_display = ('user', 'course')
#     list_filter = ('course', 'user')
#     search_fields = ('user__username', 'course__title')
#     inlines = [LessonInline]
#     exclude = ('lessons',)
    
#     def get_lessons_count(self, obj):
#         return obj.lessons.count()
#     get_lessons_count.short_description = 'Кол-во уроков'