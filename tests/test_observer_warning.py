from pathlib import Path

ROOT = Path(__file__).parents[1]
APP = (ROOT / "src/static/app.js").read_text()
I18N = (ROOT / "src/static/i18n.js").read_text()


def test_observer_warning_is_derived_from_canonical_player_speech() -> None:
    assert "state.playerHasSpoken = records.some((record) =>" in APP
    assert "record.speaker === 'Player'" in APP
    assert "record.content_type === 'speech'" in APP
    assert "String(record.content || '').trim()" in APP
    assert "state.sessionId && !state.playerHasSpoken" in APP


def test_only_successful_effective_speech_dismisses_warning() -> None:
    success = "String(data.effective_input?.speech || '').trim()"
    assert success in APP
    assert APP.index(success) > APP.index("let data = await api.turn")
    assert "state.playerHasSpoken = true;\n            updateSpeechPlaceholder();" in APP


def test_warning_copy_is_localized_and_updates_on_locale_change() -> None:
    assert I18N.count("'input.speechObserver':") == 2
    assert "Continue lets the world speak without you" in I18N
    assert "Continuar deixa o mundo falar sem você" in I18N
    locale_callback = APP.index("onLocaleChange((locale) =>")
    assert APP.index("updateSpeechPlaceholder();", locale_callback) > locale_callback
