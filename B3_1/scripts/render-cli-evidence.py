#!/usr/bin/env python3
"""Capture real saved AWS CLI output in a readable browser screenshot.

The input file must contain command output from an actual verification run.
This script only formats that output; it does not invent AWS responses.
"""

import argparse
import html
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    output = args.input.read_text(encoding="utf-8")
    if not output.strip():
        parser.error("input file is empty; no evidence to capture")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    document = f"""<!doctype html>
<html lang="ko"><meta charset="utf-8"><title>{html.escape(args.title)}</title>
<style>
  * {{box-sizing:border-box}}
  body {{margin:0;padding:42px;background:#f4f7fb;color:#122039;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo',sans-serif}}
  main {{max-width:1180px;margin:auto}}
  h1 {{margin:0 0 8px;font-size:30px}}
  p {{margin:0 0 28px;color:#56647a;font-size:16px}}
  .terminal {{border-radius:16px;overflow:hidden;background:#101827;box-shadow:0 14px 35px #18294526}}
  .bar {{padding:15px 20px;background:#1d293b;color:#d7e1f1;font-size:15px}}
  .dot {{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;background:#f26d6d}}
  .dot:nth-child(2) {{background:#f0c45a}} .dot:nth-child(3) {{background:#69c779;margin-right:20px}}
  pre {{margin:0;padding:24px 28px;white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.55 Menlo,Consolas,monospace;color:#e6edf8}}
  .command {{color:#83d6aa;border-bottom:1px solid #39475c}}
  footer {{margin-top:20px;color:#63738b;font-size:13px}}
</style>
<main><h1>{html.escape(args.title)}</h1>
<p>실제 AWS CLI 출력 캡처 · 민감한 계정 식별자는 공개 전 제거</p>
<div class="terminal"><div class="bar"><span class="dot"></span><span class="dot"></span><span class="dot"></span>B3_1 · ap-northeast-2</div>
<pre class="command">$ {html.escape(args.command)}</pre><pre>{html.escape(output)}</pre></div>
<footer>원문: {html.escape(args.input.name)} · 화면은 저장된 CLI 출력을 그대로 표시합니다.</footer></main></html>"""

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=1)
        page.set_content(document)
        page.screenshot(path=str(args.output), full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
