$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$powershell = "powershell.exe"

$workerLauncher = Join-Path $scriptDir "start_worker.ps1"
$monitorLauncher = Join-Path $scriptDir "start_monitoring.ps1"

if (!(Test-Path $workerLauncher)) { throw "Missing $workerLauncher" }
if (!(Test-Path $monitorLauncher)) { throw "Missing $monitorLauncher" }

$workerAction = New-ScheduledTaskAction -Execute $powershell -Argument "-ExecutionPolicy Bypass -File `"$workerLauncher`""
$monitorAction = New-ScheduledTaskAction -Execute $powershell -Argument "-ExecutionPolicy Bypass -File `"$monitorLauncher`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable

try {
  Register-ScheduledTask -TaskName "AutonomousCompanyMVP-Worker" -Action $workerAction -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
  Register-ScheduledTask -TaskName "AutonomousCompanyMVP-Monitoring" -Action $monitorAction -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
} catch {
  Write-Output "Failed to register startup tasks (likely permission issue)."
  Write-Output "Please run PowerShell as Administrator and re-run this script."
  throw
}

Write-Output "Startup tasks installed:"
Write-Output "- AutonomousCompanyMVP-Worker"
Write-Output "- AutonomousCompanyMVP-Monitoring"
