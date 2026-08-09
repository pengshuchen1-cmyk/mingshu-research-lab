from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_typewriter_animates_the_three_requested_questions_as_placeholders():
    from ui.homepage_components import TYPEWRITER_QUESTIONS
    from ui.homepage_typing_effect import build_question_typing_script

    script = build_question_typing_script(TYPEWRITER_QUESTIONS)

    assert "今天我的运势如何？" in script
    assert "如何推算我的命盘？" in script
    assert "今年是我的本命年，我的事业和爱情怎么样？" in script
    assert 'input.placeholder = characters.slice(0, characterIndex).join(\'\')' in script
    assert "Array.from(questions[questionIndex])" in script
    assert 'phase = \'deleting\'' in script
    assert '"hold_delay_ms": 2000' in script


def test_typewriter_bridge_enlarges_and_accessibly_labels_the_input():
    source = (ROOT / "ui" / "homepage_typing_effect.py").read_text(encoding="utf-8")

    assert '"input_height_px": 64' in source
    assert '"input_font_size_px": 18' in source
    assert '"input_right_padding_px": 88' in source
    assert '"submit_button_size_px": 54' in source
    assert "label { display: none !important; }" in source
    assert "input?.setAttribute('aria-label', '命理问题')" in source
    assert "submitButton?.setAttribute('aria-label', '询问')" in source
    assert "border-radius: 999px !important" in source
    assert "height: 56px !important" in source


def test_typewriter_never_writes_the_user_value_and_respects_accessibility():
    source = (ROOT / "ui" / "homepage_typing_effect.py").read_text(encoding="utf-8")

    assert "input.value =" not in source
    assert "if (input.value)" in source
    assert "prefers-reduced-motion: reduce" in source
    assert "renderStaticFallback" in source
    assert "shadowRoot?.querySelector" in source
    assert "__ms2QuestionTypingCleanup" in source


def test_typewriter_bridge_is_removed_from_visual_layout():
    styles = (ROOT / "ui" / "homepage_styles.py").read_text(encoding="utf-8")

    assert ".st-key-ms2-typing-placeholder-bridge" in styles
    assert "position: absolute !important" in styles
    assert "pointer-events: none !important" in styles
