import asyncio

from src import review


def test_build_diff_text_skips_large_file_but_keeps_smaller_one():
    original_limit = review.MAX_TOTAL_BYTES
    review.MAX_TOTAL_BYTES = 50
    try:
        files = [
            {"filename": "app/large.py", "patch": "x" * 60},
            {"filename": "app/small.py", "patch": "y" * 10},
        ]

        diff_text, included = asyncio.run(review.build_diff_text(files))
    finally:
        review.MAX_TOTAL_BYTES = original_limit

    assert "app/small.py" in included
    assert "app/large.py" not in included
    assert "--- app/small.py" in diff_text
