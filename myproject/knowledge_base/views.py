from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from .models import Directory
from courses.models import Course, Lesson
from quizzes.models import Quiz


class KbHome(TemplateView):
    template_name = 'knowledge_base/kb_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем ID категории из URL (если есть)
        directory_id = self.kwargs.get('directory_id', None)
        
        if directory_id:
            # Открываем конкретную категорию
            current_directory = get_object_or_404(Directory, id=directory_id)
        else:
            # Корневая папка (показываем все корневые категории)
            current_directory = None
        
        # Получаем хлебные крошки (breadcrumbs)
        breadcrumbs = self._get_breadcrumbs(current_directory)
        
        # Получаем содержимое текущей папки
        if current_directory:
            # Подкатегории текущей папки
            subdirectories = Directory.objects.filter(parent=current_directory).order_by('order', 'name')
            
            # Курсы в текущей папке
            courses = Course.objects.filter(directory=current_directory).select_related('author', 'final_quiz').order_by('title')
            
            # Тесты в текущей папке
            quizzes = Quiz.objects.filter(directory=current_directory).order_by('name')
            
            # Уроки в текущей папке (не привязанные к курсам)
            standalone_lessons = Lesson.objects.filter(
                directory=current_directory,
                course__isnull=True
            ).order_by('order', 'title')
        else:
            # Корневая папка - показываем корневые категории, курсы и тесты без категории
            subdirectories = Directory.objects.filter(parent__isnull=True).order_by('order', 'name')
            
            # Курсы без категории (directory=None)
            courses = Course.objects.filter(directory__isnull=True).select_related('author', 'final_quiz').order_by('title')
            
            # Тесты без категории (directory=None)
            quizzes = Quiz.objects.filter(directory__isnull=True).order_by('name')
            
            # Уроки без категории и без курса
            standalone_lessons = Lesson.objects.filter(
                directory__isnull=True,
                course__isnull=True
            ).order_by('order', 'title')
        
        # Уроки для каждого курса (общая логика для всех курсов)
        courses_with_lessons = []
        for course in courses:
            lessons = Lesson.objects.filter(course=course).order_by('order')
            courses_with_lessons.append({
                'course': course,
                'lessons': lessons,
                'lessons_count': lessons.count()
            })
        
        context.update({
            'current_directory': current_directory,
            'subdirectories': subdirectories,
            'courses': courses_with_lessons,
            'quizzes': quizzes,
            'standalone_lessons': standalone_lessons,
            'breadcrumbs': breadcrumbs,
            'user': self.request.user,
        })
        
        return context
    
    def _get_breadcrumbs(self, directory):
        """Строит путь навигации (хлебные крошки) от корня до текущей папки"""
        breadcrumbs = []
        
        # Добавляем корневую папку
        breadcrumbs.append({
            'name': 'База знаний',
            'url': '/kb/',
            'is_root': True
        })
        
        # Если есть текущая папка, добавляем путь к ней
        if directory:
            path = []
            current = directory
            while current:
                path.insert(0, current)
                current = current.parent
            
            for dir_item in path:
                breadcrumbs.append({
                    'name': dir_item.name,
                    'url': f'/kb/directory/{dir_item.id}/',
                    'is_root': False
                })
        
        return breadcrumbs
