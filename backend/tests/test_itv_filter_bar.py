from pathlib import Path


def test_itv_filter_bar_structure_and_controls():
    """F1-S13 & F1-S14: UnifiedFilterBar faqat bazada mavjud parametrlar bilan ishlashi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    filter_file = root_dir / "website" / "components" / "catalog" / "UnifiedFilterBar.tsx"

    assert filter_file.exists(), "UnifiedFilterBar.tsx topilmadi"
    content = filter_file.read_text(encoding="utf-8")

    # 1. Haqiqiy bazada mavjud parametrlar
    assert "Janr" in content, "Filtrda Janr maydoni topilmadi"
    assert "Bo'lim" in content, "Filtrda Bo'lim maydoni topilmadi"
    assert "Turi" in content, "Filtrda Turi maydoni topilmadi"
    assert "Yil" in content, "Filtrda Yil maydoni topilmadi"
    assert "Reyting bo'yicha saralash" in content or "saralash" in content.lower(), "Filtrda Reyting bo'yicha saralash topilmadi"

    # 2. Filtrlarni tozalash tugmasi
    assert "Filtrlarni tozalash" in content, "Filtrda '✕ Filtrlarni tozalash' tugmasi topilmadi"

    # 3. Bazada yo'q soxta parametrlar bo'lmasligi kerak
    assert "Subtitr" not in content
    assert "Audiotrek" not in content
    assert "Mamlakat" not in content
    assert "+ Bepul" not in content
