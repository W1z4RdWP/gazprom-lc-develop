from django.db import models
from django.db.models import Max
from django.contrib.auth.models import User
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

from unidecode import unidecode

from quizzes.models import Quiz

class Course(models.Model):
    """
    Модель представляющая таблицу myapp_course с курсами.

    Attrs:
        title (CharField) - заголовок курса
        description (TextField) - описание курса
        
    """
   
    title = models.CharField(max_length=200, verbose_name="Название курса")
    description = CKEditor5Field('Описание курса', config_name='noTablesImages')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    image = models.ImageField(upload_to='course_images/', blank=True, null=True, verbose_name="Изображение курса")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    directory = models.ForeignKey(
        'knowledge_base.Directory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name="Категория"
    )
    final_quiz = models.ForeignKey(
        Quiz,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Финальный тест"
    )
    quizzes = models.ManyToManyField(
        Quiz,
        related_name='courses',
        blank=True,
        verbose_name="Тесты курса"
    )

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_course_per_author'
            )
        ]


    def save(self, *args, **kwargs):
        if not self.slug:  # Генерируем slug только если он пустой
            transliterated_slug = unidecode(self.title)
            self.slug = slugify(transliterated_slug, allow_unicode=True)
            # Проверяем уникальность slug
            original_slug = self.slug
            counter = 1
            while Course.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    

class Lesson(models.Model):
    """
    Класс отвечающий за таблицу уроков в БД.
    Attrs:
        courses - ManyToMany связь с курсами, к которым относится урок.
        title - название урока.
        content - содержимое урока. Заполняется администратором сайта.
        video_id - идентификатор прикрепленного видео из рутуб. Максимальное количество символов для передачи в форму 
                    задается параметром max_length.
        directory - Внешний ключ на директорию базы знаний, к которой относится урок.
    """
    courses = models.ManyToManyField(Course, related_name='lessons', blank=True, verbose_name="Курсы")
    title = models.CharField(max_length=200, verbose_name="Название урока")
    content = CKEditor5Field('Content', config_name='extends')
    video_id = models.CharField(
        max_length=100, 
        verbose_name="ID видео с Rutube", 
        blank=True, 
        null=True,
        help_text="Пример: https://rutube.ru/video/VIDEO_ID/ - вводите только VIDEO_ID"
    )
    order = models.PositiveIntegerField(verbose_name="Порядок урока", default=0, blank=True)
    directory = models.ForeignKey(
        'knowledge_base.Directory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
        verbose_name="Категория"
    )


    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['order']

    def save(self, *args, **kwargs):
        # Автоматически вычисляем order, если он не указан или равен 0
        if not self.order or self.order == 0:
            if self.directory:
                # Если урок привязан к директории, берем максимальный order уроков этой директории
                max_order = Lesson.objects.filter(
                    directory=self.directory
                ).exclude(pk=self.pk).aggregate(
                    max_order=Max('order')
                )['max_order'] or 0
                self.order = max_order + 1
            else:
                # Если урок не привязан к директории
                max_order = Lesson.objects.filter(
                    directory__isnull=True
                ).exclude(pk=self.pk).aggregate(
                    max_order=Max('order')
                )['max_order'] or 0
                self.order = max_order + 1
        super().save(*args, **kwargs)

    def get_previous_lesson(self, course):
        """Получить предыдущий урок в конкретном курсе"""
        if not course:
            return None
        lessons_in_course = Lesson.objects.filter(courses=course, order__lt=self.order).order_by('-order')
        return lessons_in_course.first()

    def get_next_lesson(self, course):
        """Получить следующий урок в конкретном курсе"""
        if not course:
            return None
        lessons_in_course = Lesson.objects.filter(courses=course, order__gt=self.order).order_by('order')
        return lessons_in_course.first()

    def __str__(self):
        return self.title
    

class UserLessonTrajectory(models.Model):
    """
    Модель для хранения траектории прохождения курса для каждого пользователя.
    Связывает пользователя, курс и множество уроков, которые доступны этому пользователю.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="Курс")
    lessons = models.ManyToManyField(Lesson, verbose_name="Уроки в траектории")

    class Meta:
        verbose_name = 'Траектория уроков пользователя'
        verbose_name_plural = 'Траектории уроков пользователей'
        unique_together = ('user', 'course')

    def __str__(self):
        return f"Траектория {self.user.username} для {self.course.title}"