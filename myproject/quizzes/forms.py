from django import forms
from .models import Quiz, Question, Answer

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['name', 'directory']
        labels = {
            'directory': 'Категория (необязательно)'
        }
        widgets = {
            'directory': forms.Select(attrs={'class': 'form-control'})
        }
        help_texts = {
            'directory': 'Выберите категорию базы знаний, к которой относится тест, или оставьте пустым'
        }
    
    def __init__(self, *args, **kwargs):
        self.directory = kwargs.pop('directory', None)
        self.course_only = kwargs.pop('course_only', False)
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        if self.course_only:
            self.fields.pop('directory', None)
        else:
            self.fields['directory'].required = False
            self.fields['directory'].empty_label = '--- Без категории ---'
            if self.directory:
                self.fields['directory'].initial = self.directory

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']