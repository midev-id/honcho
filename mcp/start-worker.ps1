$root = "C:\Users\MAHDI\Documents\Autopreneur\honcho-server\mcp"
$logDir = Join-Path $root "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
Set-Location $root
$env:CI = "true"
& "$env:USERPROFILE\.bun\bin\bun.exe" run dev 2>&1 | Out-File -FilePath (Join-Path $logDir "worker.log") -Encoding utf8
