from django import forms
from django.contrib.auth.password_validation import (
    CommonPasswordValidator,
    MinimumLengthValidator,
    NumericPasswordValidator,
    validate_password,
)
from django.core.exceptions import ValidationError

PASSWORD_VALIDATORS = [
    MinimumLengthValidator(min_length=6),
    CommonPasswordValidator(),
    NumericPasswordValidator(),
]
PASSWORD_ERRORS = {
    'password_too_short': 'Пароль должен содержать не менее 6 символов.',
    'password_too_common': 'Этот пароль слишком распространён. Придумайте другой.',
    'password_entirely_numeric': 'Пароль не должен состоять только из цифр.',
}


class RegistrationCredentialsForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'aria-describedby': 'email-errors',
            'aria-label': 'Почта',
        }),
        error_messages={
            'required': 'Введите почту.',
            'invalid': 'Введите корректную почту в формате name@example.com.',
            'max_length': 'Адрес почты должен содержать не более 254 символов.',
        },
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'minlength': 6,
            'aria-describedby': 'password-errors',
            'aria-label': 'Пароль',
        }),
        error_messages={'required': 'Введите пароль.'},
    )

    def clean_password(self):
        password = self.cleaned_data['password']
        if not password.strip():
            raise ValidationError('Пароль не может состоять только из пробелов.', code='password_only_whitespace')
        try:
            validate_password(password, password_validators=PASSWORD_VALIDATORS)
        except ValidationError as error:
            raise ValidationError([
                ValidationError(PASSWORD_ERRORS.get(item.code, item.message), code=item.code)
                for item in error.error_list
            ]) from error
        return password
