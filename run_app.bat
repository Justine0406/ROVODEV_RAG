@echo off
echo ========================================
echo   Starting Thesis Panelist AI
echo ========================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Virtual environment activated!
echo.
echo Starting Streamlit app...
echo.

python -m streamlit run app.py

echo.
echo App closed.
pause
