from django.db import models


class Quiz(models.Model):
  name = models.CharField(max_length=300)

  class Meta:
    verbose_name = "Тест" # Как будет отображаться в админ панели
    verbose_name_plural = "Тесты" # Отображаться в множественном числе
    ordering = ['name']

    indexes = [models.Index(fields=['name'], name='name_idx')]

  def __str__(self):
    return f"{self.name}" # Так будет отображаться в админ панели

class Question(models.Model):
  SINGLE = 'single'
  MULTIPLE = 'multiple'
  QUESTION_TYPES = [
      (SINGLE, 'Один правильный ответ'),
      (MULTIPLE, 'Несколько правильных ответов'),
  ]

  quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
  text = models.CharField(max_length=300)
  question_type = models.CharField(
      max_length=10,
      choices=QUESTION_TYPES,
      default=SINGLE
  )

  class Meta:
    verbose_name = "Вопрос"
    verbose_name_plural = "Вопросы"

  def __str__(self):
    return f"Вопрос {self.text} из теста: {self.quiz}"

class Answer(models.Model):
  question = models.ForeignKey(Question, on_delete=models.CASCADE)
  text = models.CharField(max_length=300)
  is_correct = models.BooleanField(default=False)

  class Meta:
    verbose_name = "Ответ"
    verbose_name_plural = "Ответы"

  def __str__(self):
    return f"Ответ к вопросу: {self.question}"
  
