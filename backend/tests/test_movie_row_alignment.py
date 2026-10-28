from pathlib import Path


def test_movie_row_gutter_alignment():
    """F1-S24: MovieRow da px-gutter tashqi section ga berilishi shart, va ichki flex scroll dan px-gutter olib tashlanishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    page_file = root_dir / "website" / "app" / "page.tsx"
    content = page_file.read_text(encoding="utf-8")

    assert '<section className="max-w-container-max mx-auto px-gutter mb-14 sm:mb-16">' in content, (
        "MovieRow section idan px-gutter topilmadi"
    )
    assert 'flex gap-4 overflow-x-auto snap-x hide-scrollbar px-gutter' not in content, (
        "MovieRow ichki flex scrollida px-gutter qolgan, bu chapga yopishishga sabab bo'ladi"
    )


def test_recommendations_section_gutter_alignment():
    """F1-S24: RecommendationsSection da ham px-gutter tashqi section ga berilishi lozim."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    rec_file = root_dir / "website" / "components" / "recommendations" / "RecommendationsSection.tsx"
    content = rec_file.read_text(encoding="utf-8")

    assert '<section className="max-w-container-max mx-auto px-gutter' in content, (
        "RecommendationsSection section idan px-gutter topilmadi"
    )
    assert 'flex gap-4 overflow-x-auto snap-x hide-scrollbar px-gutter' not in content, (
        "RecommendationsSection ichki flex scrollida px-gutter qolmasligi lozim"
    )
