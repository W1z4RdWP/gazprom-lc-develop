from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.views.generic import CreateView, DetailView, ListView
from .forms import CourseForm, LessonForm
from .models import Course, Lesson, UserLessonTrajectory
from myapp.models import UserProgress, UserCourse, QuizResult
from myapp.views import is_admin, is_author_or_admin




class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    slug_url_kwarg = 'slug'

    def post(self, request, *args, **kwargs):
        """Обработка POST запроса для начала курса"""
        self.object = self.get_object()

        # Проверяем, начал ли пользователь курс
        user_course = UserCourse.objects.filter(
            user=request.user,
            course=self.object
        ).first()

        # Если нажата кнопка "Начать курс" и курс еще не начат
        if 'start_course' in request.POST and not user_course:
            UserCourse.objects.create(user=request.user, course=self.object)
            return redirect('courses:course_detail', slug=self.object.slug)
        
        # Если POST не обработан, просто показываем страницу как GET
        return self.get(request, *args, **kwargs)


    def get_user_course(self):
        """Получение UserCourse для текущего пользователя"""
        if not self.request.user.is_authenticated:
            return None
        return UserCourse.objects.filter(
            user=self.request.user,
            course=self.object
        ).first()


    def get_trajectory(self):
        """Получение траектории уроков для пользователя"""
        if not self.request.user.is_authenticated:
            return None
        return UserLessonTrajectory.objects.filter(
            user=self.request.user,
            course=self.object
        ).first()


    def get_lessons_and_ids(self, trajectory):
        """Получение списка уроков и их ID"""
        if trajectory:
            lessons = trajectory.lessons.all()
            total_lessons = lessons.count()  # Обновляем количество уроков, если есть траектория
            lesson_ids = lessons.values_list('id', flat=True)  # Получаем ID уроков в траектории
        else:
            lessons = self.object.lessons.all()
            total_lessons = lessons.count()
            lesson_ids = lessons.values_list('id', flat=True)
        return lessons, lesson_ids, total_lessons

    
    def get_completed_lessons_data(self, lesson_ids):
        """Получение данных о завершенных уроках"""
        completed_lessons = UserProgress.objects.filter(
            user=self.request.user,
            course=self.object,
            completed=True,
            lesson_id__in=lesson_ids
        )

        completed_count = completed_lessons.count()
        completed_ids = completed_lessons.values_list('lesson_id', flat=True)

        return completed_count, completed_ids

    
    def get_next_lesson(self, trajectory, lesson_ids):
        """Определение следующего урока для изучения"""
        if trajectory:
            lessons = trajectory.lessons.all()
            max_completed_order = UserProgress.objects.filter(
                user=self.request.user,
                course=self.object,
                completed=True,
                lesson_id__in=lesson_ids
            ).aggregate(max_order=Max('lesson__order'))['max_order'] or 0

            next_lesson = Lesson.objects.filter(
                id__in=lesson_ids,
                order__gt=max_completed_order
            ).order_by('order').first()

            if not next_lesson:
                next_lesson = lessons.first()

        else:
            max_completed_order = UserProgress.objects.filter(
                user=self.request.user,
                course=self.object,
                completed=True
            ).aggregate(max_order=Max('lesson__order'))['max_order'] or 0

            next_lesson = Lesson.objects.filter(
                course=self.object,
                order__gt=max_completed_order
            ).order_by('order').first()

            if not next_lesson:
                next_lesson = self.object.lessons.first()

        return next_lesson
        

    def calculate_progress(self, completed_lessons, total_lessons):
        """Вычисление процента прогресса"""
        if total_lessons > 0:
            return int((completed_lessons / total_lessons) * 100)
        return 0
    
    def should_show_final_quiz(self, has_started, completed_lessons, total_lessons):
        """Определение, нужно ли показывать финальный тест"""
        if not (self.request.user.is_authenticated and has_started):
            return False
        
        if self.object.final_quiz:
            quiz_passed = QuizResult.objects.filter(
                user=self.request.user,
                quiz_title=self.object.final_quiz.name,
                passed=True
            ).exists()
            return quiz_passed
        else:
            return completed_lessons == total_lessons


    def update_course_completion_animation(self, user_course, all_completed):
        """Обновление флага анимации завершения курса"""
        if all_completed and user_course and not user_course.course_completed_animation_shown:
            with transaction.atomic():
                user_course.refresh_from_db()
                if not user_course.course_complete_animation_shown:
                    user_course.end_date = timezone.now()
                    user_course.is_completed = True
                    user_course.course_complete_animation_shown = True
                    user_course.save()
    


    def get_context_data(self, **kwargs):
        """Формирование контекста для шаблона"""
        context = super().get_context_data(**kwargs)

        user_course = self.get_user_course()
        has_started = user_course is not None
        trajectory = self.get_trajectory()

        # Получаем уроки
        lessons, lesson_ids, total_lessons = self.get_lessons_and_ids(trajectory)

        # Данные о прогрессе
        completed_lessons, completed_lessons_ids = self.get_completed_lessons_data(lesson_ids)

        # Вычисляем прогресс
        progress = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0

        # Следующий урок
        next_lesson = self.get_next_lesson(trajectory, lesson_ids) if has_started else None

        # Проверка завершения
        all_completed = completed_lessons >= total_lessons

        # Обновление анимации завершения 
        self.update_course_completion_animation(user_course, all_completed)

        # Доп. данные
        exp_earned = user_course.exp_reward() if user_course else 0
        show_final_quiz = self.should_show_final_quiz(has_started, completed_lessons, total_lessons)

        # Добавляем все в контекст
        context.update({
            'user_course': user_course,
            'has_started': has_started,
            'lessons': lessons,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'completed_lessons_ids': completed_lessons_ids,
            'progress': progress,
            'next_lesson': next_lesson,
            'all_completed': all_completed,
            'exp_earned': exp_earned,
            'show_final_quiz': show_final_quiz,
            'shown_animation': user_course.course_complete_animation_shown if user_course else False
        })

        return context




