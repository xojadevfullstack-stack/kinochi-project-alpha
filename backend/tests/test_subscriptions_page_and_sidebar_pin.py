from pathlib import Path


def test_dedicated_subscriptions_page_no_redirect():
    """F1-S12: Subscriptions sahifasi profilga yo'naltirmasdan mustaqil tariflar sahifasi bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    sub_page = root_dir / "website" / "app" / "subscriptions" / "page.tsx"

    assert sub_page.exists(), "website/app/subscriptions/page.tsx topilmadi"
    content = sub_page.read_text(encoding="utf-8")

    # Profilga redirect qilmasligi kerak
    assert "router.replace(\"/profile" not in content, "Subscriptions page hali ham profilga redirect qilmoqda"
    assert "router.replace('/profile" not in content, "Subscriptions page hali ham profilga redirect qilmoqda"

    # Obunalar (Kuzatuv/Favorite ro'yxati) ko'rsatilishi kerak
    assert "Obuna" in content
    assert "subscriptions" in content or "series" in content


def test_bottom_nav_and_navbar_route_to_subscriptions():
    """F1-S12: BottomNav va Navbar obunalar tugmasi /subscriptions ga yo'naltirishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    bottom_nav = root_dir / "website" / "components" / "BottomNav.tsx"
    navbar = root_dir / "website" / "components" / "Navbar.tsx"

    b_content = bottom_nav.read_text(encoding="utf-8")
    assert 'href: "/subscriptions"' in b_content, "BottomNav da obunalar havolasi /subscriptions emas"
    assert '"/profile?tab=subscriptions"' not in b_content, "BottomNav da hali ham eski /profile?tab=subscriptions qolgan"

    n_content = navbar.read_text(encoding="utf-8")
    assert 'href="/subscriptions"' in n_content, "Navbar da obunalar havolasi /subscriptions emas"


def test_sidebar_pin_state_persists_on_refresh():
    """F1-S12: Desktop sidebarni pin qilganda F5 yangilanganda saqlanib qolishi va aside ochiq turishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    navbar = root_dir / "website" / "components" / "Navbar.tsx"

    content = navbar.read_text(encoding="utf-8")
    # Aside elementi isPinned holatini to'g'ri inobatga olishi shart
    assert "(sidebarOpen || isPinned)" in content, "Navbar aside elementi (sidebarOpen || isPinned) ni tekshirmayapti"
    # Dastlabki renderda localStorage tozalanib ketmasligi uchun guard bo'lishi kerak
    assert "isInitializedRef" in content or "isMountedRef" in content or "initialized" in content
