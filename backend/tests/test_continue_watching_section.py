from pathlib import Path


def test_continue_watching_section_exists_and_contract():
    """F1-S05: website/components/home/ContinueWatchingSection.tsx mavjudligi va shartnomasi."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    section_file = root_dir / "website" / "components" / "home" / "ContinueWatchingSection.tsx"

    assert section_file.exists(), "website/components/home/ContinueWatchingSection.tsx topilmadi"
    content = section_file.read_text(encoding="utf-8")

    assert "Ko'rishni davom ettirish" in content or "Davom ettirish" in content
    assert "mediaplus_continue_watching" in content
    assert "getHistory" in content


def test_continue_watching_section_mounted_in_home_page():
    """F1-S05: website/app/page.tsx da ContinueWatchingSection chaqirilgan bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    page_file = root_dir / "website" / "app" / "page.tsx"

    assert page_file.exists(), "website/app/page.tsx topilmadi"
    content = page_file.read_text(encoding="utf-8")

    assert "ContinueWatchingSection" in content, "page.tsx da ContinueWatchingSection topilmadi"
    assert "<ContinueWatchingSection" in content, "page.tsx da <ContinueWatchingSection /> komponenti chaqirilmagan"


def test_telegram_watch_button_records_continue_watching():
    """F1-S05: TelegramWatchButton orqali ko'rish bosilganda mediaplus_continue_watching ga yozilishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    btn_file = root_dir / "website" / "components" / "TelegramWatchButton.tsx"

    assert btn_file.exists()
    content = btn_file.read_text(encoding="utf-8")

    assert "mediaplus_continue_watching" in content, "TelegramWatchButton mediaplus_continue_watching ni yangilamaydi"
