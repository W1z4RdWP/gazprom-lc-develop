from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max, Count
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.views.generic import CreateView, DetailView, ListView

from quizzes.models import Quiz
from .forms import CourseForm, LessonForm, LessonAttachmentsForm
from .models import Course, Lesson, UserLessonTrajectory, LessonAttachment
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

    def get_completed_quizzes_data(self, course_quizzes):
        """Получение данных о пройденных тестах курса"""
        if not self.request.user.is_authenticated:
            return 0, []
        
        completed_quizzes = []
        completed_count = 0
        
        for quiz in course_quizzes:
            quiz_passed = QuizResult.objects.filter(
                user=self.request.user,
                quiz_title=quiz.name,
                passed=True
            ).exists()
            if quiz_passed:
                completed_quizzes.append(quiz.id)
                completed_count += 1
        
        return completed_count, completed_quizzes

    
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
                courses=self.object,
                order__gt=max_completed_order
            ).order_by('order').first()

            if not next_lesson:
                next_lesson = self.object.lessons.first()

        return next_lesson
        

    def calculate_progress(self, completed_lessons, total_lessons, completed_quizzes, total_quizzes):
        """Вычисление процента прогресса с учетом уроков и тестов"""
        total_items = total_lessons + total_quizzes
        if total_items > 0:
            completed_items = completed_lessons + completed_quizzes
            return int((completed_items / total_items) * 100)
        return 0
    

    def should_show_final_quiz(self, has_started, completed_lessons, total_lessons, completed_quizzes, total_quizzes):
        """Определение, нужно ли показывать финальный тест"""
        if not (self.request.user.is_authenticated and has_started):
            return False
        
        # Все уроки и тесты курса должны быть завершены
        all_lessons_and_quizzes_completed = (completed_lessons >= total_lessons and 
                                             completed_quizzes >= total_quizzes)
        
        if self.object.final_quiz:
            quiz_passed = QuizResult.objects.filter(
                user=self.request.user,
                quiz_title=self.object.final_quiz.name,
                passed=True
            ).exists()
            return quiz_passed and all_lessons_and_quizzes_completed
        else:
            return all_lessons_and_quizzes_completed


    def update_course_completion_animation(self, user_course, all_completed):
        """Обновление флага анимации завершения курса"""
        if all_completed and user_course and not user_course.course_complete_animation_shown:
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

        # Получаем тесты курса (не включая final_quiz)
        course_quizzes = self.object.quizzes.all().order_by('name')
        total_quizzes = course_quizzes.count()

        # Данные о прогрессе уроков
        completed_lessons, completed_lessons_ids = self.get_completed_lessons_data(lesson_ids)

        # Данные о прогрессе тестов
        completed_quizzes, completed_quizzes_ids = self.get_completed_quizzes_data(course_quizzes)

        # Вычисляем прогресс с учетом уроков и тестов
        progress = self.calculate_progress(completed_lessons, total_lessons, completed_quizzes, total_quizzes)

        # Следующий урок
        next_lesson = self.get_next_lesson(trajectory, lesson_ids) if has_started else None

        # Курс с 0 материалами не может быть завершён
        total_items = total_lessons + total_quizzes
        has_materials = total_items > 0

        # Проверка завершения всех уроков и тестов курса
        all_lessons_and_quizzes_completed = (
            has_materials
            and completed_lessons >= total_lessons
            and completed_quizzes >= total_quizzes
        )
        
        # Проверка завершения финального теста (если есть)
        final_quiz_passed = False
        if self.object.final_quiz:
            final_quiz_passed = QuizResult.objects.filter(
                user=self.request.user,
                quiz_title=self.object.final_quiz.name,
                passed=True
            ).exists() if self.request.user.is_authenticated else False

        # Курс считается завершенным только если есть материалы, все уроки,
        # все тесты курса и финальный тест (если есть) пройдены
        all_completed = all_lessons_and_quizzes_completed and (
            not self.object.final_quiz or final_quiz_passed
        )

        # Определяем, нужно ли показать анимацию (только один раз — при первом завершении)
        animation_already_shown = (
            user_course.course_complete_animation_shown if user_course else True
        )
        show_completion_animation = all_completed and not animation_already_shown

        # Обновление флага анимации завершения (ставим флаг ПОСЛЕ определения показа)
        self.update_course_completion_animation(user_course, all_completed)

        # Доп. данные
        exp_earned = user_course.exp_reward() if user_course else 0
        show_final_quiz = self.should_show_final_quiz(has_started, completed_lessons, total_lessons, 
                                                      completed_quizzes, total_quizzes)

        # Добавляем все в контекст
        context.update({
            'user_course': user_course,
            'has_started': has_started,
            'lessons': lessons,
            'course_quizzes': course_quizzes,
            'total_lessons': total_lessons,
            'total_quizzes': total_quizzes,
            'total_items': total_items,
            'completed_lessons': completed_lessons,
            'completed_quizzes': completed_quizzes,
            'completed_items': completed_lessons + completed_quizzes,
            'completed_lessons_ids': completed_lessons_ids,
            'completed_quizzes_ids': completed_quizzes_ids,
            'progress': progress,
            'next_lesson': next_lesson,
            'all_completed': all_completed,
            'exp_earned': exp_earned,
            'show_final_quiz': show_final_quiz,
            'final_quiz_passed': final_quiz_passed,
            'show_completion_animation': show_completion_animation,
        })

        return context




