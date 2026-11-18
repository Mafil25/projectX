from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from task.models import Level, Task, TaskProgress


@login_required(login_url='log')
def main(request):
    completed_ids = set(
        TaskProgress.objects.filter(
            user=request.user,
            is_completed=True,
        ).values_list('task_id', flat=True)
    )

    total_tasks = Task.objects.count()
    completed_task = len(completed_ids)

    overall_percent = (
        completed_task * 100 // total_tasks
        if total_tasks else 0
    )

    levels = list(
        Level.objects.prefetch_related('tasks')
    )

    for level in levels:
        tasks = sorted(
            level.tasks.all(),
            key=lambda task: (task.number, task.pk),
        )

        level.total_tasks = len(tasks)
        level.completed_tasks = sum(
            task.pk in completed_ids for task in tasks
        )

        level.progress_percent = (
            level.completed_tasks * 100 // level.total_tasks
            if level.total_tasks else 0
        )

        level.is_completed = (
            level.total_tasks > 0
            and level.completed_tasks == level.total_tasks
        )

        # Кнопка открывает первое нерешённое задание.
        # Если всё решено — первое задание для повторения.
        level.next_task = next(
            (
                task for task in tasks
                if task.pk not in completed_ids
            ),
            tasks[0] if tasks else None,
        )

    return render(request, 'main/main.html', {
        'completed_task': completed_task,
        'total_tasks': total_tasks,
        'overall_percent': overall_percent,
        'levels': levels,
        'completed_levels': sum(level.is_completed for level in levels),
        'total_levels': len(levels),
    })
