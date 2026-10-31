Исправления проекта:
- Кнопка «Запустить» исполняет Python через Pyodide в браузере.
- Кнопка «Проверить» сравнивает результат Python с Task.tests.
- Прогресс TaskProgress сохраняется через POST на task_complete.
- Убрана зависимость от Judge0 (task/services.py).
- Сохранены исходные страницы, изображения, БД и оформление.

Запуск:
  python -m pip install django
  python manage.py migrate
  python manage.py runserver

Заполни Task.tests JSON-массивом объектов {"input":"2 3\n","output":"5"}.
Первоначальная загрузка Pyodide требует доступа в интернет (CDN).
ВНИМАНИЕ: тесты и passed:true в браузере поддаются подделке.
Для защищённых экзаменов требуется независимая серверная проверка.
