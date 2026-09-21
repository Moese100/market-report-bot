from market_report.feishu import split_markdown


def test_split_markdown_keeps_all_text() -> None:
    original = ("第一段内容\n\n第二段内容很长\n" * 20).strip()
    chunks = split_markdown(original, 120)
    assert len(chunks) > 1
    assert "".join(chunks).replace("\n", "") == original.replace("\n", "")
    assert all(len(chunk) <= 120 for chunk in chunks)