class CourseListView(ListView):
    """CBV для отображения списка всех доступных курсов пользователя"""
    template_name = 'courses/all_courses_list.html'
    paginate_by = 12
    model = UserCourse


    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        user_courses_qs = UserCourse.objects.filter(
            user=self.request.user
        ).select_related('course')

        courses_data = []
        for uc in user_courses_qs:
            course = uc.course
            total_lessons = course.lessons.count()
            total_quizzes = course.quizzes.count()
            total_materials = total_lessons + total_quizzes

            # Вычисляем прогресс по урокам
            completed_lessons = UserProgress.objects.filter(
                user=self.request.user,
                course=course,
                completed=True
            ).count()

            # Вычисляем прогресс по тестам
            completed_quizzes_count = 0

            for quiz in course.quizzes.all():
                if QuizResult.objects.filter(
                    user=self.request.user,
                    quiz_title=quiz.name,
                    passed=True
                ).exists():
                    completed_quizzes_count += 1

            total_items = total_lessons + total_quizzes
            completed_items = completed_lessons + completed_quizzes_count
            progress = int((completed_items / total_items) * 100) if total_items > 0 else 0

            courses_data.append({
                'course': course,
                'total_materials': total_materials,
                'total_lessons': total_lessons,
                'total_quizzes': total_quizzes,
                'progress': progress,
                'is_completed': uc.is_completed,
            })

        context.update({
            'courses_data': courses_data,
            'has_courses': len(courses_data) > 0,
        })

        return context




def lesson_detail(request, course_slug=None, lesson_id=None):
    if not request.user.is_authenticated:
        return redirect('login')

    # Если передан lesson_id без course_slug, это урок без курса
    if lesson_id and not course_slug:
        lesson = get_object_or_404(Lesson, id=lesson_id)
        attachments = lesson.attachments.all()
        # Проверяем, есть ли у урока курсы
        if lesson.courses.exists():
            # Если есть курсы, берем первый для отображения
            course = lesson.courses.first()
            return render(request, 'courses/lesson_detail.html', {
                'lesson': lesson, 
                'course': course,
                'attachments': attachments
            })
        return render(request, 'courses/lesson_detail.html', {
            'lesson': lesson, 
            'course': None,
            'attachments': attachments
        })
    
    # Старый вариант - урок с курсом
    if course_slug and lesson_id:
        course = get_object_or_404(Course, slug=course_slug)
        lesson = get_object_or_404(Lesson, id=lesson_id, courses=course)

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
        
        attachments = lesson.attachments.all()
        return render(request, 'courses/lesson_detail.html', {
            'lesson': lesson, 
            'course': course,
            'attachments': attachments
        })
    
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
        form.instance.author = self.request.user
        return super().form_valid(form)
    

    def get_context_data(self, **kwargs):
        """Добавление контекста для шаблона"""
        context = super().get_context_data(**kwargs)
        
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
        course = self.object
        if course.directory:
            from django.urls import reverse
            return reverse('knowledge_base:kb_directory', kwargs={'directory_id': course.directory.id})
        else:
            return reverse_lazy('knowledge_base:kb_home')




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
        """Обработка валидной формы и загрузки файлов"""
        response = super().form_valid(form)
        
        # Обрабатываем загруженные файлы
        files = self.request.FILES.getlist('attachments')
        for file in files:
            LessonAttachment.objects.create(
                lesson=self.object,
                file=file,
                name=file.name
            )
        
        return response
    
    
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
        
        # Форма для загрузки файлов
        context['attachments_form'] = LessonAttachmentsForm()
        
        return context
    

    def get_success_url(self):
        """Перенаправление после успешного создания"""
        lesson = self.object
        if lesson.courses.exists():
            # Если урок привязан к курсам, берем первый курс
            return reverse_lazy('courses:course_detail', kwargs={'slug': lesson.courses.first().slug})
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
        # Сохраняем информацию о курсах и директории до удаления
        courses = list(lesson.courses.all())
        directory = lesson.directory
        lesson.delete()
        if courses:
            return redirect('courses:course_detail', slug=courses[0].slug)
        elif directory:
            from django.urls import reverse
            return redirect('knowledge_base:kb_directory', directory_id=directory.id)
        else:
            return redirect('knowledge_base:kb_home')
    # Для GET запроса
    if lesson.courses.exists():
        return redirect('courses:course_detail', slug=lesson.courses.first().slug)
    elif lesson.directory:
        from django.urls import reverse
        return redirect('knowledge_base:kb_directory', directory_id=lesson.directory.id)
    else:
        return redirect('knowledge_base:kb_home')




