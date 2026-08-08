from app.use_cases import USE_CASES_TEXT


def test_use_cases_explain_independent_zips_and_single_file_limit() -> None:
    assert "Zalo" in USE_CASES_TEXT
    assert "mỗi ZIP là độc lập" in USE_CASES_TEXT
    assert "video 2 GB" in USE_CASES_TEXT
    assert "phải ghép đủ các phần" in USE_CASES_TEXT
