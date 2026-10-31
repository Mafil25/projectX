from django.db import models
from django.conf import settings

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    number = models.PositiveIntegerField()

    tests = models.JSONField(default=list)

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
