"""Repeatable headless frontend inspection for repository agents and the debug MCP."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_OUTPUT = Path("/tmp/alex-tavern-frontend/frontend.png")
SUPPORTED_BROWSERS = frozenset({"chromium", "firefox", "webkit"})
SUPPORTED_ACTIONS = frozenset({"click", "fill", "press", "select_option", "wait_for", "wait"})
MAX_TIMEOUT_MS = 60_000
MAX_WAIT_MS = 10_000
MIN_VIEWPORT = 240
MAX_VIEWPORT = 4_096


class FrontendInspectionError(RuntimeError):
    """Raised when an inspection request or browser run is invalid."""


def _validate_request(
    url: str,
    output_path: Path,
    browser: str,
    width: int,
    height: int,
    timeout_ms: int,
    steps: Sequence[dict[str, str]],
) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise FrontendInspectionError("url must be an absolute http:// or https:// URL")
    if browser not in SUPPORTED_BROWSERS:
        raise FrontendInspectionError(f"browser must be one of {sorted(SUPPORTED_BROWSERS)}")
    if not MIN_VIEWPORT <= width <= MAX_VIEWPORT or not MIN_VIEWPORT <= height <= MAX_VIEWPORT:
        raise FrontendInspectionError(
            f"viewport dimensions must be between {MIN_VIEWPORT} and {MAX_VIEWPORT}"
        )
    if not 1 <= timeout_ms <= MAX_TIMEOUT_MS:
        raise FrontendInspectionError(f"timeout_ms must be between 1 and {MAX_TIMEOUT_MS}")
    temp_root = Path("/tmp").resolve()
    if not output_path.resolve().is_relative_to(temp_root):
        raise FrontendInspectionError("output_path must resolve under /tmp")

    for index, step in enumerate(steps):
        action = step.get("action", "")
        if action not in SUPPORTED_ACTIONS:
            raise FrontendInspectionError(
                f"step {index} action must be one of {sorted(SUPPORTED_ACTIONS)}"
            )
        selector = step.get("selector", "").strip()
        value = step.get("value", "")
        if action != "wait" and not selector:
            raise FrontendInspectionError(f"step {index} requires a selector")
        if action in {"fill", "press", "select_option"} and not value:
            raise FrontendInspectionError(f"step {index} action {action!r} requires a value")
        if action == "wait":
            try:
                delay = int(value)
            except ValueError as exc:
                raise FrontendInspectionError(
                    f"step {index} wait value must be milliseconds"
                ) from exc
            if not 0 <= delay <= MAX_WAIT_MS:
                raise FrontendInspectionError(
                    f"step {index} wait must be between 0 and {MAX_WAIT_MS} milliseconds"
                )


async def inspect_frontend(
    url: str,
    *,
    output_path: Path = DEFAULT_OUTPUT,
    browser: str = "chromium",
    width: int = 1365,
    height: int = 900,
    wait_for: str = "body",
    timeout_ms: int = 15_000,
    steps: Sequence[dict[str, str]] = (),
    full_page: bool = True,
) -> dict[str, Any]:
    """Open a fresh headless page, run bounded steps, and capture inspectable evidence."""
    output_path = output_path.resolve()
    _validate_request(url, output_path, browser, width, height, timeout_ms, steps)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.async_api import Error as PlaywrightError
        from playwright.async_api import async_playwright
    except ImportError as exc:  # pragma: no cover - dependency sync is an operator boundary
        raise FrontendInspectionError(
            "Playwright is not installed; run `uv sync --group dev`"
        ) from exc

    console_messages: list[dict[str, str]] = []
    page_errors: list[str] = []
    try:
        async with async_playwright() as playwright:
            launcher = getattr(playwright, browser)
            try:
                browser_instance = await launcher.launch(headless=True)
            except PlaywrightError as exc:
                raise FrontendInspectionError(
                    f"Playwright {browser} is unavailable; run "
                    f"`uv run playwright install {browser}`"
                ) from exc
            try:
                context = await browser_instance.new_context(
                    viewport={"width": width, "height": height},
                    color_scheme="dark",
                )
                page = await context.new_page()

                def record_console(message: Any) -> None:
                    if message.type in {"warning", "error"} and len(console_messages) < 100:
                        console_messages.append({"type": message.type, "text": message.text})

                page.on("console", record_console)
                page.on("pageerror", lambda error: page_errors.append(str(error)))
                response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                if wait_for:
                    await page.locator(wait_for).wait_for(state="visible", timeout=timeout_ms)

                for step in steps:
                    action = step["action"]
                    selector = step.get("selector", "")
                    value = step.get("value", "")
                    if action == "click":
                        await page.locator(selector).click(timeout=timeout_ms)
                    elif action == "fill":
                        await page.locator(selector).fill(value, timeout=timeout_ms)
                    elif action == "press":
                        await page.locator(selector).press(value, timeout=timeout_ms)
                    elif action == "select_option":
                        await page.locator(selector).select_option(value, timeout=timeout_ms)
                    elif action == "wait_for":
                        await page.locator(selector).wait_for(state="visible", timeout=timeout_ms)
                    else:
                        await page.wait_for_timeout(int(value))

                await page.screenshot(path=output_path, full_page=full_page)
                body_text = await page.locator("body").inner_text(timeout=timeout_ms)
                return {
                    "url": page.url,
                    "title": await page.title(),
                    "http_status": response.status if response is not None else None,
                    "viewport": {"width": width, "height": height},
                    "browser": browser,
                    "screenshot_path": str(output_path),
                    "steps_completed": len(steps),
                    "console_messages": console_messages,
                    "page_errors": page_errors[:100],
                    "visible_text": body_text[:4_000],
                }
            finally:
                await browser_instance.close()
    except FrontendInspectionError:
        raise
    except PlaywrightError as exc:
        raise FrontendInspectionError(f"frontend inspection failed: {exc}") from exc


def _parse_steps(value: str) -> list[dict[str, str]]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"steps must be valid JSON: {exc}") from exc
    if not isinstance(parsed, list) or not all(isinstance(item, dict) for item in parsed):
        raise argparse.ArgumentTypeError("steps must be a JSON array of objects")
    return [{str(key): str(item_value) for key, item_value in item.items()} for item in parsed]


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture and inspect a live frontend with Playwright."
    )
    parser.add_argument("url")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--browser", choices=sorted(SUPPORTED_BROWSERS), default="chromium")
    parser.add_argument("--width", type=int, default=1365)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--wait-for", default="body")
    parser.add_argument("--timeout-ms", type=int, default=15_000)
    parser.add_argument("--steps", type=_parse_steps, default=[])
    parser.add_argument("--viewport-only", action="store_true")
    return parser.parse_args(argv)


def main() -> None:
    """Run one frontend inspection and print its machine-readable report."""
    args = _parse_args()
    try:
        result = asyncio.run(
            inspect_frontend(
                args.url,
                output_path=args.output,
                browser=args.browser,
                width=args.width,
                height=args.height,
                wait_for=args.wait_for,
                timeout_ms=args.timeout_ms,
                steps=args.steps,
                full_page=not args.viewport_only,
            )
        )
    except FrontendInspectionError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
