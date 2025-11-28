# PowerShell script to run the Streamlit app with virtual environment activated

Write-Host "🚀 Starting Thesis Panelist AI..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Check if activation worked
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "⚠️ Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🌐 Starting Streamlit app..." -ForegroundColor Yellow
Write-Host "   URL will open in your browser shortly..." -ForegroundColor Gray
Write-Host ""

# Run Streamlit
python -m streamlit run app.py

# Deactivate when done
deactivate
