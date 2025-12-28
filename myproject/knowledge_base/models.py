from django.db import models

class Directory(models.Model):
    """Иерархическая модель папок/категорий базы знаний"""
    name = models.CharField(max_length=255, verbose_name='Название папки')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subdirectories',
        verbose_name='Родительская категория'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')
    description = models.TextField(blank=True, null=True, verbose_name='Описание категории')

    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['parent'], name='directory_parent_idx'),
        ]

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' / '.join(full_path[::-1])
    
    def get_courses_count(self):
        """Возвращает количество курсов в этой категории и подкатегориях"""
        from courses.models import Course
        count = Course.objects.filter(directory=self).count()
        for subdir in self.subdirectories.all():
            count += subdir.get_courses_count()
        return count
    
    def get_lessons_count(self):
        """Возвращает количество уроков в этой категории и подкатегориях"""
        from courses.models import Lesson
        count = Lesson.objects.filter(directory=self).count()
        for subdir in self.subdirectories.all():
            count += subdir.get_lessons_count()
        return count
    
    def get_quizzes_count(self):
        """Возвращает количество тестов в этой категории и подкатегориях"""
        from quizzes.models import Quiz
        count = Quiz.objects.filter(directory=self).count()
        for subdir in self.subdirectories.all():
            count += subdir.get_quizzes_count()
        return count