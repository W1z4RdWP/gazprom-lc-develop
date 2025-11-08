from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from django.db import transaction
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from .forms import CourseForm, LessonForm
from .models import Course, Lesson, UserLessonTrajectory
from myapp.models import UserProgress, UserCourse, QuizResult
from myapp.views import is_admin, is_author_or_admin



def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    has_started = False
    user_course = None
    progress = 0
    completed_lessons = 0
    total_lessons = course.lessons.count()
    next_lesson = None
    all_completed = False
    completed_lessons_ids = None
    user_course = UserCourse.objects.get(user=request.user, course=course)
    exp_earned = user_course.exp_reward()
    course_author = course.author.username


    if request.user.is_authenticated:
        user_course = UserCourse.objects.filter(user=request.user, course=course).first()
        has_started = user_course is not None  # Упрощенная проверка

        if has_started:
            # Получаем траекторию пользователя, если она есть
            trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
            if trajectory:
                lessons = trajectory.lessons.all()
                total_lessons = lessons.count()  # Обновляем количество уроков, если есть траектория
                lesson_ids = lessons.values_list('id', flat=True)  # Получаем ID уроков в траектории

                completed_lessons = UserProgress.objects.filter(
                    user=request.user,
                    course=course,
                    completed=True,
                    lesson_id__in=lesson_ids  # Учитываем только уроки из траектории
                ).count()

                completed_lessons_ids = UserProgress.objects.filter(
                    user=request.user,
                    course=course,
                    completed=True,
                    lesson_id__in=lesson_ids  # Учитываем только уроки из траектории
                ).values_list('lesson_id', flat=True)

                max_completed_order = UserProgress.objects.filter(
                    user=request.user,
                    course=course,
                    completed=True,
                    lesson_id__in=lesson_ids  # Учитываем только уроки из траектории
                ).aggregate(max_order=Max('lesson__order'))['max_order'] or 0

                next_lesson = Lesson.objects.filter(
                    id__in=lesson_ids,  # Учитываем только уроки из траектории
                    order__gt=max_completed_order
                ).order_by('order').first()

                if not next_lesson:
                    next_lesson = lessons.first()  # Первый урок в траектории
            else:
                lessons = course.lessons.all()
                completed_lessons = UserProgress.objects.filter(
                    user=request.user,
                    course=course,
                    completed=True
                ).count()
                progress = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0

                completed_lessons_ids = UserProgress.objects.filter(
                    user=request.user,
                    course=course,
                    completed=True
                ).values_list('lesson_id', flat=True)

                max_completed_order = UserProgress.objects.filter(
                    user=request.user,
                    course=course,
                    completed=True
                ).aggregate(max_order=Max('lesson__order'))['max_order'] or 0

                next_lesson = Lesson.objects.filter(
                    course=course,
                    order__gt=max_completed_order
                ).order_by('order').first()

                if not next_lesson:
                    next_lesson = course.lessons.first()
            progress = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0

        if request.method == 'POST' and 'start_course' in request.POST:
            if not has_started:
                UserCourse.objects.create(user=request.user, course=course)
                return redirect('course_detail', slug=slug)
    else:
        return redirect('login')

    if trajectory:
        total_lessons = trajectory.lessons.count()
        lesson_ids = trajectory.lessons.values_list('id', flat=True)
    else:
        total_lessons = course.lessons.count()
        lesson_ids = course.lessons.values_list('id', flat=True)

    completed_lessons = UserProgress.objects.filter(
        user=request.user,
        course=course,
        completed=True,
        lesson_id__in=lesson_ids
    ).count()

    all_completed = completed_lessons >= total_lessons

    # Логика показа финального теста
    show_final_quiz = False
    if request.user.is_authenticated and has_started:
        # Если есть финальный тест
        if course.final_quiz:
            # Проверяем, завершил ли пользователь тестирование
            quiz_passed = QuizResult.objects.filter(
                user=request.user,
                quiz_title=course.final_quiz.name,  # Важно: используем name, а не объект
                passed=True
            ).exists()
            if quiz_passed:
                show_final_quiz = True
        else:
            # Если теста нет, показываем после завершения всех уроков
            if completed_lessons == total_lessons:
                show_final_quiz = True
    # Если не авторизован или не начал курс, show_final_quiz останется False

    # Получаем траекторию пользователя, если она есть
    trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
    

    # Обновляем флаг анимации
    if all_completed and user_course and not user_course.course_complete_animation_shown:
        with transaction.atomic():
            user_course.refresh_from_db()
            if not user_course.course_complete_animation_shown:
                user_course.end_date = timezone.now()
                user_course.is_completed = True
                user_course.course_complete_animation_shown = True
                user_course.save()
    if trajectory:
        lessons = trajectory.lessons.all()
    else:
         lessons = course.lessons.all()
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'course_author': course_author,
        'user_course': user_course,
        'has_started': has_started,
        'progress': progress,
        'completed_lessons': completed_lessons,
        'completed_lessons_ids': completed_lessons_ids,
        'total_lessons': total_lessons,
        'next_lesson': next_lesson,
        'all_completed': all_completed,
        'shown_animation': user_course.course_complete_animation_shown if user_course else False,
        'exp_earned': exp_earned,
        'lessons':lessons,
        'show_final_quiz':show_final_quiz,
    })


