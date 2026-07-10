$ErrorActionPreference = "Stop"

$py = "C:\Users\Администратор\AppData\Local\Programs\Python\Python311\python.exe"

Write-Host "Creating virtual environment..."
& $py -m venv .venv

if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "Virtual environment created. Installing dependencies..."
    & ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"
    
    Write-Host "Removing old manual migration..."
    if (Test-Path "alembic\versions\001_initial_movies_categories.py") {
        Remove-Item -Force "alembic\versions\001_initial_movies_categories.py"
    }
    
    Write-Host "Generating Alembic migration..."
    & ".\.venv\Scripts\alembic.exe" revision --autogenerate -m "initial movies and categories"
    
    Write-Host "Upgrading database..."
    & ".\.venv\Scripts\alembic.exe" upgrade head
    
    Write-Host "Running tests..."
    & ".\.venv\Scripts\pytest.exe"
    
    Write-Host "Done!"
} else {
    Write-Error "Failed to create virtual environment. python.exe not found in .venv\Scripts."
}
