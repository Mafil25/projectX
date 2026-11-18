from django.contrib import admin
from .models import Task, TaskProgress, Level


class TaskInline(admin.StackedInline):
    model = Task
    extra = 0
    fields = ('number', 'title', 'description', 'function_name', 'starter_code', 'tests')
    ordering = ('number', 'pk')
    show_change_link = True


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('number', 'title')
    search_fields = ('title',)
    inlines = [TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'number')
    list_filter = ('level',)
    search_fields = ('title', 'description')
    ordering = ('level__number', 'number', 'pk')
    list_select_related = ('level',)


@admin.register(TaskProgress)
class TaskProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'is_completed')
    list_filter = ('is_completed', 'task__level')
    list_select_related = ('user', 'task')
