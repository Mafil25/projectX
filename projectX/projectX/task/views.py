import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView

from .models import Level, Task, TaskProgress


def level_context(level, user):
    tasks = list(level.tasks.order_by('number', 'pk'))
    completed_ids = set(TaskProgress.objects.filter(
        user=user,
        task__level=level,
        is_completed=True,
    ).values_list('task_id', flat=True))
    for task in tasks:
        task.is_completed = task.pk in completed_ids
        first_test = task.tests[0] if isinstance(task.tests, list) and task.tests and isinstance(task.tests[0], dict) else {}
        task.initial_input = (
            json.dumps(first_test.get('input', []), ensure_ascii=False)
            if task.function_name else first_test.get('input', '')
        )
    return {
        'level': level,
        'tasks': tasks,
        'completed_tasks': len(completed_ids),
        'total_tasks': len(tasks),
        'progress_percent': len(completed_ids) * 100 // len(tasks) if tasks else 0,
        'is_completed': bool(tasks) and len(completed_ids) == len(tasks),
    }


class LevelDetailView(LoginRequiredMixin, DetailView):
    login_url = 'log'
    model = Level
    template_name = 'task/level.html'
    context_object_name = 'level'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(level_context(self.object, self.request.user))
        context['task_configs'] = [{
            'id': task.pk,
            'functionName': task.function_name,
            'starterCode': task.starter_code,
            'tests': task.tests,
            'completeUrl': reverse('task_complete', args=[task.pk]),
        } for task in context['tasks']]
        return context


class TaskDetailView(LoginRequiredMixin, View):
    """Keep existing exercise links pointing at their section in the level."""
    login_url = 'log'

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        return redirect(f"{reverse('level_detail', args=[task.level_id])}#task-{task.pk}")


class TaskCompleteView(LoginRequiredMixin, View):
    """Учебный режим: клиентскую проверку можно подделать.

    Для защищённого оценивания необходим независимый серверный runner.
    """
    login_url = 'log'

    def post(self, request, pk):
        task = get_object_or_404(Task.objects.select_related('level'), pk=pk)

        try:
            data = json.loads(request.body)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Неверный JSON'}, status=400)

        if not isinstance(data, dict) or data.get('passed') is not True:
            return JsonResponse({'error': 'Задание не выполнено'}, status=400)

        if not task.tests or not isinstance(task.tests, list):
            return JsonResponse({'error': 'Для задания не заданы тесты'}, status=400)

        progress, _ = TaskProgress.objects.get_or_create(
            user=request.user,
            task=task
        )
        if not progress.is_completed:
            progress.is_completed = True
            progress.save(update_fields=['is_completed'])

        context = level_context(task.level, request.user)
        return JsonResponse({
            'success': True,
            'message': 'Прогресс сохранён',
            'completed_task_ids': [item.pk for item in context['tasks'] if item.is_completed],
            'completed_tasks': context['completed_tasks'],
            'total_tasks': context['total_tasks'],
            'is_completed': context['is_completed'],
        })
