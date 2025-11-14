from django.contrib import admin
from django.db.models import Count
from .models import Quiz, Question, Answer
from nested_admin import NestedTabularInline, NestedModelAdmin


class AnswerInline(NestedTabularInline):
    model = Answer
    extra = 1

class QuestionInline(NestedTabularInline):
    model = Question
    extra = 1
    fields = ['text', 'question_type']  # Поле quiz скрыто, устанавливается автоматически
    inlines = [AnswerInline]  # Вложенные инлайны требуют django-nested-admin

@admin.register(Quiz)
class QuizAdmin(NestedModelAdmin):
    list_display = ['name', 'directory', 'question_count']
    list_filter = ['directory', 'name']
    search_fields = ['name']
    inlines = [QuestionInline]
    autocomplete_fields = ['directory']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(question_count=Count('question'))

    def question_count(self, obj):
        return obj.question_set.count()
    question_count.short_description = 'Вопросов'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'question_type']
    list_filter = ['quiz', 'question_type']
    search_fields = ['text']
    inlines = [AnswerInline]
    autocomplete_fields = ['quiz']  # Удобный поиск тестов

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'text', 'is_correct']
    list_filter = ['question', 'is_correct']
    search_fields = ['question__text', 'text']
    autocomplete_fields = ['question']  # Удобный поиск вопросов