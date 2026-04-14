@echo off
cd /d C:\xampp\htdocs\aiinterview
set DB_BACKEND=sqlite

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 app.py
    goto :end
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
    python app.py
    goto :end
)

echo Python not found. Please install Python 3 and retry.
:end
pause
