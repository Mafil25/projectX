from django.shortcuts import render, redirect
from task.models import Task, TaskProgress
from django.contrib.auth.decorators import login_required


@login_required(login_url='log')
def main(request):

    count = TaskProgress.objects.filter(user=request.user, is_completed=True).count()
    total = Task.objects.count()
    all_tasks = Task.objects.all()


    context = {
        'completed_task' : count,
        'total_tasks' : total,
        'tasks' : all_tasks
    }

    return render(request, 'main/main.html', context)

