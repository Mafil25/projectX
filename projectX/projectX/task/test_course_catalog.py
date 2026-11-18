import ast
import io
import json
from pathlib import Path
import re

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .course_catalog import COURSE_CATALOG
from .models import Level, Task, TaskProgress


# Independent reference solutions used only by tests, never sent to the editor.
REFERENCE_SOURCE = '''
import math
from collections import Counter

def add(a, b): return a + b
def add_three(a, b, c): return a + b + c
def sum_digits(n): return sum(map(int, str(abs(n))))
def sum_range(a, b): return sum(range(min(a, b), max(a, b) + 1))
def sum_multiples(n, k): return sum(range(k, n + 1, k))

def is_even(n): return n % 2 == 0
def parity_label(n): return 'even' if n % 2 == 0 else 'odd'
def count_even(numbers): return sum(n % 2 == 0 for n in numbers)
def even_numbers(numbers): return [n for n in numbers if n % 2 == 0]
def same_parity(a, b): return a % 2 == b % 2

def find_max(a, b, c): return max(a, b, c)
def max_list(numbers): return max(numbers)
def max_absolute(numbers): return max(map(abs, numbers))
def index_of_max(numbers): return numbers.index(max(numbers)) if numbers else -1
def second_largest(numbers):
    distinct = sorted(set(numbers))
    return distinct[-2] if len(distinct) > 1 else None

def sum_list(numbers): return sum(numbers)
def sum_positive(numbers): return sum(n for n in numbers if n > 0)
def sum_even_positions(numbers): return sum(numbers[::2])
def prefix_sums(numbers): return [sum(numbers[:i + 1]) for i in range(len(numbers))]
def max_window_sum(numbers, k): return max(sum(numbers[i:i + k]) for i in range(len(numbers) - k + 1))

def factorial(n): return math.factorial(n)
def factorials_up_to(n): return [math.factorial(i) for i in range(n + 1)]
def trailing_zeros(n):
    zeros = 0
    while n:
        n //= 5
        zeros += n
    return zeros
def permutations(n, k): return math.perm(n, k)
def combinations(n, k): return math.comb(n, k)

def is_palindrome(text): return text == text[::-1]
def normalized_palindrome(text):
    cleaned = ''.join(ch for ch in text if ch.isalnum()).lower()
    return cleaned == cleaned[::-1]
def is_number_palindrome(n): return n >= 0 and str(n) == str(n)[::-1]
def palindrome_words(words): return [word for word in words if word == word[::-1]]
def longest_palindrome(text):
    candidates = [text[i:j] for i in range(len(text)) for j in range(i + 1, len(text) + 1)
                  if text[i:j] == text[i:j][::-1]]
    return max(candidates, key=len, default='')

def remove_duplicates(numbers): return list(dict.fromkeys(numbers))
def count_duplicates(numbers): return len(numbers) - len(set(numbers))
def unique_once(numbers):
    counts = Counter(numbers)
    return [n for n in numbers if counts[n] == 1]
def has_duplicates(numbers): return len(numbers) != len(set(numbers))
def intersection_unique(first, second): return [n for n in dict.fromkeys(first) if n in set(second)]

def char_count(text): return dict(Counter(text))
def most_frequent_char(text): return max(text, key=text.count) if text else ''
def count_letters(text): return dict(Counter(ch.lower() for ch in text if ch.isalpha()))
def first_unique_char(text): return next((ch for ch in text if text.count(ch) == 1), '')
def word_count(text): return dict(Counter(text.lower().split()))

def is_prime(n): return n > 1 and all(n % divisor for divisor in range(2, math.isqrt(n) + 1))
def primes_up_to(n): return [value for value in range(2, n + 1) if is_prime(value)]
def count_primes(a, b): return sum(is_prime(value) for value in range(min(a, b), max(a, b) + 1))
def next_prime(n):
    value = max(2, n + 1)
    while not is_prime(value): value += 1
    return value
def prime_factors(n):
    factors = []
    divisor = 2
    while divisor * divisor <= n:
        while n % divisor == 0:
            factors.append(divisor)
            n //= divisor
        divisor += 1
    if n > 1: factors.append(n)
    return factors

def _pairs(numbers): return ((i, j) for j in range(1, len(numbers)) for i in range(j))
def two_sum(numbers, target):
    return next(([i, j] for i, j in _pairs(numbers) if numbers[i] + numbers[j] == target), [])
def has_pair(numbers, target): return any(numbers[i] + numbers[j] == target for i, j in _pairs(numbers))
def count_pairs(numbers, target): return sum(numbers[i] + numbers[j] == target for i, j in _pairs(numbers))
def pair_values(numbers, target): return [numbers[index] for index in two_sum(numbers, target)]
def closest_pair(numbers, target):
    if len(numbers) < 2: return []
    return list(min(_pairs(numbers), key=lambda pair: (abs(numbers[pair[0]] + numbers[pair[1]] - target), pair[1], pair[0])))
'''


class FunctionRunnerTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        source = (Path(__file__).parent / 'static/task/js/python-worker.js').read_text(encoding='utf-8')
        python = re.search(r'runPythonAsync\(`(.*?)`\)', source, re.DOTALL).group(1)
        tree = ast.parse(python)
        cls.worker_code = compile(ast.Module(body=tree.body[:-1], type_ignores=[]), '<worker>', 'exec')
        cls.worker_result = compile(ast.Expression(tree.body[-1].value), '<worker-result>', 'eval')

    def run_solution(self, code, arguments, function_name=''):
        namespace = {'USER_CODE': code, 'TEST_INPUT': arguments, 'FUNCTION_NAME': function_name}
        exec(self.worker_code, namespace)
        return eval(self.worker_result, namespace)

    def test_every_catalog_case_with_worker_python(self):
        self.assertEqual(len(COURSE_CATALOG), 10)
        names = set()
        for level in COURSE_CATALOG:
            self.assertEqual(len(level['tasks']), 5)
            for task in level['tasks']:
                name = task['function_name']
                self.assertNotIn(name, names)
                names.add(name)
                self.assertGreaterEqual(len(task['tests']), 6)
                self.assertIn(f'def {name}(', task['starter_code'])
                for case in task['tests']:
                    with self.subTest(function=name, arguments=case['input']):
                        result = json.loads(self.run_solution(REFERENCE_SOURCE, json.dumps(case['input']), name))
                        self.assertEqual(type(result), type(case['expected']))
                        self.assertEqual(result, case['expected'])

    def test_print_does_not_replace_return(self):
        result = self.run_solution('def add(a, b):\n    print(a + b)', '[2, 3]', 'add')
        self.assertIsNone(json.loads(result))

    def test_missing_function_is_reported(self):
        with self.assertRaisesRegex(ValueError, 'add'):
            self.run_solution('value = 5', '[2, 3]', 'add')

    def test_function_arguments_must_be_array(self):
        with self.assertRaises(ValueError):
            self.run_solution('def add(a, b): return a + b', '{"a": 2}', 'add')

    def test_function_exceptions_are_not_accepted(self):
        with self.assertRaises(ZeroDivisionError):
            self.run_solution('def add(a, b): return 1 / 0', '[2, 3]', 'add')

    def test_standard_input_output_still_works(self):
        result = self.run_solution('a, b = map(int, input().split())\nprint(a + b)', '2 3')
        self.assertEqual(result.strip(), '5')


class CourseSeedingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for specification in COURSE_CATALOG:
            Level.objects.create(title=specification['title'], number=specification['number'])

    def seed(self):
        call_command('seed_level_tasks', stdout=io.StringIO())

    def test_fifty_tasks_and_repeat_preserves_changes_and_progress(self):
        self.seed()
        self.assertEqual(Task.objects.count(), 50)
        for level in Level.objects.all():
            self.assertEqual(list(level.tasks.order_by('number').values_list('number', flat=True)), [1, 2, 3, 4, 5])
        task = Task.objects.first()
        task.description = 'Изменённое в админке условие'
        task.save(update_fields=['description'])
        user = get_user_model().objects.create_user(username='learner')
        TaskProgress.objects.create(task=task, user=user, is_completed=True)
        self.seed()
        task.refresh_from_db()
        self.assertEqual(task.description, 'Изменённое в админке условие')
        self.assertEqual(Task.objects.count(), 50)
        self.assertTrue(TaskProgress.objects.get(user=user, task=task).is_completed)

    def test_conflicting_existing_task_is_not_overwritten(self):
        from django.core.management.base import CommandError
        existing = Task.objects.create(level=Level.objects.first(), number=1, title='Моё задание')
        with self.assertRaises(CommandError):
            self.seed()
        self.assertEqual(Task.objects.count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.title, 'Моё задание')

    def test_function_editor_has_starter_and_example_arguments(self):
        self.seed()
        user = get_user_model().objects.create_user(username='learner')
        self.client.force_login(user)
        task = Task.objects.get(function_name='add')
        response = self.client.get(reverse('level_detail', args=[task.level_id]))
        self.assertEqual(response.context['tasks'][0].initial_input, '[2, 3]')
        self.assertContains(response, 'Аргументы функции (JSON-массив)')
        self.assertContains(response, 'def add(a, b):')

    def test_all_ten_levels_show_five_editors_on_one_page(self):
        self.seed()
        user = get_user_model().objects.create_user(username='learner')
        self.client.force_login(user)
        for level in Level.objects.all():
            with self.subTest(level=level.title):
                response = self.client.get(reverse('level_detail', args=[level.pk]))
                self.assertContains(response, 'data-task-panel=', count=5)
                self.assertContains(response, 'data-code-editor', count=5)
                self.assertContains(response, 'data-code-fallback', count=5)
                self.assertContains(response, 'data-check', count=5)
                self.assertEqual(len(response.context['task_configs']), 5)
