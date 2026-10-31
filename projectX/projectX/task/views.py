import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView

from .models import Task, TaskProgress


class TaskDetailView(LoginRequiredMixin, DetailView):
    login_url = 'log'
    model = Task
    template_name = 'task/page-1.html'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['progress'] = TaskProgress.objects.filter(
            user=self.request.user,
            task=self.object
        ).first()
        return context


class TaskCompleteView(LoginRequiredMixin, View):
    """Учебный режим: клиентскую проверку можно подделать.

    Для защищённого оценивания необходим независимый серверный runner.
    """
    login_url = 'log'

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)

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

        return JsonResponse({'success': True, 'message': 'Прогресс сохранён'})
