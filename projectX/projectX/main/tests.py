from django.test import SimpleTestCase, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from task.models import Level, Task, TaskProgress


class HeadingHyphenationTests(SimpleTestCase):
    def test_russian_headings_keep_original_text_and_case(self):
        from .templatetags.text_filters import hyphenate_ru
        for heading in ['Факториал числа', 'Проверка палиндрома', 'Удаление повторяющихся элементов', 'Подсчёт символов в строке']:
            with self.subTest(heading=heading):
                result = hyphenate_ru(heading)
                self.assertIn('\u00ad', result)
                self.assertEqual(result.replace('\u00ad', ''), heading)

    def test_heading_filter_preserves_template_escaping(self):
        from django.template import Context, Template
        output = Template('{% load text_filters %}{{ title|hyphenate_ru }}').render(
            Context({'title': '<script>Факториал</script>'})
        )
        self.assertNotIn('<script>', output)
        self.assertIn('&lt;script&gt;', output)


class CourseProgressTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='learner')
        cls.other_user = get_user_model().objects.create_user(username='other')
        cls.level = Level.objects.create(title='Основы', number=1)
        cls.empty_level = Level.objects.create(title='Следующий уровень', number=2)
        cls.tasks = [Task.objects.create(
            level=cls.level, title=f'Задание {number}', description='Сложите числа',
            number=number, tests=[{'input': '2 3', 'output': '5'}],
        ) for number in range(1, 4)]

    def setUp(self):
        self.client.force_login(self.user)

    def test_empty_course_is_not_completed(self):
        Task.objects.all().delete()
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['overall_percent'], 0)
        self.assertEqual(response.context['total_tasks'], 0)
        self.assertEqual(response.context['completed_levels'], 0)
        self.assertContains(response, reverse('level_detail', args=[self.level.pk]))
        response = self.client.get(reverse('level_detail', args=[self.level.pk]))
        self.assertContains(response, 'В этом уровне пока нет заданий.')
        self.assertFalse(response.context['is_completed'])

    def test_completing_tasks_updates_level_and_overall_progress(self):
        for task in self.tasks[:2]:
            response = self.client.post(
                reverse('task_complete', args=[task.pk]),
                data={'passed': True}, content_type='application/json',
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('main'))
        self.assertEqual(response.context['completed_task'], 2)
        self.assertEqual(response.context['total_tasks'], 3)
        self.assertEqual(response.context['overall_percent'], 66)
        level = response.context['levels'][0]
        self.assertEqual(level.progress_percent, 66)
        self.assertFalse(level.is_completed)
        self.assertEqual(level.next_task.pk, self.tasks[2].pk)
        self.assertEqual(response.context['completed_levels'], 0)

        self.client.post(reverse('task_complete', args=[self.tasks[2].pk]),
                         data={'passed': True}, content_type='application/json')
        response = self.client.get(reverse('main'))
        self.assertEqual(response.context['overall_percent'], 100)
        self.assertEqual(response.context['completed_levels'], 1)
        self.assertTrue(response.context['levels'][0].is_completed)
        self.assertFalse(response.context['levels'][1].is_completed)
        self.assertContains(response, 'Завершён')
        response = self.client.get(reverse('level_detail', args=[self.level.pk]))
        self.assertContains(response, 'Уровень завершён')
        self.assertTrue(all(task.is_completed for task in response.context['tasks']))

    def test_repeat_completion_does_not_increment_progress(self):
        url = reverse('task_complete', args=[self.tasks[0].pk])
        for _ in range(2):
            self.client.post(url, data={'passed': True}, content_type='application/json')
        self.assertEqual(TaskProgress.objects.filter(user=self.user).count(), 1)

    def test_failed_submission_does_not_complete_task(self):
        response = self.client.post(
            reverse('task_complete', args=[self.tasks[0].pk]),
            data={'passed': False}, content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(TaskProgress.objects.filter(user=self.user).exists())

    def test_progress_is_specific_to_logged_in_user(self):
        TaskProgress.objects.create(user=self.other_user, task=self.tasks[0], is_completed=True)
        response = self.client.get(reverse('main'))
        self.assertEqual(response.context['completed_task'], 0)
        response = self.client.get(reverse('level_detail', args=[self.level.pk]))
        self.assertEqual(response.context['completed_tasks'], 0)
        self.assertFalse(any(task.is_completed for task in response.context['tasks']))

    def test_overall_progress_uses_all_tasks_not_level_averages(self):
        Task.objects.create(level=self.empty_level, title='Ещё задание', number=1)
        for task in self.tasks:
            TaskProgress.objects.create(user=self.user, task=task, is_completed=True)
        response = self.client.get(reverse('main'))
        self.assertEqual(response.context['overall_percent'], 75)
        self.assertEqual(response.context['completed_levels'], 1)

    def test_level_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('level_detail', args=[self.level.pk]))
        self.assertEqual(response.status_code, 302)
