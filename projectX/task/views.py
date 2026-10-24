from django.shortcuts import render
from .models import TaskProgress, Task
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin


class TaskDetailView(LoginRequiredMixin, DetailView):
    login_url='log'
    model = Task
    template_name = 'task/page-1.html'
    context_object_name = 'task'
