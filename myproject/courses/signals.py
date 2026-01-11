from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User


@receiver(m2m_changed, sender=User.groups.through)
def assign_courses_on_group_change(sender, instance, action, pk_set, **kwargs):
    """
    Сигнал, который срабатывает при изменении групп пользователя.
    При добавлении пользователя в группу - назначает ему все курсы этой группы.
    """
    # Реагируем только на добавление в группу (post_add)
    if action == 'post_add' and pk_set:
        from courses.models import Course
        from myapp.models import UserCourse
        
        # Получаем все курсы, назначенные добавленным группам
        courses = Course.objects.filter(assigned_groups__id__in=pk_set).distinct()
        
        # Назначаем курсы пользователю
        for course in courses:
            UserCourse.objects.get_or_create(
                user=instance,
                course=course
            )
