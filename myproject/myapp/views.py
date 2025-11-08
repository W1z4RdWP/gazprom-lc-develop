from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.views.generic import TemplateView
from .models import Course, UserCourse
from courses.models import Course as CourseModel

class IndexView(TemplateView):
    """Класс представление домашней страницы

        Attrs:
            template_name: имя файла для рендера
            get_context_data: функция передает контекст в шаблон 
    """
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_authenticated:
            # Получаем курсы, назначенные пользователю через UserCourse
            user_courses = UserCourse.objects.filter(user=user).values_list('course', flat=True)
            context['courses'] = CourseModel.objects.filter(id__in=user_courses)
        else:
            context['courses'] = []
            
        return context

class AboutView(TemplateView):
    """Класс представление страницы 'О нас' """
    template_name = 'about.html'

def is_admin(user) -> bool:
    return user.is_staff

def is_author_or_admin(user, course):
    return user.is_staff or user == course.author

def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)