@login_required
@user_passes_test(lambda u: is_author_or_admin(u, Course), login_url='/')
def edit_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    directory = course.directory
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course, user=request.user, directory=directory)
        if form.is_valid():
            form.save()
            # Перенаправляем в зависимости от того, где находится курс
            if course.directory:
                return redirect('knowledge_base:kb_directory', directory_id=course.directory.id)
            else:
                return redirect('courses:course_detail', slug=course.slug)
    else:
        form = CourseForm(instance=course, user=request.user, directory=directory)
    
    return render(request, 'courses/edit_course.html', {
        'form': form,
        'course': course
    })




@login_required
@user_passes_test(is_admin, login_url='/')
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    # Берем первый курс, если есть
    course = lesson.courses.first() if lesson.courses.exists() else None
    directory = lesson.directory
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson, course=course, directory=directory)
        
        # Обработка удаления файлов
        delete_attachments = request.POST.getlist('delete_attachments')
        if delete_attachments:
            LessonAttachment.objects.filter(id__in=delete_attachments, lesson=lesson).delete()
        
        if form.is_valid():
            form.save()
            
            # Обработка загрузки новых файлов
            files = request.FILES.getlist('attachments')
            for file in files:
                LessonAttachment.objects.create(
                    lesson=lesson,
                    file=file,
                    name=file.name
                )
            
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
        'course': course,
        'lesson': lesson,
        'attachments': lesson.attachments.all(),
        'attachments_form': LessonAttachmentsForm()
    })




@require_http_methods(["GET", "POST"])
def redir_to_quiz(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)

    if request.method == 'POST':
        # Проверяем, какую кнопку нажал пользователь
        action = request.POST.get('action')
        if action == 'start_quiz':
            return redirect('quizzes:quiz_start', quiz_id=course.final_quiz.id)
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
    lesson = get_object_or_404(Lesson, id=lesson_id, courses=course)
    
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

    # Проверяем завершение всех тестов курса
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

    # Все уроки и тесты курса должны быть завершены
    all_lessons_and_quizzes_completed = (completed_lessons >= total_lessons and 
                                         completed_quizzes >= total_quizzes)

    user_course = UserCourse.objects.get(user=request.user, course=course)
    
    if all_lessons_and_quizzes_completed:
        # Проверяем финальный тест
        if course.final_quiz:
            final_quiz_passed = QuizResult.objects.filter(
                user=request.user,
                quiz_title=course.final_quiz.name,
                passed=True
            ).exists()
            if final_quiz_passed:
                user_course.is_completed = True
                user_course.save()
            else:
                return redirect('courses:redir_to_quiz', course_slug=course_slug)
        else:
            user_course.is_completed = True
            user_course.save()
    
    return redirect('courses:course_detail', slug=course.slug)




