import pytest

import summarizer


def test_strip_code_fence_removes_wrapping_fence():
    assert summarizer.strip_code_fence('```markdown\n# Hi\n```') == '# Hi'
    assert summarizer.strip_code_fence('```\n# Hi\n```') == '# Hi'


def test_strip_code_fence_removes_chatty_preamble():
    assert summarizer.strip_code_fence('Sure, here you go:\n```\n# Hi\n```') == '# Hi'


def test_strip_code_fence_leaves_unfenced_text_alone():
    assert summarizer.strip_code_fence('# Hi\n\nsome text') == '# Hi\n\nsome text'


def test_strip_code_fence_keeps_interior_code_blocks():
    raw = '# Title\n\n```python\nx = 1\n```\n\nMore text'
    assert summarizer.strip_code_fence(raw) == raw


def test_two_space_nesting_becomes_a_real_sublist():
    html = summarizer.md_to_html('* a\n  * nested\n* b')
    assert '<li>a<ul>' in html
    assert html.count('<ul>') == 2


def test_deep_nesting():
    html = summarizer.md_to_html('* a\n  * b\n    * c')
    assert html.count('<ul>') == 3


def test_ordered_list_nesting():
    html = summarizer.md_to_html('1. one\n  1. sub\n2. two')
    assert html.count('<ol>') == 2


def test_code_fence_contents_are_not_treated_as_a_list():
    html = summarizer.md_to_html('text\n\n```\n  * not a list\n```')
    assert '<li>' not in html


def test_tables_render():
    html = summarizer.md_to_html('| a | b |\n|---|---|\n| 1 | 2 |')
    assert '<table>' in html


def test_get_summary_rejects_unknown_length():
    with pytest.raises(ValueError):
        summarizer.get_summary('text', 'Nonsense')


def test_every_summary_type_has_a_prompt_file():
    for option in summarizer.summary_types:
        value = option['value']
        if value == summarizer.FULL_TRANSCRIPT:
            continue
        assert (summarizer.PROMPTS / f'{value}.md').exists()
