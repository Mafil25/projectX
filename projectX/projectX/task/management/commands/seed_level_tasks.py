from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from task.course_catalog import COURSE_CATALOG
from task.models import Level, Task


class Command(BaseCommand):
    help = 'Добавить по пять заданий к десяти исходным уровням, сохраняя существующие задания.'

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for specification in COURSE_CATALOG:
            try:
                level = Level.objects.get(title=specification['title'])
            except (Level.DoesNotExist, Level.MultipleObjectsReturned) as error:
                raise CommandError(f"Не найден единственный уровень «{specification['title']}».") from error
            for number, content in enumerate(specification['tasks'], start=1):
                task, is_new = Task.objects.get_or_create(
                    level=level,
                    number=number,
                    defaults=content,
                )
                if not is_new and (task.title != content['title'] or task.function_name != content['function_name']):
                    raise CommandError(f'В уровне «{level}» номер {number} уже занят другим заданием. Данные не изменены.')
                created += is_new
        self.stdout.write(self.style.SUCCESS(f'Добавлено заданий: {created}.'))
