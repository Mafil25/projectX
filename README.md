# ProjectX

Учебная платформа для изучения Python на Django: 10 уровней, по 5 заданий в каждом, редакторы кода на одной странице уровня, автоматическая проверка и личный прогресс.

Проект проверен с Python 3.15. Зависимости перечислены в `projectX/projectX/requirements.txt`.

## Запуск на Windows (PowerShell)

Нужны установленные Python и Git. Выполните:

```powershell
git clone https://github.com/Mafil25/projectX.git
cd projectX
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r projectX\projectX\requirements.txt
```

Создайте собственный `.env` в корне репозитория:

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from django.core.management.utils import get_random_secret_key; Path('.env').write_text('SECRET_KEY=' + get_random_secret_key() + '\n', encoding='utf-8')"
```

Пример переменных находится в `.env.example`. Затем создайте базу, загрузите уровни и задания и создайте администратора:

```powershell
cd projectX\projectX
..\..\.venv\Scripts\python.exe manage.py migrate
..\..\.venv\Scripts\python.exe manage.py loaddata course
..\..\.venv\Scripts\python.exe manage.py createsuperuser
..\..\.venv\Scripts\python.exe manage.py runserver
```

Сайт: http://127.0.0.1:8000/

Админка: http://127.0.0.1:8000/admin/

В терминале символы вводимого пароля администратора не отображаются — это нормально.

## Уровни и задания

Файл `projectX/projectX/task/fixtures/course.json` содержит все 10 уровней, 50 заданий и их тесты. Загружайте его при первом запуске на новой базе. Аккаунты и личный прогресс в этот файл не включены.

В админке откройте **Levels**, выберите уровень и добавьте задания внизу страницы. Для проверки функции задайте её имя, начальный код и тесты:

```json
[{"input": [2, 3], "expected": 5}]
```

Для программы с `input()` / `print()` оставьте имя функции пустым и используйте:

```json
[{"input": "2 3", "output": "5"}]
```

Monaco Editor и Python/Pyodide загружаются из CDN, поэтому для их загрузки нужен интернет. Если Monaco недоступен, используется обычное поле для кода.

## Проверка проекта

Из папки с `manage.py`:

```powershell
..\..\.venv\Scripts\python.exe manage.py test
```

Пароли, локальная база, виртуальное окружение и резервные копии исключены из новых коммитов через `.gitignore`.
