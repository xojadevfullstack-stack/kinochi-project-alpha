import os
import pytest
from bot.main import BotInstanceLock, BotAlreadyRunningError

def test_bot_single_instance_lock(tmp_path):
    """
    BUG-006 Regression Test:
    Ensures that only a single instance of the bot can run.
    The second attempt MUST raise BotAlreadyRunningError.
    """
    lock_file = str(tmp_path / ".bot.lock")
    pid_file = str(tmp_path / ".bot.pid")

    lock1 = BotInstanceLock(lock_file=lock_file, pid_file=pid_file)
    lock2 = BotInstanceLock(lock_file=lock_file, pid_file=pid_file)

    assert lock1.acquire() is True
    assert os.path.exists(pid_file)

    # Second instance must fail
    with pytest.raises(BotAlreadyRunningError) as exc_info:
        lock2.acquire()

    assert "allaqachon ishlayapti" in str(exc_info.value)

    # Releasing lock1 allows lock2 to acquire
    lock1.release()
    assert lock2.acquire() is True
    lock2.release()
    assert not os.path.exists(pid_file)
