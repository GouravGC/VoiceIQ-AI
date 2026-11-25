from app_core.metrics import word_error_rate


def test_wer_identical_text():
    assert word_error_rate("hello world", "hello world") == 0.0


def test_wer_one_substitution():
    assert word_error_rate("hello world", "hello there") == 0.5


def test_wer_empty_reference():
    assert word_error_rate("", "") == 0.0


def test_wer_one_insertion():
    assert word_error_rate("hello world", "hello brave world") == 0.5
