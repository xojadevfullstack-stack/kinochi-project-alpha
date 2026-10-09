import os
import sys
import re
import time
import datetime
import threading
import subprocess
from typing import Dict, Any, List, Optional
from scraper.queue_manager import QueueManager
from scraper.state_manager import StateManager

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRAPER_SCRIPT = os.path.join(ROOT_DIR, "scraper", "run_scraper.py")


def _find_python() -> str:
    candidates = [
        os.path.join(ROOT_DIR, "backend", ".venv", "Scripts", "python.exe"),
        os.path.join(ROOT_DIR, "backend", ".venv", "bin", "python"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return sys.executable


VENV_PYTHON = _find_python()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


class ProcessManager:
    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    inst = super(ProcessManager, cls).__new__(cls)
                    inst._init()
                    cls._instance = inst
        return cls._instance

    def _init(self):
        # Re-entrant: helper methods are called while the lock is already held.
        self._lock = threading.RLock()
        self.process: Optional[subprocess.Popen] = None
        self.is_running: bool = False
        self.stop_requested: bool = False
        self.task_type: str = "idle"
        self.current_action: str = "Tizim tayyor"
        self.current_item: Optional[Dict[str, Any]] = None
        self.progress: Dict[str, Any] = {"current": 0, "total": 0, "percentage": 0.0}
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.logs: List[Dict[str, Any]] = []
        self.max_logs: int = 300

    # ── logging ──────────────────────────────────────────────
    def _add_log(self, message: str, level: str = "info"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        with self._lock:
            self.logs.append({"timestamp": ts, "message": message, "level": level})
            if len(self.logs) > self.max_logs:
                del self.logs[: len(self.logs) - self.max_logs]

    def _set_progress(self, current: int, total: int):
        total = max(total, 0)
        current = max(current, 0)
        if total and current > total:
            current = total
        self.progress["current"] = current
        self.progress["total"] = total
        self.progress["percentage"] = round(current / total * 100, 1) if total > 0 else 0.0

    def _parse_line(self, line: str):
        line = _ANSI_RE.sub("", line).strip()
        if not line:
            return

        lower = line.lower()
        level = "info"
        if "❌" in line or "traceback" in lower or "xatolik" in lower or "error" in lower:
            level = "error"
        elif "⚠️" in line or "warning" in lower or "yuklab bo'lmadi" in lower:
            level = "warning"
        elif "✅" in line or "muvaffaqiyatli" in lower or "yakunlandi" in lower:
            level = "success"

        self._add_log(line, level=level)

        with self._lock:
            prog = re.search(r"\[(\d+)/(\d+)\]", line)
            if prog and ("sikl boshlanmoqda" in lower or "bo'yicha sikl" in lower or "kod #" in lower):
                self._set_progress(int(prog.group(1)) - 1, int(prog.group(2)))
                title = re.search(r"'([^']+)'", line)
                code = re.search(r"Kod #(\w+)", line)
                if title:
                    self.current_item = {"title": title.group(1)}
                    self.current_action = f"🎬 '{title.group(1)}' yuklanmoqda..."
                elif code:
                    self.current_item = {"code": code.group(1)}
                    self.current_action = f"🎬 Kod #{code.group(1)} yuklanmoqda..."
                return

            page = re.search(r"Sahifa (\d+):", line)
            if page and self.task_type in ("parse", "autopilot"):
                if self.task_type == "parse":
                    total = self.progress["total"] or int(page.group(1))
                    self._set_progress(int(page.group(1)), total)
                self.current_action = line
            elif "avtopilot sikli" in lower:
                self.current_action = line
            elif "qadam:" in lower:
                clean_step = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\[\w+\]\s*', '', line)
                self.current_action = clean_step
            elif "botiga so'rov" in lower or "inline qidiruv" in lower or "qidirilmoqda" in lower:
                clean_step = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\[\w+\]\s*', '', line)
                self.current_action = clean_step
            elif "qism yuklanmoqda" in lower or "qism bazaga saqlandi" in lower or "qism saqlandi" in lower:
                self.current_action = line
            elif "muvaffaqiyatli saqlandi" in lower or "yuklab bo'lmadi" in lower:
                # finished the current item -> count it as done
                self._set_progress(self.progress["current"] + 1, max(self.progress["total"], self.progress["current"] + 1))
                self.current_action = line
            elif "dublikatlarga" in lower and "tekshirilmoqda" in lower:
                self.current_action = "Bazadagi dublikatlarga tekshirilmoqda..."
            elif "katalog yig'ish boshlanmoqda" in lower:
                self.current_action = line
            elif "yuklab olish:" in lower or "telegramga yuklash:" in lower:
                clean_step = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+\[\w+\]\s*', '', line).strip()
                self.current_action = clean_step
            elif "tanaffus" in lower:
                self.current_action = line
            elif "yuklash boshlanmoqda" in lower:
                total = re.search(r"(\d+) ta", line)
                if total:
                    self._set_progress(self.progress["current"], int(total.group(1)))
                self.current_action = line

    # ── worker ───────────────────────────────────────────────
    def _run_worker(self, cmd_args: List[str], task_name: str, expected_total: int = 0):
        # NOTE: caller (_launch) has already set is_running/progress under lock.
        return_code: Optional[int] = None
        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"

            creationflags = 0
            if sys.platform == "win32":
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

            proc = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=ROOT_DIR,
                env=env,
                creationflags=creationflags,
            )
            with self._lock:
                self.process = proc

            assert proc.stdout is not None
            while True:
                line = proc.stdout.readline()
                if not line:
                    if proc.poll() is not None:
                        break
                    time.sleep(0.05)
                    continue
                self._parse_line(line)
            try:
                proc.stdout.close()
            except Exception:
                pass
            return_code = proc.wait()
        except Exception as e:
            self._add_log(f"❌ Subprocess xatosi: {e}", level="error")
            with self._lock:
                self.current_action = f"Tizim xatosi: {e}"
        finally:
            # Items left "in_progress" by a stopped/crashed run must not stay stuck.
            try:
                reset = QueueManager().reset_stuck_in_progress()
                if reset:
                    self._add_log(f"♻️ {reset} ta qotib qolgan element 'kutilmoqda' holatiga qaytarildi.", level="info")
            except Exception as e:
                self._add_log(f"⚠️ Navbatni tiklashda xatolik: {e}", level="warning")

            try:
                StateManager().set_bot_status("idle")
                StateManager().update(autopilot_active=False)
            except Exception:
                pass

            with self._lock:
                if self.stop_requested:
                    self._add_log("⏹️ Jarayon admin tomonidan to'xtatildi", level="warning")
                    self.current_action = "To'xtatildi"
                elif return_code == 0:
                    self._add_log("🏁 Jarayon muvaffaqiyatli yakunlandi", level="success")
                    self.current_action = "Muvaffaqiyatli yakunlandi"
                    self.current_item = None
                    if task_name != "clean_duplicates" or self.progress["total"]:
                        self._set_progress(self.progress["total"], self.progress["total"])
                    if not self.progress["total"]:
                        self.progress["percentage"] = 100.0
                elif return_code is not None:
                    self._add_log(f"❌ Jarayon xatolik bilan yakunlandi (exit code: {return_code})", level="error")
                    self.current_action = f"Xatolik yuz berdi (exit code: {return_code})"
                self.is_running = False
                self.finished_at = time.time()
                self.process = None
                self.stop_requested = False

    def _launch(self, cmd: List[str], task_name: str, expected_total: int, ok_message: str) -> Dict[str, Any]:
        with self._lock:
            if self.is_running:
                return {"success": False, "message": "Boshqa jarayon allaqachon ishlayapti!"}
            # Claim the slot synchronously -> no double-start race.
            self.is_running = True
            self.stop_requested = False
            self.task_type = task_name
            self.started_at = time.time()
            self.finished_at = None
            self.current_item = None
            self.current_action = f"{task_name} jarayoni ishga tushirilmoqda..."
            self._set_progress(0, expected_total)
            self._add_log(f"🚀 Jarayon boshlandi: {task_name}", level="info")

        try:
            t = threading.Thread(target=self._run_worker, args=(cmd, task_name, expected_total), daemon=True)
            t.start()
        except Exception as e:
            with self._lock:
                self.is_running = False
            return {"success": False, "message": f"Jarayonni ishga tushirib bo'lmadi: {e}"}
        return {"success": True, "message": ok_message}

    # ── public API ───────────────────────────────────────────
    def start_parse(
        self,
        source: str = "uzmovi",
        pages: int = 3,
        start_page: Optional[int] = None,
        min_rating: Optional[float] = None
    ) -> Dict[str, Any]:
        if source not in ("uzmovi", "asilmedia", "kawaii"):
            return {"success": False, "message": "Noma'lum manba."}
        pages = max(1, min(int(pages), 50))
        cmd = [VENV_PYTHON, SCRAPER_SCRIPT, "--parse", "--source", source, "--pages", str(pages)]
        if start_page is not None:
            cmd.extend(["--start-page", str(start_page)])
        if min_rating is not None:
            cmd.extend(["--min-rating", str(min_rating)])
        return self._launch(cmd, "parse", pages, f"{source.upper()} manbasidan {pages} ta sahifa yig'ish boshlandi.")

    def start_download(
        self,
        target: str = "uzmovi",
        limit: int = 5,
        codes: Optional[str] = None,
        media_type: str = "all",
        item_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if target not in ("uzmovi", "asilmedia", "kawaii"):
            return {"success": False, "message": "Noma'lum maqsadli bot."}
        if media_type not in ("all", "movie", "series"):
            return {"success": False, "message": "Noma'lum media turi."}
        limit = max(1, min(int(limit), 500))

        cmd = [VENV_PYTHON, SCRAPER_SCRIPT, "--download", "--target", target,
               "--limit", str(limit), "--media-type", media_type]
        expected = limit
        if item_id and item_id.strip():
            cmd.extend(["--item-id", item_id.strip()])
            expected = 1
        elif codes and codes.strip():
            clean = codes.strip()
            if not re.fullmatch(r"[0-9A-Za-z,\- ]+", clean):
                return {"success": False, "message": "Kodlar formati noto'g'ri (masalan: 15 yoki 1-5 yoki 10,12)."}
            cmd.extend(["--codes", clean.replace(" ", "")])
            expected = 0  # real total is announced by the scraper's own output
        return self._launch(cmd, "download", expected, f"Telegram grabber ishga tushirildi (Maqsad: {target}).")

    def start_autopilot(
        self,
        source: str = "all",
        pages: Optional[int] = None,
        limit: Optional[int] = None,
        media_type: str = "all",
        min_rating: Optional[float] = None
    ) -> Dict[str, Any]:
        if source not in ("uzmovi", "asilmedia", "kawaii", "all"):
            return {"success": False, "message": "Noma'lum manba."}

        try:
            StateManager().update(autopilot_active=True)
            if min_rating is not None:
                StateManager().update(min_rating=float(min_rating))
        except Exception:
            pass

        cmd = [VENV_PYTHON, SCRAPER_SCRIPT, "--autopilot", "--source", source, "--media-type", media_type]
        if pages is not None and int(pages) > 0:
            cmd.extend(["--pages", str(pages)])
        if limit is not None and int(limit) > 0:
            cmd.extend(["--limit", str(limit)])
        if min_rating is not None:
            cmd.extend(["--min-rating", str(min_rating)])

        expected = int(limit) if (limit and int(limit) > 0) else 0
        src_label = "BARCHASI (UZMOVI, ASILMEDIA & KAWAII)" if source == "all" else source.upper()
        return self._launch(
            cmd,
            "autopilot",
            expected,
            f"Avtopilot ishga tushirildi ({src_label}, reyting: {min_rating or 6.0}+)."
        )

    def start_retry_failed(self) -> Dict[str, Any]:
        cmd = [VENV_PYTHON, SCRAPER_SCRIPT, "--retry-failed"]
        return self._launch(cmd, "retry_failed", 0, "Muvaffaqiyatsiz kinolarni qayta tiklash boshlandi.")

    def start_clean_duplicates(self) -> Dict[str, Any]:
        cmd = [VENV_PYTHON, SCRAPER_SCRIPT, "--clean-duplicates"]
        return self._launch(cmd, "clean_duplicates", 0, "Dublikatlarni tozalash jarayoni boshlandi.")

    def stop_process(self) -> Dict[str, Any]:
        with self._lock:
            proc = self.process
            if not self.is_running or proc is None or proc.poll() is not None:
                return {"success": False, "message": "Hozirda faol jarayon yo'q."}
            self.stop_requested = True
            self.current_action = "To'xtatilmoqda..."
            self._add_log("⚠️ Jarayonga to'xtatish signali yuborildi...", level="warning")
            try:
                StateManager().update(autopilot_active=False)
                StateManager().set_bot_status("idle")
            except Exception:
                pass

        try:
            proc.terminate()
        except Exception as e:
            return {"success": False, "message": f"To'xtatishda xatolik: {e}"}

        def kill_if_alive():
            time.sleep(5)
            try:
                if proc.poll() is None:
                    proc.kill()
                    self._add_log("🛑 Jarayon majburiy to'xtatildi (kill).", level="warning")
            except Exception:
                pass

        threading.Thread(target=kill_if_alive, daemon=True).start()
        return {"success": True, "message": "Jarayonni to'xtatish so'rovi berildi."}

    def get_status(self) -> Dict[str, Any]:
        stats = QueueManager().stats()
        state = StateManager().get_state()
        with self._lock:
            elapsed = 0
            speed = 0.0
            if self.started_at:
                end = time.time() if self.is_running else (self.finished_at or time.time())
                elapsed = int(end - self.started_at)
                done_in_run = self.progress.get("current", 0)
                if elapsed > 10 and done_in_run > 0:
                    speed = round((done_in_run / elapsed) * 60, 1)

            bot_status = state.get("telegram_bot_status", "idle")
            if self.is_running:
                if bot_status in ("idle", "offline"):
                    bot_status = "online"
                if "floodwaiterror" in self.current_action.lower() or "flood-wait" in self.current_action.lower() or bot_status == "flood_wait":
                    bot_status = "flood_wait"

            return {
                "is_running": self.is_running,
                "task_type": self.task_type,
                "current_action": self.current_action,
                "current_item": dict(self.current_item) if self.current_item else None,
                "progress": dict(self.progress),
                "started_at": datetime.datetime.fromtimestamp(self.started_at).isoformat() if self.started_at else None,
                "elapsed_seconds": elapsed,
                "speed_movies_per_min": speed,
                "bot_status": bot_status,
                "logs": list(self.logs),
                "stats": stats,
                "state": state,
            }

    def clear_logs(self):
        with self._lock:
            self.logs = []
