# Codex 5시간 한도 기준점 도구

Codex의 5시간 사용 한도가 초기화된 뒤 사용률이 0%이면, 짧은 요청을 한 번 보내는 Windows용 도구입니다.

> 요청이 다음 5시간 주기의 기준점이 되는 동작은 OpenAI에서 공식적으로 보장하지 않습니다. 설치 후 실행 기록과 Codex의 다음 초기화 시각을 확인하세요.

## 만든 목적

Codex의 5시간 한도는 한도가 초기화된 뒤 첫 요청을 보낸 시점을 기준으로 다음 주기가 시작될 수 있습니다. 초기화 후 한동안 Codex를 사용하지 않으면 다음 초기화 시각도 늦어져 사용 가능한 시간대가 계속 달라질 수 있습니다.

이 도구는 초기화를 10분 간격으로 확인하고 짧은 요청을 자동으로 보내, 다음 5시간 주기의 기준점을 초기화 직후에 가깝게 유지하기 위해 만들었습니다.

## 준비 사항

- Windows 10 또는 Windows 11
- Python 3 (`python.exe` 또는 `pythonw.exe`가 PATH에 등록되어 있어야 함)
- Codex CLI 설치 및 ChatGPT 계정 로그인

다음 명령이 정상적으로 실행되는지 먼저 확인하세요.

```powershell
python --version
codex --version
codex login status
```

## 설치

저장소를 복제하거나 ZIP 파일을 내려받아 압축을 풉니다. PowerShell에서 내려받은 폴더로 이동한 뒤 설치 스크립트를 실행합니다.

```powershell
cd '내려받은 폴더 경로'
.\install.ps1
```

PowerShell 실행 정책 때문에 스크립트 실행이 차단되면 다음 명령으로 이번 설치에만 우회할 수 있습니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

`install.ps1`은 현재 폴더의 실제 경로를 자동으로 찾아 Windows 작업 스케줄러에 등록합니다. 사용자 이름이나 설치 위치를 코드에 직접 입력할 필요가 없습니다.

설치 후에는 컴퓨터를 켤 때마다 직접 실행할 필요가 없습니다. 저장소 폴더를 다른 위치로 옮겼다면 새 위치에서 `install.ps1`을 다시 실행하세요.

## 작동 방식

1. Windows 작업 스케줄러가 10분마다 `anchor.py run`을 실행합니다.
2. 기록된 초기화 시각 전이면 Codex에 연결하지 않고 종료합니다.
3. 초기화 시각이 지나면 현재 5시간 한도의 사용률을 조회합니다.
4. 사용률이 0%이면 읽기 전용의 짧은 Codex 요청을 한 번 보냅니다.
5. 요청이 성공하면 다음 초기화 시각을 저장하고 Windows 알림을 표시합니다.

사용자가 먼저 Codex를 사용했다면 자동 요청을 건너뛰고 다음 초기화를 기다립니다. 자동 요청 자체도 한도를 조금 사용합니다.

PC가 켜져 있고 Windows 계정에 로그인된 동안 실행됩니다. 화면 잠금 상태에서는 실행되지만, 종료 또는 절전 상태에서는 실행되지 않습니다. 다시 로그인하거나 절전에서 복귀하면 실행을 재개하므로 기준점이 늦어질 수 있습니다.

## 상태 및 기록 확인

PowerShell에서 저장소 폴더로 이동한 뒤 실행합니다.

```powershell
python .\anchor.py status
Get-ScheduledTaskInfo -TaskName CodexQuotaAnchor
Get-Content "$env:LOCALAPPDATA\CodexQuotaAnchor\events.jsonl" -Tail 10
.\notify.ps1
```

- `status`: 현재 한도와 다음 목표 시각을 조회합니다. 자동 요청은 보내지 않습니다.
- `events.jsonl`: 자동 요청과 알림 실행 기록입니다.
- `notify.ps1`: Windows 알림만 시험합니다.

상태와 로그는 저장소 안이 아닌 `%LOCALAPPDATA%\CodexQuotaAnchor`에 저장됩니다. 따라서 사용자별 기록이 Git에 포함되지 않고, 저장소를 어느 폴더에 복제해도 사용할 수 있습니다.

## 중지 및 제거

```powershell
Disable-ScheduledTask -TaskName CodexQuotaAnchor
Enable-ScheduledTask -TaskName CodexQuotaAnchor
.\uninstall.ps1
```

`uninstall.ps1`은 예약 작업만 제거합니다. 실행 기록도 지우려면 `%LOCALAPPDATA%\CodexQuotaAnchor` 폴더를 별도로 삭제하세요.

## GitHub에 올릴 때

`.gitignore`가 개인 상태, 로그, Python 캐시를 제외합니다. Codex 로그인 정보는 이 저장소에 저장하거나 복사하지 않습니다. `state.json`, `events.jsonl`, `__pycache__`가 커밋 대상에 포함되지 않았는지 확인한 뒤 공유하세요.
