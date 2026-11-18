from django.urls import path
from . import views

urlpatterns = [
    path('level/<int:pk>/', views.LevelDetailView.as_view(), name='level_detail'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('<int:pk>/complete/', views.TaskCompleteView.as_view(), name='task_complete'),
]