def course_detail_all(request):
    courses = []
    completed_courses = []

    if request.user.is_authenticated:
        # Получаем курсы, назначенные пользователю
        user_courses = UserCourse.objects.filter(user=request.user).values_list('course', flat=True)
        courses = Course.objects.filter(id__in=user_courses)
        # Получаем список завершенных курсов
        completed_courses = UserCourse.objects.filter(
            user=request.user, 
            is_completed=True
        ).values_list('course_id', flat=True)

    context = {
        'courses': courses,
        'completed_courses': completed_courses,
    }
    return render(request, 'courses/all_courses_list.html', context)


def lesson_detail(request, course_slug, lesson_id):
    if not request.user.is_authenticated:
        return redirect('login')

    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    # Проверка доступа к курсу
    user_course = UserCourse.objects.filter(user=request.user, course=course).first()
    if not user_course:
        return redirect('course_detail', slug=course.slug)

    # Проверка траектории
    trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
    if trajectory:
        lessons_in_trajectory = trajectory.lessons.all()
        if lesson not in lessons_in_trajectory:
            return redirect('course_detail', slug=course.slug)  # Или вы можете отобразить страницу с ошибкой

    # Помечаем урок как просмотренный (но не завершенный)
    UserProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'course': course}
    )
    return render(request, 'courses/lesson_detail.html', {'lesson': lesson})


@login_required
@user_passes_test(is_admin, login_url='/')
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.author = request.user
            course.save()
            return redirect('home')
    else:
        form = CourseForm()
    return render(request, 'courses/create_course.html', {'form': form})

@login_required
def create_lesson(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            return redirect('course_detail', course_slug)
    else:
        form = LessonForm()
    return render(request, 'courses/create_lesson.html', {'form': form, 'course': course})


@login_required
@user_passes_test(is_admin, login_url='/')
def delete_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == 'POST':
        course.delete()
        return redirect('home')
    return redirect('course_detail', slug=slug)


@login_required
@user_passes_test(is_admin, login_url='/')
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course_slug = lesson.course.slug
    if request.method == 'POST':
        lesson.delete()
    return redirect('course_detail', course_slug)


@login_required
@user_passes_test(lambda u: is_author_or_admin(u, Course), login_url='/')
def edit_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_detail', slug=course.slug)
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'courses/edit_course.html', {
        'form': form,
        'course': course
    })



@login_required
@user_passes_test(is_admin, login_url='/')
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            return redirect('lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    else:
        form = LessonForm(instance=lesson)
    
    return render(request, 'courses/edit_lesson.html', {
        'form': form,
        'course': lesson.course,
        'lesson': lesson
    })

@require_http_methods(["GET", "POST"])
def redir_to_quiz(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)

    if request.method == 'POST':
        # Проверяем, какую кнопку нажал пользователь
        action = request.POST.get('action')
        if action == 'start_quiz':
            return redirect('quiz_start', quiz_id=course.final_quiz.id)
        else:
            return redirect('profile')

    # GET-запрос - показываем страницу с подтверждением
    return render(request, 'courses/redir_to_quiz.html', {'course': course})

@require_POST
def complete_lesson(request, course_slug, lesson_id):
    """Отмечает урок как завершенный и начисляет пользователю опыт"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    if not UserCourse.objects.filter(user=request.user, course=course).exists():
        return redirect('course_detail', slug=course.slug)
    
    # Получаем траекторию пользователя
    trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
    
    # Проверяем, что урок входит в траекторию пользователя (если траектория задана)
    if trajectory and lesson not in trajectory.lessons.all():
        return redirect('course_detail', slug=course.slug)

    # Создаем или обновляем прогресс
    UserProgress.objects.update_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'completed': True, 'course': course}
    )

    # Получаем общее количество уроков для пользователя
    if trajectory:
        total_lessons = trajectory.lessons.count()
        lesson_ids = trajectory.lessons.values_list('id', flat=True)
    else:
        total_lessons = course.lessons.count()
        lesson_ids = course.lessons.values_list('id', flat=True)

    # Считаем ТОЛЬКО уроки из траектории
    completed_lessons = UserProgress.objects.filter(
        user=request.user,
        course=course,
        completed=True,
        lesson_id__in=lesson_ids
    ).count()

    all_completed = completed_lessons >= total_lessons

    user_course = UserCourse.objects.get(user=request.user, course=course)
    
    if all_completed:
        if course.final_quiz:
            return redirect('redir_to_quiz', course_slug=course_slug)
        else:
            user_course.is_completed = True
            user_course.save()
    
    return redirect('course_detail', slug=course.slug)


def complete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user_course = UserCourse.objects.get(user=request.user, course=course)
    
    if course.final_quiz:
        quiz_result = QuizResult.objects.filter(
            user=request.user,
            quiz=course.final_quiz,
            passed=True
        ).exists()
        
        if quiz_result:
            user_course.is_completed = True
            user_course.save()
            return redirect('course_detail', slug=course.slug)
        else:
            return redirect('quiz_start', quiz_id=course.final_quiz.id)
    else:
        user_course.is_completed = True
        user_course.save()
        return redirect('course_detail', slug=course.slug)
    

