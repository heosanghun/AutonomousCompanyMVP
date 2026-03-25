$ErrorActionPreference = "Stop"

$taskNames = @(
  "AutonomousCompanyMVP-Worker",
  "AutonomousCompanyMVP-Monitoring"
)

foreach ($name in $taskNames) {
  if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    Write-Output "Removed task: $name"
  } else {
    Write-Output "Task not found: $name"
  }
}
