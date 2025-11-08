from collections import defaultdict


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import FormView
from django.views.decorators.cache import cache_page
from django.urls import reverse_lazy

from myapp.models import UserCourse, UserProgress, QuizResult, UserAnswer
from quizzes.models import Answer
from courses.models import UserLessonTrajectory
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
 


class RegisterView(FormView):
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)



@cache_page(60*15)
@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """
    Отображает страницу профиля пользователя, а также его прогресс
    по начатым курсам.

    Args:
        request (HttpRequest): Объект запроса.

    Returns:
        HttpResponse: Ответ с отрендеренным шаблоном профиля.
        Шаблон включает формы для редактирования профиля и список курсов с прогрессом.
    """
    user = request.user
    started_courses = UserCourse.objects.filter(user=user).select_related('course')
    unfinished_courses = []
    finished_courses = []
    exp = 0
    level = 1
    quiz_results = QuizResult.objects.filter(user=request.user).order_by('-completed_at')
    # Пагинация для истории тестов
    paginator = Paginator(quiz_results, 4)  # 4 элементов на странице
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

        # Проверка на AJAX-запрос
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'users/includes/_quiz_history.html', {'page_obj': page_obj})

    all_lessons_completed = False
    percent = 0 

    for user_course in started_courses:
        course = user_course.course
        completed = UserProgress.objects.filter(
            user=user,
            course=course,
            completed=True
        ).count()

        trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
        total = trajectory.lessons.count() if trajectory else course.lessons.count()
        percent = int((completed / total) * 100) if total > 0 else 0

        course_data = {
            'course': course,
            'completed': completed,
            'total': total,
            'percent': percent
        }

        if course.final_quiz:
            quiz_passed = QuizResult.objects.filter(
                user=request.user,
                quiz_title=course.final_quiz,
                passed=True
            ).exists()
            course_data['quiz_passed'] = quiz_passed

        if percent == 100:
            user_course_obj = UserCourse.objects.get(user=user, course=course)
            if user_course_obj.can_receive_exp():
                finished_courses.append(course_data)
                exp += user_course_obj.exp_reward()
            else:
                unfinished_courses.append(course_data)
                exp += 15
        else:
            unfinished_courses.append(course_data)
            exp += 15

        # Обновляем флаг завершения всех уроков
        all_lessons_completed = (percent == 100) or all_lessons_completed

    # Функция для расчета уровня и прогресса
    def count_exp(exp, level):
        while exp >= level * 100:
            level += 1
        progress = ((exp - ((level - 1) * 100)) / 100) * 100
        return level, min(progress, 100)

    level, progress = count_exp(exp, level)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'users/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'unfinished_courses': unfinished_courses,
        'finished_courses': finished_courses,
        'exp': exp,
        'progress': int(progress),
        'level': level,
        'quiz_results': quiz_results,
        'page_obj': page_obj,
        'all_lessons_completed': all_lessons_completed,
    })


@login_required
def quiz_report(request, quiz_id):
    quiz_result = get_object_or_404(QuizResult, id=quiz_id, user=request.user)
    answers = quiz_result.answers.select_related('question', 'selected_answer').all()

    # Создаем словарь, где ключ - вопрос, значение - список выбранных ответов
    multiple_choice_answers = {}

    for answer in answers:
        if answer.question.question_type == 'multiple':
            # Если вопрос еще не в словаре, добавляем с пустым списком
            if answer.question not in multiple_choice_answers:
                multiple_choice_answers[answer.question] = []
            # Добавляем выбранный ответ (если он есть)
            if answer.selected_answer:
                multiple_choice_answers[answer.question].append(answer.selected_answer)

    context = {
        'quiz_result': quiz_result,
        'answers': answers,
        'multiple_choice_answers': multiple_choice_answers,
    }
    return render(request, 'users/includes/_quiz_report.html', context)


class CustomLoginView(LoginView):
    """
    Кастомный класс расширяющий функционал встроенной в Django функции авторизации.
    Если пользователь зарегистрирован, но администратор сайта не поставил ему в админ панеле галочку - подтверждение,
    то пользователю, при попытке входа, будет выводится сообщение "Ваш аккаунт ожидает подтверждения администратором."
    """
    template_name = "users/login.html"

    def form_valid(self, form):
        user = form.get_user()
        if not user.profile.is_approved:
            messages.error(self.request, "Ваш аккаунт ожидает подтверждения администратором.")
            return redirect('login')
        auth_login(self.request, user)
        return redirect(self.get_success_url())