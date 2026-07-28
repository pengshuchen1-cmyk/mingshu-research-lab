from __future__ import annotations


def test_extended_ai_domains_have_normative_rules():
    from core.bazi_rulebook import load_rulebook

    book = load_rulebook()
    required = {
        "career",
        "family",
        "health_advisory",
        "children",
        "education",
        "relocation",
        "property",
        "benefactor",
    }

    assert required <= set(book.sections)
    for section in required:
        assert len(book.sections[section]) >= 2
        assert all(rule.citations for rule in book.sections[section])
