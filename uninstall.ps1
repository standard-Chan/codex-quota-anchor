$ErrorActionPreference = 'Stop'
Unregister-ScheduledTask -TaskName 'CodexQuotaAnchor' -Confirm:$false
Write-Output 'Removed CodexQuotaAnchor'

