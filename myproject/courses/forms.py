from django import forms
from .models import Course, Lesson, UserLessonTrajectory, Quiz
from django_ckeditor_5.fields import CKEditor5Widget
from captcha.fields import CaptchaField
import re

class CourseForm(forms.ModelForm):
    captcha = CaptchaField()
    class Meta:
        model = Course
        fields = ['title', 'description', 'image', 'slug', 'directory', 'final_quiz']
        quizzes = forms.ModelMultipleChoiceField(
            queryset=Quiz.objects.all(),
            required=False,
            widget=forms.CheckboxSelectMultiple,
            label="Тесты курса"
        )
        labels = {
            'slug': 'ЧПУ (оставьте пустым для автогенерации)',
            'directory': 'Категория (необязательно)'
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
            'directory': 'Выберите категорию базы знаний, к которой относится курс, или оставьте пустым'
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

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'video_id', 'course', 'directory', 'order']
        widgets = {
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'}, 
                config_name='extends'
            ),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'directory': forms.Select(attrs={'class': 'form-control'})
        }

        labels = {
            'video_id': 'Ссылка на видео с Rutube',
            'course': 'Курс (необязательно)',
            'directory': 'Категория (необязательно)'
        }

        help_texts = {
            'video_id': 'Введите полную ссылку на видео. Пример: https://rutube.ru/video/abcdef12345/',
            'course': 'Выберите курс, к которому относится урок, или оставьте пустым',
            'directory': 'Выберите категорию базы знаний, к которой относится урок, или оставьте пустым'
        }


    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        self.directory = kwargs.pop('directory', None)
        super().__init__(*args, **kwargs)

        # Делаем поле course необязательным
        self.fields['course'].required = False
        self.fields['course'].empty_label = '--- Без курса ---'
        
        # Делаем поле directory необязательным
        self.fields['directory'].required = False
        self.fields['directory'].empty_label = '--- Без категории ---'
        
        # Если курс передан явно, скрываем поле и устанавливаем его значение
        if self.course:
            self.fields['course'].widget = forms.HiddenInput()
            self.fields['course'].initial = self.course

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
        # Если курс передан через kwargs, привязываем урок к курсу
        # (это для обратной совместимости со старым кодом)
        if self.course and not lesson.course:
            lesson.course = self.course
        if commit:
            lesson.save()
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
                if lesson.course != course:
                    raise forms.ValidationError(
                        f"Урок '{lesson.title}' не принадлежит выбранному курсу."
                    )
        return cleaned_data