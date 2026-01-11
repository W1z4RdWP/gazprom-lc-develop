from django import forms
from django.contrib.auth.models import Group
from .models import Course, Lesson, UserLessonTrajectory, Quiz
from django_ckeditor_5.fields import CKEditor5Widget
from captcha.fields import CaptchaField
import re

class CourseForm(forms.ModelForm):
    captcha = CaptchaField()
    
    assigned_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'group-checkbox-list'}),
        label="Назначить группам",
        help_text="Пользователям из выбранных групп будет автоматически назначен этот курс"
    )
    
    class Meta:
        model = Course
        fields = ['title', 'description', 'image', 'slug', 'directory', 'final_quiz', 'assigned_groups']
        quizzes = forms.ModelMultipleChoiceField(
            queryset=Quiz.objects.all(),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            label="Тесты курса"
        )
        labels = {
            'slug': 'ЧПУ (оставьте пустым для автогенерации)',
            'directory': 'Категория (необязательно)',
            'assigned_groups': 'Назначить группам'
        }
        required = {'slug': False}  # Поле slug не обязательно
        widgets = {
            'description': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='extends'
            ),
            'directory': forms.Select(attrs={'class': 'form-control'})
        }
        help_texts = {
            'directory': 'Выберите категорию базы знаний, к которой относится курс, или оставьте пустым',
            'assigned_groups': 'Пользователям из выбранных групп будет автоматически назначен этот курс'
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if slug and not re.match(r'^[-a-zA-Z0-9_]+$', slug):
            raise forms.ValidationError("ЧПУ может содержать только латинские буквы, цифры, дефисы и подчеркивания")
        return slug

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and self.user:
            # Проверяем существует ли уже курс с таким названием у этого автора
            qs = Course.objects.filter(title=title, author=self.user)
            # Если форма редактирует существующий курс, исключаем его из проверки
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    f"Курс с названием '{title}' уже существует у вас. Пожалуйста, выберите другое название."
                )
        return title


    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.directory = kwargs.pop('directory', None)
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = "Рекомендуемый размер: 1200x600 пикселей"
        
        # Делаем поле directory необязательным
        self.fields['directory'].required = False
        self.fields['directory'].empty_label = '--- Без категории ---'
        
        # Если директория передана явно, устанавливаем её значение
        if self.directory:
            self.fields['directory'].initial = self.directory
        
        # Инициализируем поле assigned_groups текущими значениями при редактировании
        if self.instance and self.instance.pk:
            self.fields['assigned_groups'].initial = self.instance.assigned_groups.all()

    def save(self, commit=True):
        # ВАЖНО: Сохраняем старые группы ДО вызова super().save(),
        # потому что после него ManyToMany связи уже будут обновлены
        if self.instance and self.instance.pk:
            old_groups = set(self.instance.assigned_groups.all())
        else:
            old_groups = set()
        
        # Получаем выбранные группы из формы
        assigned_groups = self.cleaned_data.get('assigned_groups', [])
        new_groups = set(assigned_groups)
        
        # Находим новые группы (которые были добавлены)
        added_groups = new_groups - old_groups
        
        # Сохраняем курс
        course = super().save(commit=commit)
        
        if commit and added_groups:
            # Назначаем курс пользователям из новых групп
            from myapp.models import UserCourse
            from django.contrib.auth.models import User
            
            for group in added_groups:
                users_in_group = User.objects.filter(groups=group)
                for user in users_in_group:
                    UserCourse.objects.get_or_create(
                        user=user,
                        course=course
                    )
        
        return course

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'video_id', 'courses', 'directory', 'order']
        widgets = {
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'}, 
                config_name='extends'
            ),
            'courses': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'directory': forms.Select(attrs={'class': 'form-control'})
        }

        labels = {
            'video_id': 'Ссылка на видео с Rutube',
            'courses': 'Курсы (необязательно)',
            'directory': 'Категория (необязательно)'
        }

        help_texts = {
            'video_id': 'Введите полную ссылку на видео. Пример: https://rutube.ru/video/abcdef12345/',
            'courses': 'Выберите курсы, к которым относится урок, или оставьте пустым',
            'directory': 'Выберите категорию базы знаний, к которой относится урок, или оставьте пустым'
        }


    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)  # Для обратной совместимости
        self.directory = kwargs.pop('directory', None)
        super().__init__(*args, **kwargs)

        # Делаем поле courses необязательным
        self.fields['courses'].required = False
        
        # Делаем поле directory необязательным
        self.fields['directory'].required = False
        self.fields['directory'].empty_label = '--- Без категории ---'
        
        # Если курс передан явно (для обратной совместимости), добавляем его к courses
        if self.course:
            if self.instance and self.instance.pk:
                # При редактировании добавляем курс, если его еще нет
                if self.course not in self.instance.courses.all():
                    self.initial['courses'] = list(self.instance.courses.all()) + [self.course]
            else:
                # При создании устанавливаем курс
                self.initial['courses'] = [self.course]

        # Если директория передана явно, устанавливаем её значение
        if self.directory:
            self.fields['directory'].initial = self.directory

        # Делаем поле order необязательным (будет автоматически вычисляться)
        self.fields['order'].required = False
        self.fields['order'].help_text = 'Порядок урока (необязательно, будет автоматически вычислен)'


    def clean_video_id(self):
        video_url = self.cleaned_data.get('video_id')
        if not video_url:
            return None
            
        # Извлекаем ID видео из URL
        match = re.match(
            r'^https?://rutube\.ru/video/(?:embed/)?([a-zA-Z0-9_-]{32})(?:/|\?|$)', 
            video_url
        )
        
        if not match:
            raise forms.ValidationError("Некорректная ссылка на Rutube. Пример правильной ссылки: https://rutube.ru/video/abcdef12345/")
            
        return match.group(1)

    
    def save(self, commit=True):
        lesson = super().save(commit=False)
        if commit:
            lesson.save()
            # Сохраняем ManyToMany связи
            self.save_m2m()
            # Если курс передан через kwargs (для обратной совместимости), добавляем его
            if self.course and self.course not in lesson.courses.all():
                lesson.courses.add(self.course)
        return lesson
    

class UserLessonTrajectoryForm(forms.ModelForm):
    class Meta:
        model = UserLessonTrajectory
        fields = '__all__'
        widgets = {
            'course': forms.Select(attrs={'onchange': 'this.form.submit();'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['course'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        lessons = cleaned_data.get('lessons')

        if course and lessons:
            for lesson in lessons:
                if course not in lesson.courses.all():
                    raise forms.ValidationError(
                        f"Урок '{lesson.title}' не принадлежит выбранному курсу."
                    )
        return cleaned_data