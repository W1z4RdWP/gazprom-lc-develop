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