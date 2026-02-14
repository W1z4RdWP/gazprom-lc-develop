from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
# from captcha.fields import CaptchaField




class UserUpdateForm(forms.ModelForm):
    """
    Форма для обновления данных пользователя.

    Attributes:
        Meta: Метаданные формы.
    """
        
    class Meta:
        """
        Метаданные формы.

        Attributes:
            model (User): Модель, с которой связана форма.
            fields (list): Поля, которые будут отображаться в форме.
        """
                
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': True, 'autocomplete': 'off'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email', 'autocomplete': 'off'}),
        }




class ProfileUpdateForm(forms.ModelForm):
    """
    Форма для обновления профиля пользователя.

    Attributes:
        Meta: Метаданные формы.
    """
        
    class Meta:
        """
        Метаданные формы.

        Attributes:
            model (Profile): Модель, с которой связана форма.
            fields (list): Поля, которые будут отображаться в форме.
        """
        
        model = Profile
        fields = ['image', 'bio']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'autocomplete': 'off'}),
        }


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации нового пользователя (для администратора)."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False, label='Имя')
    last_name = forms.CharField(max_length=150, required=False, label='Фамилия')
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='Группа',
        empty_label='— не выбрано —'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'group']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'family-name'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('password1', 'password2'):
            if name in self.fields:
                self.fields[name].widget.attrs['class'] = 'form-control'




class AdminUserEditForm(forms.Form):
    """Форма редактирования пользователя администратором (is_staff): имя, фамилия, почта, группа."""
    first_name = forms.CharField(max_length=150, required=False, label='Имя', widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    last_name = forms.CharField(max_length=150, required=False, label='Фамилия', widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    email = forms.EmailField(required=False, label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='Группа',
        empty_label='— не выбрано —',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            current_group = user.groups.first()
            if current_group:
                self.fields['group'].initial = current_group

    def save(self):
        if not self._user:
            return None
        self._user.first_name = self.cleaned_data.get('first_name', '')
        self._user.last_name = self.cleaned_data.get('last_name', '')
        self._user.email = self.cleaned_data.get('email', '')
        self._user.save()
        self._user.groups.clear()
        group = self.cleaned_data.get('group')
        if group:
            self._user.groups.add(group)
        return self._user