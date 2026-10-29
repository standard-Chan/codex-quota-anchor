param(
    [string]$Title = 'Codex quota window anchored',
    [string]$Message = 'The automatic request was sent successfully. The next 5-hour window has started.'
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$icon = New-Object System.Windows.Forms.NotifyIcon
try {
    $icon.Icon = [System.Drawing.SystemIcons]::Information
    $icon.Visible = $true
    $icon.ShowBalloonTip(10000, $Title, $Message, [System.Windows.Forms.ToolTipIcon]::Info)
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Seconds 10
}
finally {
    $icon.Visible = $false
    $icon.Dispose()
}
