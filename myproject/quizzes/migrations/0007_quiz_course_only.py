# Generated manually for unique (course-only) quizzes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0006_quiz_directory'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='course_only',
            field=models.BooleanField(
                default=False,
                help_text='Тест существует только внутри курса и не отображается в базе знаний',
                verbose_name='Только для курса'
            ),
        ),
    ]
