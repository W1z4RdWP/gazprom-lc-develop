import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Count, Exists, OuterRef
from django.contrib import messages  # Добавлен импорт
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import DetailView, TemplateView, CreateView
from django.urls import reverse_lazy

from myapp.models import QuizResult, UserCourse, UserAnswer
from courses.models import Course  # Добавлен импорт модели Course
from .models import Quiz, Question, Answer
from .forms import QuizForm
from .utils import DataMixin

from typing import Optional


class StartQuizView(DataMixin, TemplateView):
    """
    Класс представление для рендера стартовой страницы тестов.

    Атрибуты:
     - template_name - путь к шаблону;
     - get_context_data() - в шаблон передается переменная topics, которая возвращает количество вопросов в каждом тесте
    """
    template_name = 'quizzes/start.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context, topics=Quiz.objects.annotate(questions_count=Count('question')))




class CreateQuizView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """CBV формы создания теста"""
    model = Quiz
    form_class = QuizForm
    template_name = 'quizzes/create_quiz.html'


    def test_func(self):
        """Проверка прав доступа - только для администраторов"""
        return self.request.user.is_staff
    

    def get_form_kwargs(self):
        """Передача дополнительных параметров в форму"""
        kwargs = super().get_form_kwargs()
        
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
        quiz = self.object
        if quiz.directory:
            from django.urls import reverse
            return reverse('knowledge_base:kb_directory', kwargs={'directory_id': quiz.directory.id})
        else:
            return reverse_lazy('knowledge_base:kb_home')




@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_quiz(request, quiz_id):
    """Функция для редактирования теста"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    directory = quiz.directory
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz, directory=directory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тест успешно сохранён.')
            return redirect('quizzes:edit_quiz', quiz_id=quiz.id)
    else:
        form = QuizForm(instance=quiz, directory=directory)
    
    # Загружаем вопросы с ответами для отображения
    questions = Question.objects.filter(quiz=quiz).order_by('id').prefetch_related('answer_set')
    
    return render(request, 'quizzes/edit_quiz.html', {
        'form': form,
        'quiz': quiz,
        'questions': questions,
    })


# ==================== AJAX API для вопросов и ответов ====================

def _staff_required_json(user):
    """Проверка прав для AJAX-эндпоинтов"""
    return user.is_authenticated and user.is_staff


@login_required
@require_POST
@user_passes_test(_staff_required_json)
def api_add_question(request, quiz_id):
    """Добавить вопрос к тесту"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат данных'}, status=400)

    text = data.get('text', '').strip()
    question_type = data.get('question_type', Question.SINGLE)

    if not text:
        return JsonResponse({'error': 'Текст вопроса не может быть пустым'}, status=400)

    question = Question.objects.create(
        quiz=quiz,
        text=text,
        question_type=question_type
    )
    return JsonResponse({
        'id': question.id,
        'text': question.text,
        'question_type': question.question_type,
    })


@login_required
@require_POST
@user_passes_test(_staff_required_json)
def api_update_question(request, quiz_id, question_id):
    """Обновить вопрос"""
    question = get_object_or_404(Question, id=question_id, quiz_id=quiz_id)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат данных'}, status=400)

    text = data.get('text')
    question_type = data.get('question_type')

    if text is not None:
        text = text.strip()
        if not text:
            return JsonResponse({'error': 'Текст вопроса не может быть пустым'}, status=400)
        question.text = text

    if question_type is not None:
        if question_type in [Question.SINGLE, Question.MULTIPLE]:
            question.question_type = question_type

    question.save()
    return JsonResponse({
        'id': question.id,
        'text': question.text,
        'question_type': question.question_type,
    })


@login_required
@require_POST
@user_passes_test(_staff_required_json)
def api_delete_question(request, quiz_id, question_id):
    """Удалить вопрос"""
    question = get_object_or_404(Question, id=question_id, quiz_id=quiz_id)
    question.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
@user_passes_test(_staff_required_json)
def api_add_answer(request, quiz_id, question_id):
    """Добавить ответ к вопросу"""
    question = get_object_or_404(Question, id=question_id, quiz_id=quiz_id)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат данных'}, status=400)

    text = data.get('text', '').strip()
    is_correct = data.get('is_correct', False)

    if not text:
        return JsonResponse({'error': 'Текст ответа не может быть пустым'}, status=400)

    answer = Answer.objects.create(
        question=question,
        text=text,
        is_correct=is_correct
    )
    return JsonResponse({
        'id': answer.id,
        'text': answer.text,
        'is_correct': answer.is_correct,
    })


@login_required
@require_POST
@user_passes_test(_staff_required_json)
def api_update_answer(request, quiz_id, answer_id):
    """Обновить ответ"""
    answer = get_object_or_404(Answer, id=answer_id, question__quiz_id=quiz_id)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат данных'}, status=400)

    text = data.get('text')
    is_correct = data.get('is_correct')

    if text is not None:
        text = text.strip()
        if not text:
            return JsonResponse({'error': 'Текст ответа не может быть пустым'}, status=400)
        answer.text = text

    if is_correct is not None:
        answer.is_correct = bool(is_correct)

    answer.save()
    return JsonResponse({
        'id': answer.id,
        'text': answer.text,
        'is_correct': answer.is_correct,
    })


