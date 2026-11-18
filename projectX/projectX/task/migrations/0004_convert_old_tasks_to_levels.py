import django.db.models.deletion
from django.db import migrations, models


def convert_old_tasks_to_levels(apps, schema_editor):
    """Unassigned tasks were the original level cards, not exercises.

    Existing exercises that already belong to a level are left untouched.
    Old completion flags must not count as solving newly created exercises.
    Back up the database before applying this irreversible data conversion.
    """
    Task = apps.get_model('task', 'Task')
    Level = apps.get_model('task', 'Level')
    database = schema_editor.connection.alias
    old_levels = Task.objects.using(database).filter(level__isnull=True)
    used_numbers = set(Level.objects.using(database).values_list('number', flat=True))

    for old_level in old_levels.order_by('number', 'pk').iterator():
        number = old_level.number
        if number in used_numbers:
            number = max(used_numbers, default=0) + 1
        Level.objects.using(database).create(
            title=old_level.title,
            description=old_level.description,
            number=number,
        )
        used_numbers.add(number)

    # Cascades only the progress belonging to these former level records.
    old_levels.delete()


class Migration(migrations.Migration):
    dependencies = [('task', '0003_level_task_level')]

    operations = [
        migrations.RunPython(convert_old_tasks_to_levels),
        migrations.AlterField(
            model_name='task',
            name='level',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='tasks',
                to='task.level',
            ),
        ),
        migrations.AlterField(
            model_name='task',
            name='tests',
            field=models.JSONField(
                default=list,
                help_text='Список тестов: [{"input": "2 3", "output": "5"}]. Ввод и вывод — строки.',
            ),
        ),
    ]
