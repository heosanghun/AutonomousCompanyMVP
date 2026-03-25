$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$python = "python"

$workerScript = Join-Path $scriptDir "autonomous_worker.py"
$logPath = Join-Path $rootDir "outputs\worker\launcher.log"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $logPath) | Out-Null

Start-Process -FilePath $python -ArgumentList "`"$workerScript`"" -WorkingDirectory $rootDir -WindowStyle Hidden
"[$([DateTime]::UtcNow.ToString('o'))] worker_started" | Out-File -FilePath $logPath -Encoding utf8 -Append
Write-Output "Autonomous worker started in background."
