from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import Users


def reg(request):
    context = {
            'message' : 'Данный не соответстыуют требованиям формы или имя пользователя занято'
        }

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        if not username:
            return render(request, 'registration/registration.html', context)
        group = request.POST['group']
        email = request.POST['email']
        password = request.POST['password']

        
        if Users.objects.filter(username=username).exists():
            return render(request, 'registration/registration.html', context)
        else:
            Users.objects.create_user(username=username,
                               user_group=group,
                                email=email,
                                 password=password
                                 )
            return redirect('log')

    return render(request, 'registration/registration.html')


def log(request):
    context = {'message': 'Введены неверные данные для входа'}

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('main')
        return render(request, 'registration/log.html', context)

    return render(request, 'registration/log.html')