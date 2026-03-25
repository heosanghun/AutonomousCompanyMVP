$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$python = "python"

$serverScript = Join-Path $scriptDir "monitoring_server.py"
$logPath = Join-Path $rootDir "outputs\\monitoring\\launcher.log"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $logPath) | Out-Null

Start-Process -FilePath $python -ArgumentList "`"$serverScript`"" -WorkingDirectory $rootDir -WindowStyle Hidden
"[$([DateTime]::UtcNow.ToString('o'))] monitoring_server_started" | Out-File -FilePath $logPath -Encoding utf8 -Append
Write-Output "Monitoring server started in background."
