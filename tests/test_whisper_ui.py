"""Task 30: whisper/audience control in the frontend (static boundary tests)."""

from __future__ import annotations

import re
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "src" / "static"
APP = "\n".join(
    (STATIC / name).read_text(encoding="utf-8")
    for name in ("app.js", "transcript.js", "composer.js")
)
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
    def test_only_explicit_whispers_render_a_badge(self) -> None:
        assert "msg-whisper-badge" in APP
        assert "responseBuffer.audienceOrigin === 'whisper'" in APP
        assert "record.audience != null" in APP
        assert "responseBuffer.audienceOrigin = record.audience_origin" in APP

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


class TestTheRejectedTurnKeepsWhatTheUserTyped:
    """Task 30's second criterion, written and never tested.

    "A rejected audience (backend 422) shows the error toast and does not clear
    the composer." The behaviour was implemented correctly all along - what was
    missing is anything stopping a later edit from moving `clearWhisperSelection`
    or the input resets into a `finally`, which would silently destroy a
    whispered turn the user has to retype.

    Static boundary assertions, like the rest of this file: the composer is a
    module of imperative DOM code with no test harness, so the boundary is the
    source itself.
    """

    def _submit_body(self) -> str:
        """Everything from the success path to the end of the catch block."""
        start = APP.index("state.lastTurnFailed = false;\n        state.canUndo = true;")
        return APP[start : APP.index("} finally {", start)]

    def test_the_inputs_are_cleared_only_before_the_catch(self) -> None:
        body = self._submit_body()
        catch_at = body.index("} catch (err) {")
        after_failure = body[catch_at:]
        fields = ("inputSpeech.value = ''", "inputThought.value = ''", "inputAction.value = ''")
        for field in fields:
            assert field not in after_failure, (
                f"{field} runs on the failure path; the user loses what they typed"
            )

    def test_the_whisper_selection_survives_a_failure(self) -> None:
        body = self._submit_body()
        after_failure = body[body.index("} catch (err) {") :]
        assert "clearWhisperSelection()" not in after_failure, (
            "a rejected whisper would drop its audience, so the retry goes public"
        )

    def test_a_failure_raises_an_error_toast(self) -> None:
        body = self._submit_body()
        after_failure = body[body.index("} catch (err) {") :]
        assert "t('turn.failed'" in after_failure
        assert "'error'" in after_failure, "the toast must be styled as an error"

    def test_a_stopped_turn_is_not_reported_as_a_failure(self) -> None:
        """Pressing stop is a user decision, not a rejected audience."""
        body = self._submit_body()
        after_failure = body[body.index("} catch (err) {") :]
        assert "err.name === 'AbortError'" in after_failure
        assert "t('turn.stopped')" in after_failure

    def test_the_failure_message_exists_in_both_languages(self) -> None:
        assert I18N.count("'turn.failed':") == 2
        assert I18N.count("'turn.stopped':") == 2


class TestTheActionMenuIsNeverLeftStale:
    """Task 30's fourth criterion: the mobile action menu stays usable while a
    whisper is selected.

    The menu is where whisper, undo, retry and skip live on a phone. If a turn
    can end without refreshing it, a failed whispered turn leaves the retry
    button hidden with the audience still selected - the one state where the
    user most needs the menu.
    """

    def test_both_turn_outcomes_refresh_the_menu(self) -> None:
        start = APP.index("state.lastTurnFailed = false;\n        state.canUndo = true;")
        body = APP[start : APP.index("} finally {", start)]
        catch_at = body.index("} catch (err) {")
        assert "updateActionPopup();" in body[:catch_at], "success path never refreshes the menu"
        assert "updateActionPopup();" in body[catch_at:], "failure path never refreshes the menu"

    def test_the_retry_button_appears_exactly_when_the_turn_failed(self) -> None:
        assert "actionRetryBtn.style.display = state.lastTurnFailed ? '' : 'none'" in APP

    def test_the_whisper_button_needs_only_a_session(self) -> None:
        """Nothing about a pending selection may hide the control that edits it."""
        assert "whisperBtn.style.display = hasSession ? '' : 'none'" in APP
