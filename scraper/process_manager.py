import os
import sys
import re
import time
import datetime
import threading
import subprocess
from typing import Dict, Any, List, Optional
from scraper.queue_manager import QueueManager

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VENV_PYTHON = os.path.join(ROOT_DIR, "backend", ".venv", "Scripts", "python.exe")
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable

class ProcessManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ProcessManager, cls).__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self.process: Optional[subprocess.Popen] = None
        self.reader_thread: Optional[threading.Thread] = None
        self.is_running: bool = False
        self.task_type: str = "idle"  # "parse", "download", "clean_duplicates", "idle"
        self.current_action: str = "Tizim tayyor"
        self.current_item: Optional[Dict[str, Any]] = None
        self.progress: Dict[str, Any] = {
            "current": 0,
            "total": 0,
            "percentage": 0.0
        }
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.logs: List[Dict[str, Any]] = []
        self.max_logs: int = 250
        self.qm = QueueManager()

    def _add_log(self, message: str, level: str = "info"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        with self._lock:
            self.logs.append({
                "timestamp": ts,
                "message": message,
                "level": level
            })
            if len(self.logs) > self.max_logs:
                self.logs.pop(0)

    def _parse_line(self, line: str):
        line = line.strip()
        if not line:
            return

        level = "info"
        lower = line.lower()
        if "❌" in line or "xatolik" in lower or "error" in lower or "failed" in lower:
            level = "error"
        elif "⚠️" in line or "ogohlantirish" in lower or "warning" in lower:
            level = "warning"
        elif "✅" in line or "muvaffaqiyatli" in lower or "yakunlandi" in lower:
            level = "success"

        self._add_log(line, level=level)

        with self._lock:
            # 1. Check for progress pattern [idx/total]
            # e.g.: [1/5] 🎬 Kod #15 bo'yicha ... or [3/20] 🚀 [KINO] 'Avatar' ...
            prog_match = re.search(r"\[(\d+)\/(\d+)\]", line)
            if prog_match:
                curr = int(prog_match.group(1))
                tot = int(prog_match.group(2))
                self.progress["current"] = curr
                self.progress["total"] = tot
                self.progress["percentage"] = round((curr / tot) * 100, 1) if tot > 0 else 0.0

            # 2. Check for current item/action details
            if "bo'yicha sikl boshlanmoqda" in line or "bo'yicha moderator sikli boshlanmoqda" in line:
                self.current_action = line
                # Try to extract title
                title_match = re.search(r"'([^']+)'", line)
                if title_match:
                    self.current_item = {"title": title_match.group(1)}
                elif "Kod #" in line:
                    code_match = re.search(r"Kod #(\w+)", line)
                    if code_match:
                        self.current_item = {"code": code_match.group(1)}
            elif "Sahifa " in line and "element yuklandi" in line:
                self.current_action = line
            elif "parallel katalog yig'ish boshlanmoqda" in line:
                self.current_action = line
            elif "dublikatlarga parallel tekshirilmoqda" in line:
                self.current_action = "Bazadagi dublikatlarga tekshirilmoqda..."
            elif "Muvaffaqiyatli saqlandi" in line:
                self.current_action = line
            elif "Yuklab bo'lmadi" in line:
                self.current_action = line
            elif "tanaffus" in line:
                self.current_action = "Telegram flood-wait oldini olish uchun tanaffus..."

    def _run_worker(self, cmd_args: List[str], task_name: str, expected_total: int = 0):
        self.is_running = True
        self.task_type = task_name
        self.started_at = time.time()
        self.finished_at = None
        self.progress = {
            "current": 0,
            "total": expected_total,
            "percentage": 0.0
        }
        self.current_action = f"{task_name.upper()} jarayoni ishga tushirildi..."
        self._add_log(f"🚀 Jarayon boshlandi: {' '.join(cmd_args)}", level="info")

        try:
            # Set unbuffered python output
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"

            self.process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=ROOT_DIR,
                env=env
            )

            for line in iter(self.process.stdout.readline, ''):
                if not line:
                    break
                self._parse_line(line)

            self.process.stdout.close()
            return_code = self.process.wait()
            
            with self._lock:
                if return_code == 0:
                    self._add_log(f"🏁 Jarayon muvaffaqiyatli yakunlandi (Exit code: 0)", level="success")
                    self.current_action = "Muvaffaqiyatli yakunlandi"
                    self.progress["percentage"] = 100.0
                elif return_code < 0 or return_code == 15: # Terminated
                    self._add_log("⏹️ Jarayon admin tomonidan to'xtatildi", level="warning")
                    self.current_action = "To'xtatildi"
                else:
                    self._add_log(f"❌ Jarayon xatolik bilan yakunlandi (Exit code: {return_code})", level="error")
                    self.current_action = f"Xatolik yuz berdi (code: {return_code})"
        except Exception as e:
            self._add_log(f"❌ Subprocess xatosi: {str(e)}", level="error")
            self.current_action = f"Tizim xatosi: {str(e)}"
        finally:
            with self._lock:
                self.is_running = False
                self.finished_at = time.time()
                self.process = None

    def start_parse(self, source: str = "uzmovi", pages: int = 3) -> Dict[str, Any]:
        with self._lock:
            if self.is_running:
                return {"success": False, "message": "Boshqa jarayon allaqachon ishlayapti!"}

        script_path = os.path.join(ROOT_DIR, "scraper", "run_scraper.py")
        cmd = [
            VENV_PYTHON,
            script_path,
            "--parse",
            "--source", source,
            "--pages", str(pages)
        ]

        self.reader_thread = threading.Thread(
            target=self._run_worker,
            args=(cmd, "parse", pages),
            daemon=True
        )
        self.reader_thread.start()
        return {"success": True, "message": f"{source} manbasidan {pages} ta sahifa yig'ish boshlandi."}

    def start_download(
        self,
        target: str = "uzmovi",
        limit: int = 5,
        codes: Optional[str] = None,
        media_type: str = "all"
    ) -> Dict[str, Any]:
        with self._lock:
            if self.is_running:
                return {"success": False, "message": "Boshqa jarayon allaqachon ishlayapti!"}

        script_path = os.path.join(ROOT_DIR, "scraper", "run_scraper.py")
        cmd = [
            VENV_PYTHON,
            script_path,
            "--download",
            "--target", target,
            "--limit", str(limit),
            "--media-type", media_type
        ]
        if codes and codes.strip():
            cmd.extend(["--codes", codes.strip()])

        expected_count = limit
        if codes and codes.strip():
            expected_count = len([c for c in codes.split(",") if c.strip()])

        self.reader_thread = threading.Thread(
            target=self._run_worker,
            args=(cmd, "download", expected_count),
            daemon=True
        )
        self.reader_thread.start()
        return {"success": True, "message": f"Telegram grabber ishga tushirildi (Maqsad: {target})."}

    def start_clean_duplicates(self) -> Dict[str, Any]:
        with self._lock:
            if self.is_running:
                return {"success": False, "message": "Boshqa jarayon allaqachon ishlayapti!"}

        script_path = os.path.join(ROOT_DIR, "scraper", "run_scraper.py")
        cmd = [
            VENV_PYTHON,
            script_path,
            "--clean-duplicates"
        ]

        self.reader_thread = threading.Thread(
            target=self._run_worker,
            args=(cmd, "clean_duplicates", 0),
            daemon=True
        )
        self.reader_thread.start()
        return {"success": True, "message": "Dublikatlarni tozalash jarayoni boshlandi."}

    def stop_process(self) -> Dict[str, Any]:
        with self._lock:
            if not self.is_running or not self.process:
                return {"success": False, "message": "Hozirda faol jarayon yo'q."}

            try:
                self.process.terminate()
                self._add_log("⚠️ Jarayonga to'xtatish signali (terminate) yuborildi...", level="warning")
                # Wait briefly
                def kill_if_alive():
                    time.sleep(3)
                    if self.process and self.process.poll() is None:
                        self.process.kill()
                        self._add_log("🛑 Jarayon majburiy to'xtatildi (killed).", level="warning")
                threading.Thread(target=kill_if_alive, daemon=True).start()
                return {"success": True, "message": "Jarayonni to'xtatish so'rovi berildi."}
            except Exception as e:
                return {"success": False, "message": f"To'xtatishda xatolik: {str(e)}"}

    def get_status(self) -> Dict[str, Any]:
        qm = QueueManager()
        stats = qm.stats()

        elapsed = 0
        if self.started_at:
            if self.is_running:
                elapsed = int(time.time() - self.started_at)
            elif self.finished_at:
                elapsed = int(self.finished_at - self.started_at)

        with self._lock:
            return {
                "is_running": self.is_running,
                "task_type": self.task_type,
                "current_action": self.current_action,
                "current_item": self.current_item,
                "progress": dict(self.progress),
                "started_at": datetime.datetime.fromtimestamp(self.started_at).isoformat() if self.started_at else None,
                "elapsed_seconds": elapsed,
                "logs": list(self.logs),
                "stats": stats
            }

    def clear_logs(self):
        with self._lock:
            self.logs = []
