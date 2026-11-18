from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import Users
from .forms import RegistrationCredentialsForm


def reg(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        group = request.POST.get('group', '')
        form = RegistrationCredentialsForm(request.POST)
        valid_credentials = form.is_valid()
        invalid_username = not username or Users.objects.filter(username=username).exists()
        if invalid_username or not valid_credentials:
            return render(request, 'registration/registration.html', {
                'form': form,
                'username': username,
                'group': group,
                'message': 'Данный не соответстыуют требованиям формы или имя пользователя занято' if invalid_username else '',
            })
        Users.objects.create_user(
            username=username,
            user_group=group,
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
        )
        return redirect('log')

    return render(request, 'registration/registration.html', {'form': RegistrationCredentialsForm()})


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
