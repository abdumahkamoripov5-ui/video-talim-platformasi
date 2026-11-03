@echo off
echo Backend ishga tushmoqda...
cd /d "%~dp0"
venv\Scripts\python manage.py runserver 8000
pause
