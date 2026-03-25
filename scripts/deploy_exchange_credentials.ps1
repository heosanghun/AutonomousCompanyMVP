$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$secPath = Join-Path $root "secrets\exchange_credentials.json"
if (!(Test-Path $secPath)) {
  Write-Error "Missing $secPath"
}

$json = Get-Content $secPath -Raw | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($json.EXCHANGE_API_KEY) -or [string]::IsNullOrWhiteSpace($json.EXCHANGE_API_SECRET)) {
  Write-Error "Invalid credentials file"
}

setx EXCHANGE_API_KEY $json.EXCHANGE_API_KEY | Out-Null
setx EXCHANGE_API_SECRET $json.EXCHANGE_API_SECRET | Out-Null
Write-Output "Exchange credentials persisted via setx. Restart shells to apply."
