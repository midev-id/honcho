$ErrorActionPreference = "Stop"
Set-Location "C:\Users\MAHDI\Documents\Autopreneur\honcho-server\mcp"
$env:PATH = "C:\Users\MAHDI\.bun\bin;$env:PATH"
& "C:\Users\MAHDI\.bun\bin\bun.exe" run dev
