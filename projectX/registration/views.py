from django.shortcuts import render


def reg(request):
    return render(request, 'registration/registration.html')


def log(request):
    return render(request, 'registration/log.html')
