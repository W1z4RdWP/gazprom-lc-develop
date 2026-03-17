# Generated manually for unique (course-only) lessons

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0013_lessonattachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='course_only',
            field=models.BooleanField(
                default=False,
                help_text='Урок существует только внутри курса и не отображается в базе знаний',
                verbose_name='Только для курса'
            ),
        ),
    ]
