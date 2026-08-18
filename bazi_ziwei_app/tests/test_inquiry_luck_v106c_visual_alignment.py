import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InquiryLuckV106CVisualAlignmentTests(unittest.TestCase):
    def test_inquiry_and_luck_pages_use_homepage_visual_language(self):
        expected = {
            "inquiry_page.py": [
                "ms-inquiry-page",
                "page_header(",
                "ms-inquiry-context",
                "ms-inquiry-thread",
            ],
            "luck_page.py": ["v106c-page-hero", "ms-report-panel", "ms-mini-metric", "ms-luck-stage-card", "ms-tag"],
        }
        for filename, tokens in expected.items():
            text = (ROOT / "ui" / filename).read_text(encoding="utf-8")
            for token in tokens:
                self.assertIn(token, text, f"{filename} 缺少 {token}")

    def test_inquiry_and_luck_pages_do_not_emit_old_light_inline_cards(self):
        combined = "\n".join(
            (ROOT / "ui" / filename).read_text(encoding="utf-8")
            for filename in ["inquiry_page.py", "luck_page.py"]
        )
        forbidden = [
            "background:#FAF7F4",
            "background:#f8f9fa",
            "background:#e8f5e9",
            "color:#3D2B1A",
            "color:#5C4A32",
            "color:#8C7A64",
            "color:#666",
            "border:1px solid #EDE6DC",
            "border:1px solid #e0e0e0",
        ]
        for snippet in forbidden:
            self.assertNotIn(snippet, combined)

    def test_global_css_has_luck_stage_card_component(self):
        text = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
        for token in [".ms-luck-stage-card", ".ms-luck-stage-card.current", ".ms-action-grid"]:
            self.assertIn(token, text)

    def test_inquiry_uses_minimal_chat_workspace_without_old_hero(self):
        inquiry = (ROOT / "ui" / "inquiry_page.py").read_text(encoding="utf-8")
        styles = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")

        for removed in [
            "LOCAL RULES · AI Q&amp;A",
            '<div class="v106c-page-title">AI问答</div>',
            "用当前命盘的本地四柱事实回答，并显示依据与不确定性。",
            "你可以这样问",
        ]:
            self.assertNotIn(removed, inquiry)
        self.assertIn("本地规则校验 · 对话最多保留 20 条", inquiry)
        self.assertIn("empty_state_header(", inquiry)
        self.assertIn('page_header(\n            "命理助手"', inquiry)
        self.assertNotIn('st.title("AI问答")', inquiry)
        self.assertIn("render_loaded_profile_hint", inquiry)
        self.assertIn("当前命盘的本地规则摘要", inquiry)
        self.assertIn('key="ms_inquiry_chat_input"', inquiry)
        self.assertIn('max_chars=2000', inquiry)
        for token in [
            '.st-key-ms-inquiry-page',
            '[data-testid="stChatMessage"]',
            '[data-testid="stChatInput"]',
            '[data-testid="stBottomBlockContainer"]',
            'align-items: center !important',
            'min-height: 44px',
            'bottom: calc(64px + env(safe-area-inset-bottom))',
        ]:
            self.assertIn(token, styles)


if __name__ == "__main__":
    unittest.main()
