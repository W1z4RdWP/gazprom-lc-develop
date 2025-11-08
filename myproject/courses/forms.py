from django import forms
from .models import Course, Lesson, UserLessonTrajectory
from django_ckeditor_5.fields import CKEditor5Widget
from captcha.fields import CaptchaField
import re

class CourseForm(forms.ModelForm):
    captcha = CaptchaField()
    class Meta:
        model = Course
        fields = ['title', 'description', 'image', 'slug', 'final_quiz']
        labels = {'slug': 'ЧПУ (оставьте пустым для автогенерации)'}
        required = {'slug': False}  # Поле slug не обязательно
        widgets = {
            'description': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='extends'
            )
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if slug and not re.match(r'^[-a-zA-Z0-9_]+$', slug):
            raise forms.ValidationError("ЧПУ может содержать только латинские буквы, цифры, дефисы и подчеркивания")
        return slug
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = "Рекомендуемый размер: 1200x600 пикселей"

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'video_id', 'order']
        widgets = {
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'}, 
                config_name='extends'
            )
        }

        labels = {
            'video_id': 'Ссылка на видео с Rutube'
        }

        help_texts = {
            'video_id': 'Введите полную ссылку на видео. Пример: https://rutube.ru/video/abcdef12345/'
        }


        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if not self.instance.pk:  # Только для новых уроков
                self.fields['order'].queryset = Lesson.objects.filter(
                    course=self.initial['course']
                ).order_by('order')


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