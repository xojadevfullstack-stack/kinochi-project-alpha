import pytest
from scraper.run_scraper import ScraperCliLock, ScraperAlreadyRunningError

def test_single_instance_lock_prevents_concurrent_runs(tmp_path):
    """F-017: Scraper CLI ishga tushganda bir vaqtning o'zida ikkinchi jarayon to'xtatilishi kerak."""
    lock_file = str(tmp_path / "test_scraper.lock")

    lock1 = ScraperCliLock(lock_file=lock_file)
    assert lock1.acquire() is True

    # Ikkinchi jarayon lock olishga uringanda ScraperAlreadyRunningError yuzaga kelishi kerak
    lock2 = ScraperCliLock(lock_file=lock_file)
    with pytest.raises(ScraperAlreadyRunningError):
        lock2.acquire()

    # Birinchi jarayon tugagach, lock bo'shashi kerak
    lock1.release()

    # Endi ikkinchi jarayon muvaffaqiyatli lock ola olishi kerak
    assert lock2.acquire() is True
    lock2.release()