@login_required
@require_POST
@user_passes_test(_staff_required_json)
def api_delete_answer(request, quiz_id, answer_id):
    """Удалить ответ"""
    answer = get_object_or_404(Answer, id=answer_id, question__quiz_id=quiz_id)
    answer.delete()
    return JsonResponse({'success': True})




def get_questions(request, quiz_id: int = None, is_start: bool = False) -> HttpResponse:
    if request.method == 'POST' or is_start:
        # Если is_start=True, quiz_id берется из URL
        if is_start and not quiz_id:
            return redirect('quizzes:quizzes')
        
        # Если не стартовая страница, получаем quiz_id из сессии
        if not is_start:
            quiz_id = request.session.get('quiz_id')
            current_question_id = request.session.get('current_question_id')
            if not quiz_id or not current_question_id:
                return redirect('quizzes:quizzes')

            # Получаем следующий вопрос
            question = _get_subsequent_question(quiz_id, current_question_id)
        else:
            # Проверяем количество вопросов перед стартом теста
            questions_count = Question.objects.filter(quiz_id=quiz_id).count()
            if questions_count == 0:
                return redirect('quizzes:quiz_empty_warning', quiz_id=quiz_id)
            
            # Сброс сессии при старте нового теста
            request.session['quiz_id'] = quiz_id
            request.session['score'] = 0
            request.session['current_question_id'] = None
            
            # Получаем первый вопрос
            question = _get_first_question(quiz_id)

        if not question:
            return redirect('quizzes:get-finish')
        
        # Обновление сессии
        request.session['current_question_id'] = question.id
        answers = Answer.objects.filter(question=question)
        is_last = not Question.objects.filter(
            quiz_id=quiz_id, 
            id__gt=question.id
        ).exists()

        # Расчет прогресса
        all_questions_ids = list(Question.objects.filter(quiz_id=quiz_id)
                               .order_by('id')
                               .values_list('id', flat=True))
        current_index = all_questions_ids.index(question.id) + 1
        total_questions = len(all_questions_ids)
        progress_percent = int((current_index / total_questions) * 100)
        
        return render(request, 'quizzes/question.html', {
            'question': question,
            'answers': answers,
            'is_last': is_last,
            'current_question_number': current_index,
            'total_questions': total_questions,
            'progress_percent': progress_percent
        })
    
    return redirect(request.META['HTTP_REFERER'])

def _get_first_question(quiz_id: int) -> Optional[Question]:
    return Question.objects.filter(quiz_id=quiz_id).order_by('id').first()

def _get_subsequent_question(quiz_id: int, current_id: int) -> Optional[Question]:
    return Question.objects.filter(
        quiz_id=quiz_id,
        id__gt=current_id
    ).order_by('id').first()




def get_answer(request) -> HttpResponse:
    if request.method == 'POST':
        current_question_id = request.session.get('current_question_id')
        quiz_id = request.session.get('quiz_id')
        question = get_object_or_404(Question, id=current_question_id)
        is_correct = False

        # Получаем или инициализируем словарь ответов пользователя в сессии
        quiz_answers = request.session.get('quiz_answers', {})

        if question.question_type == Question.MULTIPLE:
            submitted_ids = request.POST.getlist('answer_ids')
            submitted_ids = [int(id) for id in submitted_ids]
            correct_answers = Answer.objects.filter(question=question, is_correct=True)
            correct_ids = set(correct_answers.values_list('id', flat=True))
            submitted_set = set(submitted_ids)
            is_correct = (submitted_set == correct_ids and len(submitted_ids) == len(correct_ids))

            # Сохраняем выбранные ответы в сессии
            quiz_answers[str(question.id)] = {
                'selected_ids': submitted_ids,
                'is_correct': is_correct,
                'question_type': 'multiple'
            }

            context = {
                'current_question_number': list(Question.objects.filter(quiz_id=quiz_id).order_by('id').values_list('id', flat=True)).index(current_question_id) + 1,
                'total_questions': Question.objects.filter(quiz_id=quiz_id).count(),
                'progress_percent': int(((list(Question.objects.filter(quiz_id=quiz_id).order_by('id').values_list('id', flat=True)).index(current_question_id) + 1) / Question.objects.filter(quiz_id=quiz_id).count()) * 100),
                'is_correct': is_correct,
                'question': question,
                'submitted_answers': Answer.objects.filter(id__in=submitted_ids),
                'correct_answers': correct_answers,
            }
        else:
            submitted_answer_id = request.POST.get('answer_id')
            if submitted_answer_id:
                try:
                    submitted_answer = Answer.objects.get(id=submitted_answer_id)
                except Answer.DoesNotExist:
                    messages.error(request, 'Выбранный ответ не найден.')
                    return redirect('quizzes:quizzes')

                is_correct = submitted_answer.is_correct

                # Сохраняем выбранный ответ в сессии
                quiz_answers[str(question.id)] = {
                    'selected_id': int(submitted_answer_id),
                    'is_correct': is_correct,
                    'question_type': 'single'
                }

                try:
                    correct_answer = Answer.objects.get(question=question, is_correct=True)
                except Answer.DoesNotExist:
                    messages.error(request, 'Ошибка данных вопроса: не найден правильный ответ.')
                    return redirect('quizzes:quizzes')

                context = {
                    'current_question_number': list(Question.objects.filter(quiz_id=quiz_id).order_by('id').values_list('id', flat=True)).index(current_question_id) + 1,
                    'total_questions': Question.objects.filter(quiz_id=quiz_id).count(),
                    'progress_percent': int(((list(Question.objects.filter(quiz_id=quiz_id).order_by('id').values_list('id', flat=True)).index(current_question_id) + 1) / Question.objects.filter(quiz_id=quiz_id).count()) * 100),
                    'is_correct': is_correct,
                    'question': question,
                    'submitted_answer': submitted_answer,
                    'correct_answer': correct_answer,
                }
            else:
                return redirect('quizzes:quizzes')

        # Сохраняем обновлённые ответы в сессии
        request.session['quiz_answers'] = quiz_answers
        request.session.modified = True

        # Обновление счета (опционально, если нужен быстрый счёт)
        if is_correct:
            request.session['score'] = request.session.get('score', 0) + 1
            request.session.modified = True

        return render(request, 'quizzes/answer.html', context)
    
    return redirect('quizzes:quizzes')



