Monaco Editor + Django + Pyodide
================================
1. Install dependencies: python -m pip install -r requirements.txt
2. Apply migrations if needed: python manage.py migrate
3. Start Django: python manage.py runserver
4. Open an existing task while logged in.

Monaco loads from cdnjs.cloudflare.com; Pyodide loads from cdn.jsdelivr.net.
An internet connection is required on the first load. If Monaco is unavailable,
the editor falls back to a plain textarea.

Changed files:
- task/templates/task/page-1.html
- task/static/task/css/page-1_style.css

The Pyodide execution Worker, Django models, routes and database are kept unchanged.
Browser test results are not cryptographically trusted; client-side completion
can be forged and is not suitable for graded exams.