class CourseListView(ListView):
    """CBV для отображения списка всех доступных курсов пользователя"""
    template_name = 'courses/all_courses_list.html'
    paginate_by = 10
    model = UserCourse

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        courses = []
        completed_courses = []

        # Получаем курсы, назначенные пользователю
        user_courses = UserCourse.objects.filter(user=self.request.user).values_list('course', flat=True)
        courses = Course.objects.filter(id__in=user_courses)
        # Получаем список завершенных курсов
        completed_courses = UserCourse.objects.filter(
            user=self.request.user, 
            is_completed=True
        ).values_list('course_id', flat=True)

        context.update({
            'courses': courses,
            'completed_courses': completed_courses,
        })

        return context




def lesson_detail(request, course_slug=None, lesson_id=None):
    if not request.user.is_authenticated:
        return redirect('login')

    # Если передан lesson_id без course_slug, это урок без курса
    if lesson_id and not course_slug:
        lesson = get_object_or_404(Lesson, id=lesson_id, course__isnull=True)
        return render(request, 'courses/lesson_detail.html', {'lesson': lesson, 'course': None})
    
    # Старый вариант - урок с курсом
    if course_slug and lesson_id:
        course = get_object_or_404(Course, slug=course_slug)
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

        # Проверка доступа к курсу
        user_course = UserCourse.objects.filter(user=request.user, course=course).first()
        if not user_course:
            return redirect('courses:course_detail', slug=course.slug)

        # Проверка траектории
        trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
        if trajectory:
            lessons_in_trajectory = trajectory.lessons.all()
            if lesson not in lessons_in_trajectory:
                return redirect('courses:course_detail', slug=course.slug)

        # Помечаем урок как просмотренный (но не завершенный)
        UserProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'course': course}
        )
        return render(request, 'courses/lesson_detail.html', {'lesson': lesson, 'course': course})
    
    return redirect('knowledge_base:kb_home')




class CreateCourseView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """CBV формы создания курса"""
    model = Course
    form_class = CourseForm
    # success_url = reverse_lazy('home')
    template_name = 'courses/create_course.html'

    def test_func(self):
        return self.request.user.is_staff
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('home')




