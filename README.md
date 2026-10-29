# Codex 5시간 한도 기준점 도구

Codex의 5시간 사용 한도가 초기화된 뒤 사용률이 0%이면, 짧은 요청을 한 번 보내는 Windows 및 Linux용 도구입니다.

> 요청이 다음 5시간 주기의 기준점이 되는 동작은 OpenAI에서 공식적으로 보장하지 않습니다. 설치 후 실행 기록과 Codex의 다음 초기화 시각을 확인하세요.

## 만든 목적

Codex의 5시간 한도는 한도가 초기화된 뒤 첫 요청을 보낸 시점을 기준으로 다음 주기가 시작될 수 있습니다. 초기화 후 한동안 Codex를 사용하지 않으면 다음 초기화 시각도 늦어져 사용 가능한 시간대가 계속 달라질 수 있습니다.

이 도구는 초기화를 10분 간격으로 확인하고 짧은 요청을 자동으로 보내, 다음 5시간 주기의 기준점을 초기화 직후에 가깝게 유지하기 위해 만들었습니다.

## 지원 환경 및 준비 사항

- Windows 10/11 또는 systemd를 사용하는 Ubuntu/Debian
- Python 3
- Codex CLI 설치 및 ChatGPT 계정 로그인

다음 명령이 정상적으로 실행되는지 먼저 확인하세요.

```powershell
python --version  # Linux에서는 python3 --version
codex --version
codex login status
```

## Windows 설치

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

## Ubuntu/Debian 설치

공식 OpenAI 문서의 Linux 설치 명령으로 Codex CLI를 설치하고 로그인합니다.

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex
```

저장소 폴더에서 Linux 설치 스크립트를 실행합니다.

```bash
chmod +x install-linux.sh uninstall-linux.sh
./install-linux.sh
```

설치 스크립트는 현재 Python, Codex CLI 및 저장소의 절대경로를 찾아 systemd 사용자 서비스와 10분 타이머를 등록합니다. `sudo`는 필요하지 않습니다. 저장소 폴더를 옮겼다면 새 위치에서 `./install-linux.sh`을 다시 실행하세요.

데스크톱 알림을 사용하려면 `notify-send`가 필요합니다.

```bash
sudo apt update
sudo apt install libnotify-bin
```

GUI가 없는 서버에서는 자동 요청은 정상 동작하며 알림 실패만 로그에 남습니다.

## 파일 구조

```text
codex-quota-anchor/
├─ anchor.py       # 한도 조회, 자동 요청, 상태 저장을 담당하는 메인 프로그램
├─ install.ps1     # 10분 간격 Windows 예약 작업 설치 및 갱신
├─ uninstall.ps1   # Windows 예약 작업 제거
├─ notify.ps1      # 자동 요청 성공 후 Windows 알림 표시
├─ install-linux.sh    # systemd 사용자 서비스와 10분 타이머 설치
├─ uninstall-linux.sh  # Linux 서비스와 타이머 제거
├─ README.md       # 설치 및 사용 설명서
├─ .gitattributes  # 운영체제별 줄바꿈 형식 지정
└─ .gitignore      # 로그, 상태 파일, Python 캐시의 Git 업로드 제외

%LOCALAPPDATA%/CodexQuotaAnchor/
├─ state.json      # 다음 초기화 목표 시각과 마지막 자동 요청 시각
├─ events.jsonl    # 조회, 요청, 알림, 오류 기록
└─ run.lock        # 동시에 두 번 실행되는 것을 막는 잠금 파일

~/.local/state/codex-quota-anchor/  # Linux 기본 실행 데이터 위치
├─ state.json
├─ events.jsonl
└─ run.lock
```

위쪽은 GitHub에서 내려받는 프로그램 파일입니다. 아래쪽은 실행 중 각 사용자 PC에 자동으로 생성되는 개인 데이터이며 GitHub 저장소에는 포함되지 않습니다.

## 작동 방식

1. Windows 작업 스케줄러 또는 Linux systemd 사용자 타이머가 10분마다 `anchor.py run`을 실행합니다.
2. 기록된 초기화 시각 전이면 Codex에 연결하지 않고 종료합니다.
3. 초기화 시각이 지나면 현재 5시간 한도의 사용률을 조회합니다.
4. 사용률이 0%이면 읽기 전용의 짧은 Codex 요청을 한 번 보냅니다.
5. 요청이 성공하면 다음 초기화 시각을 저장하고 글자 깨짐을 방지하기 위해 영문 Windows 알림을 표시합니다.

사용자가 먼저 Codex를 사용했다면 자동 요청을 건너뛰고 다음 초기화를 기다립니다. 자동 요청 자체도 한도를 조금 사용합니다.

PC가 켜져 있고 사용자 세션이 실행되는 동안 동작합니다. 종료 또는 절전 상태에서는 실행되지 않으며, 다시 로그인하거나 절전에서 복귀하면 실행을 재개하므로 기준점이 늦어질 수 있습니다.

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

Linux에서는 `${XDG_STATE_HOME:-$HOME/.local/state}/codex-quota-anchor`에 저장됩니다. Linux 상태 확인 명령은 다음과 같습니다.

```bash
python3 ./anchor.py status
systemctl --user status codex-quota-anchor.timer
journalctl --user -u codex-quota-anchor.service -n 20
tail -n 20 "${XDG_STATE_HOME:-$HOME/.local/state}/codex-quota-anchor/events.jsonl"
```

## 중지 및 제거

```powershell
Disable-ScheduledTask -TaskName CodexQuotaAnchor
Enable-ScheduledTask -TaskName CodexQuotaAnchor
.\uninstall.ps1
```

`uninstall.ps1`은 예약 작업만 제거합니다. 실행 기록도 지우려면 `%LOCALAPPDATA%\CodexQuotaAnchor` 폴더를 별도로 삭제하세요.

Ubuntu/Debian에서는 다음 명령으로 systemd 사용자 서비스와 타이머를 제거합니다. 실행 기록은 그대로 남습니다.

```bash
./uninstall-linux.sh
```

## GitHub에 올릴 때

`.gitignore`가 개인 상태, 로그, Python 캐시를 제외합니다. Codex 로그인 정보는 이 저장소에 저장하거나 복사하지 않습니다. `state.json`, `events.jsonl`, `__pycache__`가 커밋 대상에 포함되지 않았는지 확인한 뒤 공유하세요.
