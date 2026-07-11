$outputFile = Join-Path $PSScriptRoot "output\findings.json"

if (Test-Path $outputFile) {
    Remove-Item $outputFile -Force
    Write-Host "Removed output\findings.json" -ForegroundColor Yellow
} else {
    Write-Host "No generated findings file was found."
}
