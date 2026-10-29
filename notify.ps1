param(
    [string]$Title = 'Codex 한도 기준점 설정',
    [string]$Message = '5시간 한도 초기화 후 자동 요청을 보냈습니다.'
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
