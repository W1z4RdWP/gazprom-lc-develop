from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
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
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='Группы',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'groups']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'family-name'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('password1', 'password2'):
            if name in self.fields:
                self.fields[name].widget.attrs['class'] = 'form-control'




class AdminUserEditForm(forms.Form):
    """Форма редактирования пользователя администратором (is_staff): имя, фамилия, почта, группы."""
    first_name = forms.CharField(max_length=150, required=False, label='Имя', widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    last_name = forms.CharField(max_length=150, required=False, label='Фамилия', widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    email = forms.EmailField(required=False, label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='Группы',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['groups'].initial = user.groups.all()

    def save(self):
        if not self._user:
            return None
        self._user.first_name = self.cleaned_data.get('first_name', '')
        self._user.last_name = self.cleaned_data.get('last_name', '')
        self._user.email = self.cleaned_data.get('email', '')
        self._user.save()
        self._user.groups.set(self.cleaned_data.get('groups', []))
        return self._user


class ChangeUserPasswordForm(forms.Form):
    """Форма смены пароля пользователя администратором."""

    password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        min_length=8,
        required=True,
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        min_length=8,
        required=True,
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            validate_password(password1, self._user)
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают.')
        return password2

    def save(self):
        if not self._user:
            return None
        self._user.set_password(self.cleaned_data['password1'])
        self._user.save()
        return self._user
