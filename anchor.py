"""Send one small Codex turn when the account's five-hour window resets."""

import argparse
import json
import os
import platform
import queue
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "CodexQuotaAnchor"
else:
    DATA_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "codex-quota-anchor"
STATE = DATA_DIR / "state.json"
LOG = DATA_DIR / "events.jsonl"
LOCK = DATA_DIR / "run.lock"
WINDOW = 300

DATA_DIR.mkdir(parents=True, exist_ok=True)


def stamp():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def log(event, **fields):
    with LOG.open("a", encoding="utf-8") as file:
        file.write(json.dumps({"at": stamp(), "event": event, **fields}, ensure_ascii=False) + "\n")


def codex_path():
    configured = os.environ.get("CODEX_QUOTA_CODEX_PATH")
    if configured and Path(configured).is_file():
        return configured
    found = shutil_which("codex")
    if found:
        return found
    if IS_WINDOWS:
        base = Path(os.environ.get("LOCALAPPDATA", "")) / "OpenAI" / "Codex" / "bin"
        files = list(base.glob("*/codex.exe"))
    else:
        files = [path for path in (Path.home() / ".local" / "bin" / "codex", Path("/usr/local/bin/codex")) if path.is_file()]
    if not files:
        raise RuntimeError("Codex CLI를 찾지 못했습니다.")
    return str(max(files, key=lambda file: file.stat().st_mtime))


def shutil_which(name):
    return shutil.which(name)


def read_limits():
    proc = subprocess.Popen(
        [codex_path(), "app-server"], cwd=HERE,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1,
    )
    lines = queue.Queue()
    errors = []

    def collect():
        for line in proc.stdout:
            try:
                lines.put(json.loads(line))
            except json.JSONDecodeError:
                pass

    threading.Thread(target=collect, daemon=True).start()
    threading.Thread(target=lambda: errors.extend(proc.stderr.readlines()), daemon=True).start()
    try:
        proc.stdin.write(json.dumps({"id": 1, "method": "initialize", "params": {"clientInfo": {
            "name": "quota_anchor", "title": "Codex Quota Anchor", "version": "1.0.0"}}}) + "\n")
        proc.stdin.flush()
        deadline = time.monotonic() + 45
        initialized = False
        while time.monotonic() < deadline:
            try:
                msg = lines.get(timeout=min(1, deadline - time.monotonic()))
            except queue.Empty:
                continue
            if msg.get("id") == 1:
                if "error" in msg:
                    raise RuntimeError(str(msg["error"]))
                initialized = True
                proc.stdin.write(json.dumps({"method": "initialized", "params": {}}) + "\n")
                proc.stdin.write(json.dumps({"id": 2, "method": "account/rateLimits/read"}) + "\n")
                proc.stdin.flush()
            if initialized and msg.get("id") == 2:
                if "error" in msg:
                    raise RuntimeError(str(msg["error"]))
                buckets = msg["result"].get("rateLimitsByLimitId") or {}
                bucket = buckets.get("codex") or msg["result"].get("rateLimits")
                if not bucket or not bucket.get("primary"):
                    raise RuntimeError("5시간 한도 정보를 받지 못했습니다.")
                primary = bucket["primary"]
                if primary.get("windowDurationMins") != WINDOW:
                    raise RuntimeError("예상한 300분 한도가 아닙니다.")
                if primary.get("usedPercent") is None or primary.get("resetsAt") is None:
                    raise RuntimeError("사용량 또는 초기화 시각이 없습니다.")
                return {"used": primary["usedPercent"], "reset": primary["resetsAt"]}
        raise TimeoutError(f"한도 조회 시간이 초과되었습니다. exit={proc.poll()} stderr={''.join(errors)[-800:]}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


def load_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(data):
    temp = HERE / "state.tmp"
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, STATE)


def send_turn():
    result = subprocess.run(
        [codex_path(), "exec", "--ephemeral", "--skip-git-repo-check",
         "--sandbox", "read-only", "-m", "gpt-6-luna", "--json",
         "간단히 '확인'이라고만 답해 주세요. 도구는 사용하지 마세요."],
        cwd=HERE, capture_output=True, text=True, encoding="utf-8", timeout=180,
    )
    if result.returncode:
        raise RuntimeError(f"Codex 요청 실패 (종료 코드 {result.returncode}): {result.stderr[-500:]}")
    events = []
    for line in result.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    if not any(event.get("type") == "turn.completed" for event in events):
        raise RuntimeError("Codex 요청 완료를 확인하지 못했습니다.")


def notify_user():
    if IS_WINDOWS:
        command = [
            "powershell.exe", "-NoProfile", "-NonInteractive", "-STA",
            "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File",
            str(HERE / "notify.ps1"),
        ]
    else:
        notifier = shutil.which("notify-send")
        if not notifier:
            raise RuntimeError("notify-send를 찾지 못했습니다. libnotify-bin을 설치하세요.")
        command = [
            notifier,
            "Codex quota window anchored",
            "The automatic request was sent successfully. The next 5-hour window has started.",
        ]
    result = subprocess.run(
        command, cwd=HERE, capture_output=True, text=True, encoding="utf-8", timeout=25,
    )
    if result.returncode:
        raise RuntimeError(f"사용자 알림 실패: {result.stderr[-500:]}")


def acquire_lock():
    lock_file = LOCK.open("a+b")
    if lock_file.tell() == 0:
        lock_file.write(b"0")
        lock_file.flush()
    lock_file.seek(0)
    try:
        if IS_WINDOWS:
            import msvcrt
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock_file.close()
        return None
    return lock_file


def run():
    lock_file = acquire_lock()
    if lock_file is None:
        return
    try:
        now = int(time.time())
        state = load_state()
        # When a known reset is far away, avoid starting the CLI before the reset.
        target = state.get("target_reset")
        if target and now < target:
            return
        limits = read_limits()
        if target is None:
            if limits["used"] > 0:
                state["target_reset"] = limits["reset"]
                save_state(state)
                log("watching", target_reset=limits["reset"])
                return
            target = now
        if limits["used"] > 0:
            state["target_reset"] = limits["reset"]
            save_state(state)
            log("already_used", target_reset=limits["reset"])
            return
        # The service can report a future reset even at 0%; the prior target
        # remains authoritative for deciding that this window has just cleared.
        log("sending", previous_reset=target)
        send_turn()
        state["last_sent_at"] = int(time.time())
        state["target_reset"] = state["last_sent_at"] + WINDOW * 60
        save_state(state)
        try:
            fresh = read_limits()
            if fresh["reset"] > state["last_sent_at"]:
                state["target_reset"] = fresh["reset"]
            log("sent", next_reset=fresh["reset"], used=fresh["used"])
        except Exception as exc:
            log("sent_next_reset_unverified", error=str(exc))
        save_state(state)
        try:
            notify_user()
            log("notified")
        except Exception as exc:
            log("notification_error", message=str(exc))
    except Exception as exc:
        log("error", message=str(exc))
        raise
    finally:
        lock_file.seek(0)
        if IS_WINDOWS:
            import msvcrt
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "status"])
    args = parser.parse_args()
    if args.command == "status":
        print(json.dumps({"limits": read_limits(), "state": load_state()}, ensure_ascii=False, indent=2))
    else:
        run()


if __name__ == "__main__":
    main()

