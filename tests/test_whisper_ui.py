"""Task 30: whisper/audience control in the frontend (static boundary tests)."""

from __future__ import annotations

import re
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "src" / "static"
APP = (STATIC / "app.js").read_text(encoding="utf-8")
HTML = (STATIC / "index.html").read_text(encoding="utf-8")
I18N = (STATIC / "i18n.js").read_text(encoding="utf-8")
CSS = (STATIC / "style.css").read_text(encoding="utf-8")


class TestComposerControl:
    def test_whisper_button_and_popup_exist_in_the_action_menu(self) -> None:
        assert 'id="action-whisper-btn"' in HTML
        assert 'id="whisper-popup"' in HTML
        # Lives in the primary action row, so the mobile long-press menu keeps
        # its secondary actions (Suggest included) reachable and unchanged.
        primary = HTML[HTML.index("action-popup-primary") : HTML.index("action-popup-secondary")]
        assert "action-whisper-btn" in primary
        assert 'id="action-suggest-btn"' in HTML

    def test_turn_payload_carries_audience_only_when_selected(self) -> None:
        assert re.search(
            r"audience:\s*whisperAudience\.length\s*\?\s*whisperAudience\s*:\s*undefined",
            APP,
        )

    def test_whisper_requires_speech_or_action_client_side(self) -> None:
        assert "whisperAudience.length && !speech && !action" in APP
        assert "action.whisperNeedsContent" in APP

    def test_selection_never_silently_persists(self) -> None:
        # Cleared on the committed-turn success path.
        assert "clearWhisperSelection();" in APP
        assert APP.index("state.canUndo = true;\n        clearWhisperSelection();") > 0

    def test_controlled_character_is_never_a_whisper_target(self) -> None:
        populate = APP[APP.index("function populateWhisperOptions") :]
        assert "cid === state.controlledId) continue" in populate[:600]


class TestWhisperedRendering:
    def test_history_records_with_audience_render_a_badge(self) -> None:
        assert "msg-whisper-badge" in APP
        assert "whisperNamesFor(responseBuffer.audience)" in APP
        assert "record.audience != null" in APP

    def test_badge_uses_localized_label(self) -> None:
        assert "msg.whisperTo" in APP

    def test_i18n_keys_exist_in_both_languages(self) -> None:
        for key in (
            "action.whisperTitle",
            "action.whisperHeading",
            "action.whisperNeedsContent",
            "msg.whisperTo",
        ):
            assert I18N.count(f"'{key}'") >= 2, key

    def test_styles_exist(self) -> None:
        assert ".whisper-popup" in CSS
        assert ".msg-whisper-badge" in CSS
