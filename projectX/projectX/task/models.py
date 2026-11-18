from django.db import models
from django.conf import settings


class Level(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    number = models.PositiveIntegerField(unique=True)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return self.title


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    number = models.PositiveIntegerField()

    function_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Имя проверяемой функции, например add. Оставьте пустым для проверки input()/print().',
    )
    starter_code = models.TextField(
        blank=True,
        default='',
        help_text='Начальный код в редакторе, например заготовка функции.',
    )

    tests = models.JSONField(
        default=list,
        help_text='Для input/print: [{"input": "2 3", "output": "5"}]. Для функции: [{"input": [2, 3], "expected": 5}].',
    )

    level = models.ForeignKey(
        Level,
        on_delete=models.PROTECT,
        related_name='tasks',
    )

    def __str__(self):
        return self.title

class TaskProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_progress'
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='user_progres'
    )

    is_completed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'task'],
                name='unique_user_task'
            )
        ]

    def __str__(self):
        return f'{self.user} — {self.task}'
