from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.log, name="log"),
    path('reg', views.reg, name="reg"),
    path('main/', include("main.urls")),
]
