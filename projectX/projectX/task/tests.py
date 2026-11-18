from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Level, Task, TaskProgress


class LevelAdminTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_superuser(username='admin', password='test-password')
        self.client.force_login(user)

    def test_add_task_inside_level(self):
        response = self.client.post(reverse('admin:task_level_add'), {
            'title': 'Основы', 'description': 'Первый уровень', 'number': '1',
            'tasks-TOTAL_FORMS': '1', 'tasks-INITIAL_FORMS': '0',
            'tasks-MIN_NUM_FORMS': '0', 'tasks-MAX_NUM_FORMS': '1000',
            'tasks-0-title': 'Сумма', 'tasks-0-description': 'Сложите два числа',
            'tasks-0-number': '1',
            'tasks-0-tests': '[{"input": "2 3", "output": "5"}]',
            '_save': 'Сохранить',
        })
        self.assertEqual(response.status_code, 302)
        level = Level.objects.get(title='Основы')
        task = Task.objects.get(title='Сумма')
        self.assertEqual(task.level, level)
        self.assertEqual(task.tests, [{'input': '2 3', 'output': '5'}])


class TaskNavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='learner')
        cls.other = get_user_model().objects.create_user(username='other')
        cls.level = Level.objects.create(title='Первый уровень', number=1)
        cls.other_level = Level.objects.create(title='Другой уровень', number=2)
        cls.second = Task.objects.create(level=cls.level, title='Второе', number=2,
                                         tests=[{'input': '2 3', 'output': '5'}])
        cls.first = Task.objects.create(level=cls.level, title='Первое', number=1,
                                        tests=[{'input': '2 3', 'output': '5'}])
        cls.unrelated = Task.objects.create(level=cls.other_level, title='Чужое задание', number=1,
                                            tests=[{'input': '2 3', 'output': '5'}])

    def setUp(self):
        self.client.force_login(self.user)

    def test_sidebar_shows_only_current_level_in_number_order(self):
        TaskProgress.objects.create(user=self.user, task=self.first, is_completed=True)
        response = self.client.get(reverse('level_detail', args=[self.level.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([task.pk for task in response.context['tasks']], [self.first.pk, self.second.pk])
        self.assertTrue(response.context['tasks'][0].is_completed)
        self.assertFalse(response.context['tasks'][1].is_completed)
        self.assertContains(response, f'data-task-link="{self.first.pk}"')
        self.assertContains(response, f'data-task-link="{self.second.pk}"')
        self.assertContains(response, 'aria-current="location"', count=1)
        self.assertNotContains(response, f'data-task-link="{self.unrelated.pk}"')
        self.assertContains(response, f'href="#task-{self.second.pk}"')
        self.assertContains(response, 'data-code-fallback', count=2)
        self.assertContains(response, 'data-run', count=2)
        self.assertContains(response, 'data-check', count=2)
        self.assertNotContains(response, f'href="{reverse("task_detail", args=[self.second.pk])}"')

    def test_task_results_are_below_editor_without_progress_bar(self):
        response = self.client.get(reverse('level_detail', args=[self.level.pk]))
        html = response.content.decode()
        self.assertLess(html.index(f'id="python-code-{self.first.pk}"'), html.index('id="level-summary"'))
        self.assertLess(html.index(f'id="python-code-{self.second.pk}"'), html.index('id="level-summary"'))
        self.assertContains(response, 'id="level-completed-count">0</span>')
        self.assertNotContains(response, '<progress')

    def test_level_summary_follows_tasks_without_progress_bar(self):
        response = self.client.get(reverse('level_detail', args=[self.level.pk]))
        html = response.content.decode()
        self.assertLess(html.index('<div class="tasks">'), html.index('aria-label="Итоги уровня"'))
        self.assertContains(response, 'aria-label="Задания уровня"')
        self.assertNotContains(response, '<progress')

    def test_completion_response_updates_current_user_and_level_only(self):
        TaskProgress.objects.create(user=self.other, task=self.second, is_completed=True)
        TaskProgress.objects.create(user=self.user, task=self.unrelated, is_completed=True)
        response = self.client.post(reverse('task_complete', args=[self.first.pk]),
                                    data={'passed': True}, content_type='application/json')
        result = response.json()
        self.assertEqual(result['completed_task_ids'], [self.first.pk])
        self.assertEqual(result['completed_tasks'], 1)
        self.assertEqual(result['total_tasks'], 2)
        self.assertFalse(result['is_completed'])
        response = self.client.post(reverse('task_complete', args=[self.second.pk]),
                                    data={'passed': True}, content_type='application/json')
        result = response.json()
        self.assertEqual(result['completed_task_ids'], [self.first.pk, self.second.pk])
        self.assertEqual(result['completed_tasks'], 2)
        self.assertTrue(result['is_completed'])
        response = self.client.get(reverse('level_detail', args=[self.level.pk]))
        self.assertTrue(response.context['is_completed'])
        self.assertContains(response, '✓ Уровень завершён')

    def test_old_exercise_url_redirects_to_section_on_level_page(self):
        response = self.client.get(reverse('task_detail', args=[self.second.pk]))
        self.assertRedirects(response, f'{reverse("level_detail", args=[self.level.pk])}#task-{self.second.pk}')

    def test_each_editor_has_its_own_configuration(self):
        self.first.function_name = 'add'
        self.first.starter_code = 'def add(a, b):\n    pass'
        self.first.tests = [{'input': [2, 3], 'expected': 5}]
        self.first.save()
        response = self.client.get(reverse('level_detail', args=[self.level.pk]))
        first, second = response.context['task_configs']
        self.assertEqual(first['id'], self.first.pk)
        self.assertEqual(first['functionName'], 'add')
        self.assertEqual(first['tests'], [{'input': [2, 3], 'expected': 5}])
        self.assertEqual(first['completeUrl'], reverse('task_complete', args=[self.first.pk]))
        self.assertEqual(second['id'], self.second.pk)
        self.assertEqual(second['functionName'], '')
        self.assertEqual(second['tests'], [{'input': '2 3', 'output': '5'}])
        self.assertEqual(second['completeUrl'], reverse('task_complete', args=[self.second.pk]))