def complete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user_course = UserCourse.objects.get(user=request.user, course=course)

    # Курс с 0 материалами не может быть завершён
    total_materials = course.lessons.count() + course.quizzes.count()
    if total_materials == 0:
        return redirect('courses:course_detail', slug=course.slug)
    
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
            return redirect('quizzes:quiz_start', quiz_id=course.final_quiz.id)
    else:
        user_course.is_completed = True
        user_course.save()
        return redirect('courses:course_detail', slug=course.slug)




@login_required
@user_passes_test(is_admin, login_url='/')
def get_available_lessons(request, course_slug):
    """Получение списка доступных уроков для добавления в курс (JSON API)"""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Получаем ID уроков, которые уже привязаны к этому курсу
    course_lesson_ids = course.lessons.values_list('id', flat=True)
    
    # Получаем уроки, которые еще не привязаны к этому курсу
    available_lessons = Lesson.objects.exclude(id__in=course_lesson_ids).order_by('title')
    
    lessons_data = []
    for lesson in available_lessons:
        courses_list = ', '.join([c.title for c in lesson.courses.all()]) if lesson.courses.exists() else 'Без курса'
        lessons_data.append({
            'id': lesson.id,
            'title': lesson.title,
            'current_course': courses_list,
            'directory': lesson.directory.name if lesson.directory else 'Без категории',
        })
    
    return JsonResponse({'lessons': lessons_data})




@login_required
@user_passes_test(is_admin, login_url='/')
@require_POST
def add_lesson_to_course(request, course_slug):
    """Добавление существующего урока в курс"""
    course = get_object_or_404(Course, slug=course_slug)
    lesson_id = request.POST.get('lesson_id')
    
    if not lesson_id:
        return JsonResponse({'success': False, 'error': 'Не указан ID урока'}, status=400)
    
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        # Проверяем, не добавлен ли уже урок в этот курс
        if lesson.courses.filter(id=course.id).exists():
            return JsonResponse({'success': False, 'error': 'Урок уже добавлен в этот курс'}, status=400)
        
        # Добавляем урок в курс через ManyToMany
        lesson.courses.add(course)
        
        return JsonResponse({'success': True, 'message': f'Урок "{lesson.title}" успешно добавлен в курс'})
    except Lesson.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Урок не найден'}, status=404)
    

@login_required
@user_passes_test(is_admin, login_url='/')
def get_available_quizzes(request, course_slug):
    """Получение списка доступных тестов для добавления в курс (JSON API)"""
    course = get_object_or_404(Course, slug=course_slug)

    # Получаем ID тестов, которые уже привязаны к курсу
    course_quiz_ids = course.quizzes.values_list('id', flat=True)
    
    # Получаем тесты, которые еще не привязаны к этому курсу
    available_quizzes = Quiz.objects.exclude(id__in=course_quiz_ids).order_by('name')
    
    # Исключаем также финальный тест курса, если он есть
    if course.final_quiz:
        available_quizzes = available_quizzes.exclude(id=course.final_quiz.id)

    quizzes_data = []
    for quiz in available_quizzes:
        quizzes_data.append({
            'id': quiz.id,
            'name': quiz.name,
            'directory': quiz.directory.name if quiz.directory else 'Без категории',
        })

    return JsonResponse({'quizzes': quizzes_data})


@login_required
@user_passes_test(is_admin, login_url='/')
@require_POST
def add_quiz_to_course(request, course_slug):
    """Добавление существующего теста в курс"""
    course = get_object_or_404(Course, slug=course_slug)
    quiz_id = request.POST.get('quiz_id')

    if not quiz_id:
        return JsonResponse({'success': False, 'error': 'Не указан ID теста'}, status=400)

    try:
        quiz = Quiz.objects.get(id=quiz_id)
        # Добавлеяем тест в курс через ManyToMany
        course.quizzes.add(quiz)
        return JsonResponse({'success': True, 'message': f'Тест "{quiz.name}" успешно добавлен в курс'})
    except Quiz.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Тест не найден'}, status=404)


@login_required
@user_passes_test(is_admin, login_url='/')
@require_POST
def delete_attachment(request, attachment_id):
    """Удаление прикреплённого файла"""
    attachment = get_object_or_404(LessonAttachment, id=attachment_id)
    lesson = attachment.lesson
    attachment.delete()
    
    # Если это AJAX-запрос, возвращаем JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Файл удалён'})
    
    # Иначе редирект обратно на страницу редактирования
    return redirect('courses:edit_lesson', lesson_id=lesson.id)