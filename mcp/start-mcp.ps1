$ErrorActionPreference = "Stop"
Set-Location "C:\Users\MAHDI\Documents\Autopreneur\honcho-server\mcp"
$env:PATH = "$env:USERPROFILE\.bun\bin;$env:PATH"
& "$env:USERPROFILE\.bun\bin\bun.exe" run dev
