$ErrorActionPreference = "Stop"

$destination = Join-Path $PSScriptRoot "mitre\enterprise-attack.json"
$url = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json"

Write-Host "Downloading the official MITRE ATT&CK Enterprise STIX bundle..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $url -OutFile $destination

if (-not (Test-Path $destination)) {
    throw "The ATT&CK file was not created."
}

$size = (Get-Item $destination).Length
Write-Host "Downloaded: $destination" -ForegroundColor Green
Write-Host "Size: $size bytes"
