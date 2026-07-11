$ErrorActionPreference = "Stop"

Write-Host "Building and starting Lab 1a..." -ForegroundColor Cyan
docker compose up --build -d

if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Lab started successfully." -ForegroundColor Green
Write-Host "Dashboard: http://localhost:8000"
Write-Host "Findings: output\findings.json"

Start-Sleep -Seconds 2
Start-Process "http://localhost:8000"
