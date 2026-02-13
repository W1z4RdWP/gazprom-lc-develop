from collections import defaultdict


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import FormView, TemplateView
from django.views.decorators.cache import cache_page
from django.urls import reverse_lazy

from myapp.models import UserCourse, UserProgress, QuizResult, UserAnswer
from quizzes.models import Answer
from courses.models import UserLessonTrajectory
from .forms import UserUpdateForm, ProfileUpdateForm, UserRegistrationForm
 



# @cache_page(60*15)
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
        
        # Получаем траекторию для подсчета уроков
        trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
        
        # Подсчет завершенных уроков
        if trajectory:
            lesson_ids = trajectory.lessons.values_list('id', flat=True)
            completed_lessons = UserProgress.objects.filter(
                user=user,
                course=course,
                completed=True,
                lesson_id__in=lesson_ids
            ).count()
            total_lessons = trajectory.lessons.count()
        else:
            lesson_ids = course.lessons.values_list('id', flat=True)
            completed_lessons = UserProgress.objects.filter(
                user=user,
                course=course,
                completed=True,
                lesson_id__in=lesson_ids
            ).count()
            total_lessons = course.lessons.count()

        # Подсчет пройденных тестов курса
        course_quizzes = course.quizzes.all()
        total_quizzes = course_quizzes.count()
        completed_quizzes = 0
        
        for quiz in course_quizzes:
            quiz_passed = QuizResult.objects.filter(
                user=request.user,
                quiz_title=quiz.name,
                passed=True
            ).exists()
            if quiz_passed:
                completed_quizzes += 1

        # Расчет прогресса с учетом уроков и тестов
        total_items = total_lessons + total_quizzes
        completed_items = completed_lessons + completed_quizzes
        percent = int((completed_items / total_items) * 100) if total_items > 0 else 0

        course_data = {
            'course': course,
            'completed': completed_lessons,
            'total': total_lessons,
            'completed_quizzes': completed_quizzes,
            'total_quizzes': total_quizzes,
            'percent': percent
        }

        # Проверка финального теста
        if course.final_quiz:
            quiz_passed = QuizResult.objects.filter(
                user=request.user,
                quiz_title=course.final_quiz.name,
                passed=True
            ).exists()
            course_data['quiz_passed'] = quiz_passed

        # Курс считается завершенным только если все уроки, все тесты и финальный тест (если есть) пройдены
        all_items_completed = (completed_lessons >= total_lessons and 
                              completed_quizzes >= total_quizzes)
        final_quiz_passed = course_data.get('quiz_passed', True) if course.final_quiz else True
        is_course_completed = all_items_completed and final_quiz_passed

        if is_course_completed:
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
        # Создаем копию POST данных и гарантируем, что username всегда установлен
        post_data = request.POST.copy()
        if 'username' not in post_data or not post_data['username']:
            post_data['username'] = request.user.username
        
        user_form = UserUpdateForm(post_data, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    # Показывать форму редактирования, если есть ошибки валидации
    show_edit_form = request.method == 'POST' and (user_form.errors or profile_form.errors)
    
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
        'show_edit_form': show_edit_form,
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




def _get_user_learning_stats(target_user):
    """Собирает статистику обучения пользователя: курсы, опыт, уровень, тесты."""
    started_courses = UserCourse.objects.filter(user=target_user).select_related('course')
    unfinished_courses = []
    finished_courses = []
    exp = 0
    level = 1

    for user_course in started_courses:
        course = user_course.course
        trajectory = UserLessonTrajectory.objects.filter(user=target_user, course=course).first()

        if trajectory:
            lesson_ids = trajectory.lessons.values_list('id', flat=True)
            completed_lessons = UserProgress.objects.filter(
                user=target_user,
                course=course,
                completed=True,
                lesson_id__in=lesson_ids
            ).count()
            total_lessons = trajectory.lessons.count()
        else:
            lesson_ids = course.lessons.values_list('id', flat=True)
            completed_lessons = UserProgress.objects.filter(
                user=target_user,
                course=course,
                completed=True,
                lesson_id__in=lesson_ids
            ).count()
            total_lessons = course.lessons.count()

        course_quizzes = course.quizzes.all()
        total_quizzes = course_quizzes.count()
        completed_quizzes = sum(
            1 for q in course_quizzes
            if QuizResult.objects.filter(user=target_user, quiz_title=q.name, passed=True).exists()
        )
        total_items = total_lessons + total_quizzes
        completed_items = completed_lessons + completed_quizzes
        percent = int((completed_items / total_items) * 100) if total_items > 0 else 0

        course_data = {
            'course': course,
            'completed': completed_lessons,
            'total': total_lessons,
            'completed_quizzes': completed_quizzes,
            'total_quizzes': total_quizzes,
            'percent': percent,
        }
        if course.final_quiz:
            course_data['quiz_passed'] = QuizResult.objects.filter(
                user=target_user,
                quiz_title=course.final_quiz.name,
                passed=True
            ).exists()
        else:
            course_data['quiz_passed'] = True

        all_done = completed_lessons >= total_lessons and completed_quizzes >= total_quizzes
        is_course_completed = all_done and course_data.get('quiz_passed', True)

        if is_course_completed:
            if user_course.can_receive_exp():
                finished_courses.append(course_data)
                exp += user_course.exp_reward()
            else:
                unfinished_courses.append(course_data)
                exp += 15
        else:
            unfinished_courses.append(course_data)
            exp += 15

    while exp >= level * 100:
        level += 1
    progress = ((exp - ((level - 1) * 100)) / 100) * 100
    progress = min(progress, 100)

    quiz_results = QuizResult.objects.filter(user=target_user).order_by('-completed_at')[:10]
    return {
        'unfinished_courses': unfinished_courses,
        'finished_courses': finished_courses,
        'exp': exp,
        'level': level,
        'progress': int(progress),
        'quiz_results': quiz_results,
    }


@login_required
def user_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Детальный просмотр пользователя и статистики обучения (только для staff)."""
    if not request.user.is_staff:
        return redirect('home')
    profile_user = get_object_or_404(User, pk=pk)
    stats = _get_user_learning_stats(profile_user)
    context = {
        'profile_user': profile_user,
        **stats,
    }
    return render(request, 'users/user_detail.html', context)


class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'users/user_management.html'

    def test_func(self):
        """Проверка прав доступа - только для администраторов"""
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        return context


class RegisterUserView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Регистрация нового пользователя (только для staff)."""
    template_name = 'users/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('users:user_management')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        user = form.save(commit=False)
        user.email = form.cleaned_data['email']
        user.first_name = form.cleaned_data.get('first_name', '')
        user.last_name = form.cleaned_data.get('last_name', '')
        user.save()
        group = form.cleaned_data.get('group')
        if group:
            user.groups.add(group)
        messages.success(self.request, f'Пользователь «{user.username}» успешно создан.')
        return super().form_valid(form)


class CustomLoginView(LoginView):
    template_name = "users/login.html"


    def form_valid(self, form):
        user = form.get_user()
        auth_login(self.request, user)
        return redirect(self.get_success_url())