def get_finish(request) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect('login')

    quiz_id = request.session.get('quiz_id')
    if not quiz_id:
        return redirect('quizzes:quizzes')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions_count = Question.objects.filter(quiz=quiz).count() # Количество вопросов в тесте всего
    score = request.session.get('score', 0)
    percent_score = int((score / questions_count) * 100) if questions_count > 0 else 0 # Процент правильных ответов

    passed = percent_score >= 80
    quiz_result = QuizResult.objects.create(
        user=request.user,
        quiz_title=quiz.name,
        score=score,
        total_questions=questions_count,
        percent=percent_score,
        passed=passed
    )

    # --- СОХРАНЯЕМ ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ ---
    quiz_answers = request.session.get('quiz_answers', {})
    for q in Question.objects.filter(quiz=quiz):
        ans_data = quiz_answers.get(str(q.id))
        if not ans_data:
            continue
        if ans_data['question_type'] == 'multiple':
            for ans_id in ans_data['selected_ids']:
                ans = Answer.objects.get(id=ans_id)
                UserAnswer.objects.create(
                    user=request.user,
                    quiz_result=quiz_result,
                    question=q,
                    selected_answer=ans,
                    is_correct=ans.is_correct and ans_data['is_correct']
                )
        else:
            ans = Answer.objects.get(id=ans_data['selected_id'])
            UserAnswer.objects.create(
                user=request.user,
                quiz_result=quiz_result,
                question=q,
                selected_answer=ans,
                is_correct=ans.is_correct
            )
    # --------------------------------------------

    # Обработка привязки к курсу
    if hasattr(quiz, 'course') and quiz.course:
        course = quiz.course
        if passed:
            UserCourse.objects.filter(
                user=request.user, 
                course=course
            ).update(is_completed=True)
            return redirect('course_detail', slug=course.slug)
        else:
            messages.error(request, "Тест не пройден. Попробуйте снова!")
            return redirect('quizzes:quiz_start', quiz_id=quiz.id)

    context = {
        'score': score,
        'questions_count': questions_count,
        'percent_score': percent_score,
        'quiz_title': quiz.name
    }
    
    _reset_quiz(request)
    return render(request, 'quizzes/finish.html', context)

def _reset_quiz(request) -> HttpRequest:
    keys = ['quiz_id', 'current_question_id', 'score']
    for key in keys:
        if key in request.session:
            del request.session[key]
    return request

def start_quiz_handler(request):
    if request.method == 'POST':
        quiz_id = request.POST.get('quiz_id')
        if not quiz_id:
            return redirect('quizzes:quizzes')
        
        # Сохраняем в сессии и перенаправляем на тест
        request.session['quiz_id'] = int(quiz_id)
        request.session['score'] = 0
        request.session['current_question_id'] = None
        return redirect('quizzes:quiz_start', quiz_id=quiz_id)
    
    return redirect('quizzes:quizzes')


def quiz_empty_warning(request, quiz_id: int) -> HttpResponse:
    """Страница предупреждения о том, что в тесте нет вопросов"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    is_staff_or_superuser = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    
    return render(request, 'quizzes/quiz_empty_warning.html', {
        'quiz': quiz,
        'is_staff_or_superuser': is_staff_or_superuser
    })
