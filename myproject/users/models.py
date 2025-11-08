from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from typing import Any

class Profile(models.Model):
    """
    Модель профиля пользователя.

    Attributes:
        user (User): Связь один-к-одному с моделью User.
        image (ImageField): Изображение профиля. По умолчанию используется 'profile_pics/default.jpg'.
        bio (TextField): Текстовое поле с информацией о пользователе.
        is_approved (BooleanField): Провряет, подтвердил ли администратор регистрацию пользователя.

    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='profile_pics/default.jpg', upload_to='profile_pics')
    bio = models.TextField(max_length=500, blank=True, null=True, verbose_name="О себе")
    is_approved = models.BooleanField(default=False, verbose_name="Подвтерждение администратором")

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['user']

    def __str__(self) -> str:
        """
        Возвращает строковое представление профиля.

        Returns:
            str: Учётная запись и имя пользователя.
        """
                
        return f'Учётная запись {self.user.username}'
    



@receiver(post_save, sender=User)
def create_profile(sender: Any, instance: User, created: bool, **kwargs: Any) -> None:
    """
    Сигнал для автоматического создания профиля при создании пользователя.

    Args:
        sender (Any): Модель, отправившая сигнал.
        instance (User): Экземпляр модели User.
        created (bool): Флаг, указывающий, был ли объект создан.
        **kwargs (Any): Дополнительные аргументы.
    """
        
    if created:
        Profile.objects.create(user=instance)




@receiver(post_save, sender=User)
def save_profile(sender: Any, instance: User, **kwargs: Any) -> None:
    """
    Сигнал для автоматического сохранения профиля при сохранении пользователя.
    

    Args:
        sender (Any): Модель, отправившая сигнал.
        instance (User): Экземпляр модели User.
        **kwargs (Any): Дополнительные аргументы.
    """

    profile = instance.profile
    profile.save()