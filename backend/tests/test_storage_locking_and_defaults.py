import os
import sys
import json
import pytest
from filelock import FileLock, Timeout

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scraper.queue_manager import QueueManager
from scraper.state_manager import StateManager, DEFAULT_STATE
from scraper.autopilot_v2.quarantine_manager import QuarantineManager


def test_queue_manager_creates_empty_list_and_lock(tmp_path):
    queue_file = str(tmp_path / "test_queue.json")
    assert not os.path.exists(queue_file)

    qm = QueueManager(filepath=queue_file)
    assert os.path.exists(queue_file)
    assert qm.items == {}

    with open(queue_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == []
    assert qm._interprocess_lock is not None

    # Jarayonlararo qulflash ishlashini tekshiramiz:
    with qm._interprocess_lock:
        competing_lock = FileLock(qm.lock_path, timeout=0.1)
        with pytest.raises(Timeout):
            competing_lock.acquire(timeout=0.1)


def test_state_manager_creates_default_state_and_lock(tmp_path):
    state_file = str(tmp_path / "test_state.json")
    assert not os.path.exists(state_file)

    sm = StateManager.__new__(StateManager, filepath=state_file)
    sm.filepath = state_file
    sm.lock_path = f"{state_file}.lock"
    sm._lock = FileLock(sm.lock_path, timeout=15)
    sm.state = dict(DEFAULT_STATE)
    sm.load()

    assert os.path.exists(state_file)
    with open(state_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["uzmovi_current_page"] == DEFAULT_STATE["uzmovi_current_page"]
    assert sm._lock is not None

    with sm._lock:
        competing_lock = FileLock(sm.lock_path, timeout=0.1)
        with pytest.raises(Timeout):
            competing_lock.acquire(timeout=0.1)


def test_quarantine_manager_creates_empty_dict_and_lock(tmp_path):
    quarantine_file = str(tmp_path / "test_quarantine.json")
    assert not os.path.exists(quarantine_file)

    qm = QuarantineManager(filepath=quarantine_file)
    assert os.path.exists(quarantine_file)
    assert qm.items == {}

    with open(quarantine_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == {}
    assert qm._lock is not None

    with qm._lock:
        competing_lock = FileLock(qm.lock_path, timeout=0.1)
        with pytest.raises(Timeout):
            competing_lock.acquire(timeout=0.1)
