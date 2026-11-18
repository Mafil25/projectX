from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


class RegistrationValidationTests(TestCase):
    def register(self, **changes):
        data = {
            'username': 'newstudent',
            'group': 'ПИ-21',
            'email': 'learner@example.org',
            'password': 'vT8!zQ',
        }
        data.update(changes)
        return self.client.post(reverse('reg'), data)

    def assert_rejected(self, response, field, code):
        self.assertEqual(response.status_code, 200)
        errors = response.context['form'].errors.as_data()
        self.assertIn(code, [error.code for error in errors[field]])
        self.assertFalse(get_user_model().objects.filter(username='newstudent').exists())

    def test_malformed_email_is_rejected_on_server(self):
        for email in ['without-at', 'user@', '@example.org', 'user@@example.org', 'user@example', 'user name@example.org']:
            with self.subTest(email=email):
                response = self.register(email=email)
                self.assert_rejected(response, 'email', 'invalid')
                self.assertContains(response, 'Введите корректную почту в формате name@example.com.')
                self.assertNotIn('password', response.context['form'].errors)

    def test_required_email_and_password_have_specific_errors(self):
        response = self.register(email='', password='')
        self.assert_rejected(response, 'email', 'required')
        self.assert_rejected(response, 'password', 'required')
        self.assertContains(response, 'Введите почту.')
        self.assertContains(response, 'Введите пароль.')

    def test_five_character_password_is_rejected(self):
        response = self.register(password='vT8!z')
        self.assert_rejected(response, 'password', 'password_too_short')
        self.assertContains(response, 'Пароль должен содержать не менее 6 символов.')

    def test_six_character_password_is_accepted_and_hashed(self):
        response = self.register()
        self.assertRedirects(response, reverse('log'))
        user = get_user_model().objects.get(username='newstudent')
        self.assertTrue(user.check_password('vT8!zQ'))
        self.assertNotEqual(user.password, 'vT8!zQ')
        self.assertEqual(user.email, 'learner@example.org')
        self.assertEqual(user.user_group, 'ПИ-21')

    def test_common_numeric_and_whitespace_passwords_are_rejected(self):
        for password, code in [
            ('password', 'password_too_common'),
            ('918273645', 'password_entirely_numeric'),
            ('      ', 'password_only_whitespace'),
        ]:
            with self.subTest(code=code):
                self.assert_rejected(self.register(password=password), 'password', code)

    def test_password_matching_username_or_email_is_allowed(self):
        for username, email, password in [
            ('myIdentityQ7', 'learner@example.org', 'myIdentityQ7'),
            ('otherpersonQ8', 'emailIdentityQ7@example.org', 'emailIdentityQ7'),
        ]:
            with self.subTest(username=username):
                response = self.register(username=username, email=email, password=password)
                self.assertRedirects(response, reverse('log'))
                self.assertTrue(get_user_model().objects.get(username=username).check_password(password))

    def test_passphrases_are_allowed_without_forced_character_mix(self):
        response = self.register(password='orchid river comet lantern')
        self.assertRedirects(response, reverse('log'))
        self.assertTrue(get_user_model().objects.get(username='newstudent').check_password('orchid river comet lantern'))

    def test_password_spaces_are_not_silently_trimmed(self):
        password = '  vT8!zQ  '
        self.assertRedirects(self.register(password=password), reverse('log'))
        user = get_user_model().objects.get(username='newstudent')
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.check_password(password.strip()))

    def test_both_field_errors_are_shown_and_other_values_preserved(self):
        response = self.register(email='bad-address', password='vT8!z')
        self.assert_rejected(response, 'email', 'invalid')
        self.assert_rejected(response, 'password', 'password_too_short')
        self.assertContains(response, 'data-field-error="email"')
        self.assertContains(response, 'data-field-error="password"')
        self.assertContains(response, 'value="newstudent"')
        self.assertContains(response, 'value="ПИ-21"')
        self.assertContains(response, 'value="bad-address"')
        self.assertNotContains(response, 'value="vT8!z"')

    def test_valid_email_plus_address_is_accepted(self):
        self.assertRedirects(self.register(email='learner+python@example.org'), reverse('log'))

    def test_duplicate_username_still_uses_existing_general_error(self):
        get_user_model().objects.create_user(username='newstudent')
        response = self.register()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['message'])
        self.assertEqual(get_user_model().objects.filter(username='newstudent').count(), 1)

    def test_existing_login_does_not_apply_registration_password_rules(self):
        get_user_model().objects.create_user(username='existing', password='123')
        response = self.client.post(reverse('log'), {'username': 'existing', 'password': '123'})
        self.assertRedirects(response, reverse('main'))
