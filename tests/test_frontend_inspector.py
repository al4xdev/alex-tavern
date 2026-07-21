from pathlib import Path

import pytest

from tools.frontend_inspector import (
    FrontendInspectionError,
    _parse_steps,
    _validate_request,
)


def validate(**overrides: object) -> None:
    values = {
        "url": "http://127.0.0.1:8889",
        "output_path": Path("/tmp/alex-tavern-frontend/test.png"),
        "browser": "chromium",
        "width": 1365,
        "height": 900,
        "timeout_ms": 15_000,
        "steps": [],
    }
    values.update(overrides)
    _validate_request(**values)  # type: ignore[arg-type]


def test_request_accepts_bounded_typed_steps() -> None:
    validate(
        steps=[
            {"action": "click", "selector": "#sessions-btn"},
            {"action": "fill", "selector": "#input-speech", "value": "Hello"},
            {"action": "press", "selector": "#input-speech", "value": "Enter"},
            {"action": "select_option", "selector": "#language", "value": "pt-BR"},
            {"action": "wait_for", "selector": ".message"},
            {"action": "wait", "value": "250"},
        ]
    )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"url": "file:///tmp/page.html"}, "absolute http"),
        ({"output_path": Path("/home/example/out.png")}, "under /tmp"),
        ({"browser": "system-firefox"}, "browser must be"),
        ({"width": 100}, "viewport"),
        ({"timeout_ms": 0}, "timeout_ms"),
        ({"steps": [{"action": "evaluate", "value": "alert(1)"}]}, "action must be"),
        ({"steps": [{"action": "click"}]}, "requires a selector"),
        ({"steps": [{"action": "fill", "selector": "#x"}]}, "requires a value"),
        ({"steps": [{"action": "wait", "value": "10001"}]}, "wait must be"),
    ],
)
def test_request_rejects_unsafe_or_unbounded_inputs(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(FrontendInspectionError, match=message):
        validate(**overrides)


def test_steps_cli_value_is_a_json_array_of_objects() -> None:
    assert _parse_steps('[{"action":"click","selector":"#x"}]') == [
        {"action": "click", "selector": "#x"}
    ]
    with pytest.raises(Exception, match="JSON array"):
        _parse_steps('{"action":"click"}')
