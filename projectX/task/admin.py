from django.contrib import admin
from .models import Task, TaskProgress

admin.site.register(Task)

admin.site.register(TaskProgress)
