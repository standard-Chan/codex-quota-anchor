$ErrorActionPreference = 'Stop'
$taskName = 'CodexQuotaAnchor'
$pythonCommand = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
}
if (-not $pythonCommand) {
    throw 'Python 3을 찾지 못했습니다. Python 설치 시 Add Python to PATH를 활성화한 뒤 다시 실행하세요.'
}
$python = $pythonCommand.Source
$script = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'anchor.py')).Path
$dataDirectory = Join-Path $env:LOCALAPPDATA 'CodexQuotaAnchor'
New-Item -ItemType Directory -Path $dataDirectory -Force | Out-Null

# 이전 버전이 저장소 폴더에 만든 상태와 로그가 있으면 사용자 데이터 폴더로 옮깁니다.
foreach ($fileName in @('state.json', 'events.jsonl')) {
    $oldPath = Join-Path $PSScriptRoot $fileName
    $newPath = Join-Path $dataDirectory $fileName
    if ((Test-Path -LiteralPath $oldPath) -and -not (Test-Path -LiteralPath $newPath)) {
        Move-Item -LiteralPath $oldPath -Destination $newPath
    }
}

$action = New-ScheduledTaskAction -Execute $python -Argument ('"' + $script + '" run') -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Write-Output "Installed $taskName"
Write-Output "Runtime data: $dataDirectory"


