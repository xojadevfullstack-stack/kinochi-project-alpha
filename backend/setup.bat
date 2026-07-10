@echo off
set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"

echo Checking python...
"%PY%" --version
if errorlevel 1 exit /b %errorlevel%

echo Creating venv...
"%PY%" -m venv .venv
if errorlevel 1 exit /b %errorlevel%

echo Installing dev dependencies...
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
if errorlevel 1 exit /b %errorlevel%

echo Removing old migration...
del /F /Q alembic\versions\001_initial_movies_categories.py

echo Generating new migration...
.\.venv\Scripts\alembic.exe revision --autogenerate -m "initial movies and categories"
if errorlevel 1 exit /b %errorlevel%

echo Upgrading DB...
.\.venv\Scripts\alembic.exe upgrade head
if errorlevel 1 exit /b %errorlevel%

echo Running tests...
.\.venv\Scripts\pytest.exe
if errorlevel 1 exit /b %errorlevel%

echo All done successfully!