class CreateLessonView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """CBV формы создания урока"""
    model = Lesson
    form_class = LessonForm
    template_name = 'courses/create_lesson.html'

    def test_func(self):
        """Проверка прав доступа - только для администраторов"""
        return self.request.user.is_staff
    
    def get_form_kwargs(self):
        """Передача дополнительных параметров в форму"""
        kwargs = super().get_form_kwargs()
        # Получаем course_slug из URL, если он есть (для обратной совместимости)
        course_slug = self.kwargs.get('course_slug')
        if course_slug:
            try:
                course = Course.objects.get(slug=course_slug)
                kwargs['course'] = course
            except Course.DoesNotExist:
                pass
        
        # Получаем directory_id из GET-параметра
        directory_id = self.request.GET.get('directory')
        if directory_id:
            try:
                from knowledge_base.models import Directory
                directory = Directory.objects.get(id=directory_id)
                kwargs['directory'] = directory
            except (Directory.DoesNotExist, ValueError):
                pass
        
        return kwargs

    def form_valid(self, form):
        """Обработка валидной формы"""
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Добавление контекста для шаблона"""
        context = super().get_context_data(**kwargs)
        # Получаем курс из URL, если он есть
        course_slug = self.kwargs.get('course_slug')
        if course_slug:
            try:
                context['course'] = Course.objects.get(slug=course_slug)
            except Course.DoesNotExist:
                pass
        
        # Получаем директорию из GET-параметра
        directory_id = self.request.GET.get('directory')
        if directory_id:
            try:
                from knowledge_base.models import Directory
                context['directory'] = Directory.objects.get(id=directory_id)
            except (Directory.DoesNotExist, ValueError):
                pass
        
        return context
    
    def get_success_url(self):
        """Перенаправление после успешного создания"""
        lesson = self.object
        if lesson.course:
            return reverse_lazy('courses:course_detail', kwargs={'slug': lesson.course.slug})
        elif lesson.directory:
            from django.urls import reverse
            return reverse('knowledge_base:kb_directory', kwargs={'directory_id': lesson.directory.id})
        else:
            return reverse_lazy('knowledge_base:kb_home')
    





@login_required
@user_passes_test(is_admin, login_url='/')
def delete_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == 'POST':
        course.delete()
        return redirect('home')
    return redirect('courses:course_detail', slug=slug)


@login_required
@user_passes_test(is_admin, login_url='/')
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        course = lesson.course  # Сохраняем курс до удаления
        directory = lesson.directory  # Сохраняем директорию до удаления
        lesson.delete()
        if course:
            return redirect('courses:course_detail', slug=course.slug)
        elif directory:
            from django.urls import reverse
            return redirect('knowledge_base:kb_directory', directory_id=directory.id)
        else:
            return redirect('knowledge_base:kb_home')
    # Для GET запроса
    if lesson.course:
        return redirect('courses:course_detail', slug=lesson.course.slug)
    elif lesson.directory:
        from django.urls import reverse
        return redirect('knowledge_base:kb_directory', directory_id=lesson.directory.id)
    else:
        return redirect('knowledge_base:kb_home')


@login_required
@user_passes_test(lambda u: is_author_or_admin(u, Course), login_url='/')
def edit_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courses:course_detail', slug=course.slug)
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
    directory = lesson.directory
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson, course=course, directory=directory)
        if form.is_valid():
            form.save()
            if course:
                return redirect('courses:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
            elif lesson.directory:
                return redirect('knowledge_base:kb_directory', directory_id=lesson.directory.id)
            else:
                return redirect('knowledge_base:kb_home')
    else:
        form = LessonForm(instance=lesson, course=course, directory=directory)
    
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
        return redirect('courses:course_detail', slug=course.slug)
    
    # Получаем траекторию пользователя
    trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
    
    # Проверяем, что урок входит в траекторию пользователя (если траектория задана)
    if trajectory and lesson not in trajectory.lessons.all():
        return redirect('courses:course_detail', slug=course.slug)

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
            return redirect('courses:redir_to_quiz', course_slug=course_slug)
        else:
            user_course.is_completed = True
            user_course.save()
    
    return redirect('courses:course_detail', slug=course.slug)


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
            return redirect('courses:course_detail', slug=course.slug)
        else:
            return redirect('quiz_start', quiz_id=course.final_quiz.id)
    else:
        user_course.is_completed = True
        user_course.save()
        return redirect('courses:course_detail', slug=course.slug)
    

