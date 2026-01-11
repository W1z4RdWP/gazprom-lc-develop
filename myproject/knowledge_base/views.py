from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import models
import json
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
            
            # Уроки в текущей папке (все уроки, независимо от привязки к курсу)
            standalone_lessons = Lesson.objects.filter(
                directory=current_directory
            ).order_by('order', 'title')
        else:
            # Корневая папка - показываем корневые категории, курсы и тесты без категории
            subdirectories = Directory.objects.filter(parent__isnull=True).order_by('order', 'name')
            
            # Курсы без категории (directory=None)
            courses = Course.objects.filter(directory__isnull=True).select_related('author', 'final_quiz').order_by('title')
            
            # Тесты без категории (directory=None)
            quizzes = Quiz.objects.filter(directory__isnull=True).order_by('name')
            
            # Уроки без категории (все уроки, независимо от привязки к курсу)
            standalone_lessons = Lesson.objects.filter(
                directory__isnull=True
            ).order_by('order', 'title')
        
        # Уроки и тесты для каждого курса (общая логика для всех курсов)
        courses_with_lessons = []
        for course in courses:
            lessons = Lesson.objects.filter(courses=course).order_by('order')
            quizzes_count = course.quizzes.count()
            courses_with_lessons.append({
                'course': course,
                'lessons': lessons,
                'lessons_count': lessons.count(),
                'quizzes_count': quizzes_count
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




@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def edit_directory_name(request, directory_id):
    """AJAX представление для inline редактирования названия категории"""
    directory = get_object_or_404(Directory, id=directory_id)
    
    try:
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()
        
        if not new_name:
            return JsonResponse({'success': False, 'error': 'Название не может быть пустым'}, status=400)
        
        if len(new_name) > 255:
            return JsonResponse({'success': False, 'error': 'Название слишком длинное (максимум 255 символов)'}, status=400)
        
        directory.name = new_name
        directory.save()
        
        return JsonResponse({'success': True, 'name': directory.name})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат данных'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def delete_directory(request, directory_id):
    """AJAX представление для удаления категории"""
    directory = get_object_or_404(Directory, id=directory_id)
    
    try:
        data = json.loads(request.body) if request.body else {}
        action = data.get('action', 'check')  # check, move_to_root, delete_all
        
        # Проверяем, есть ли вложенные элементы
        has_subdirectories = Directory.objects.filter(parent=directory).exists()
        has_courses = Course.objects.filter(directory=directory).exists()
        has_lessons = Lesson.objects.filter(directory=directory).exists()
        has_quizzes = Quiz.objects.filter(directory=directory).exists()
        
        has_content = has_subdirectories or has_courses or has_lessons or has_quizzes
        
        # Если просто проверка - возвращаем информацию о содержимом
        if action == 'check':
            return JsonResponse({
                'success': True,
                'has_content': has_content,
                'has_subdirectories': has_subdirectories,
                'has_courses': has_courses,
                'has_lessons': has_lessons,
                'has_quizzes': has_quizzes
            })
        
        directory_name = directory.name
        
        if action == 'move_to_root':
            # Перемещаем всё содержимое в корень
            Directory.objects.filter(parent=directory).update(parent=None)
            Course.objects.filter(directory=directory).update(directory=None)
            Lesson.objects.filter(directory=directory).update(directory=None)
            Quiz.objects.filter(directory=directory).update(directory=None)
            
            # Удаляем саму категорию
            directory.delete()
            
            return JsonResponse({
                'success': True, 
                'message': f'Категория "{directory_name}" удалена. Содержимое перемещено в корень.'
            })
        
        elif action == 'delete_all':
            # Рекурсивная функция для удаления всего содержимого
            def delete_directory_recursive(dir_obj):
                # Сначала удаляем все вложенные директории рекурсивно
                for subdir in Directory.objects.filter(parent=dir_obj):
                    delete_directory_recursive(subdir)
                
                # Удаляем курсы в этой директории (и связанные с ними уроки через курс)
                Course.objects.filter(directory=dir_obj).delete()
                
                # Удаляем уроки в этой директории
                Lesson.objects.filter(directory=dir_obj).delete()
                
                # Удаляем тесты в этой директории
                Quiz.objects.filter(directory=dir_obj).delete()
                
                # Удаляем саму директорию
                dir_obj.delete()
            
            delete_directory_recursive(directory)
            
            return JsonResponse({
                'success': True, 
                'message': f'Категория "{directory_name}" и всё её содержимое удалены безвозвратно.'
            })
        
        else:
            return JsonResponse({'success': False, 'error': 'Неизвестное действие'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат данных'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def create_directory(request):
    """AJAX представление для inline создания категории"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        parent_id = data.get('parent_id')
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Название не может быть пустым'}, status=400)
        
        if len(name) > 255:
            return JsonResponse({'success': False, 'error': 'Название слишком длинное (максимум 255 символов)'}, status=400)
        
        # Получаем родительскую директорию (если указана)
        parent = None
        if parent_id:
            parent = get_object_or_404(Directory, id=parent_id)
        
        # Определяем порядок для новой директории
        if parent:
            max_order = Directory.objects.filter(parent=parent).aggregate(max_order=models.Max('order'))['max_order']
        else:
            max_order = Directory.objects.filter(parent__isnull=True).aggregate(max_order=models.Max('order'))['max_order']
        
        new_order = (max_order or 0) + 1
        
        # Создаём новую директорию
        directory = Directory.objects.create(
            name=name,
            parent=parent,
            order=new_order
        )
        
        return JsonResponse({
            'success': True,
            'id': directory.id,
            'name': directory.name
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат данных'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
