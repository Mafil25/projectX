from django.urls import path

from . import views

urlpatterns = [
    path('<int:pk>', views.TaskDetailView.as_view(), name="task"),
]
