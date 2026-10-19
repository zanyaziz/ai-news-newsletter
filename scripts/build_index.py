#!/usr/bin/env python3
"""Regenerate the archive landing page (index.html) from editions/*.html.

- One entry per edition file named YYYY-MM-DD.html, newest first.
- Headline = first non-empty <h1>, else first non-empty <h2>, else the title.
- Pagination is client-side in the generated page, 10 editions per page.
- Also injects an idempotent "← All editions" bar into each edition page.
Run from anywhere:  python3 scripts/build_index.py
"""
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EDITIONS = ROOT / "editions"
PAGE_SIZE = 10

# Editions that were delivered in chat but whose HTML was never archived
# (the live page was overwritten the next day). The four former gaps
# (Sep 14, Oct 4, Oct 11, Oct 12, 2026) were rebuilt from the surviving
# research files on Oct 18, 2026, so this list is now empty.
# Sep 22, 2026 had no edition (kept as a standing note below).
GAPS = []


def clean(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def extract_headline(source: str) -> str:
    for tag in ("h1", "h2"):
        for m in re.finditer(rf"<{tag}[^>]*>(.*?)</{tag}>", source, re.S | re.I):
            text = clean(m.group(1))
            if text:
                return text
    m = re.search(r"<title[^>]*>(.*?)</title>", source, re.S | re.I)
    return clean(m.group(1)) if m else "AI News Newsletter"


def inject_back_bar(path: Path) -> None:
    source = path.read_text(errors="ignore")
    if "ain-archive-bar" in source:
        return
    bar = (
        '<div id="ain-archive-bar" style="position:sticky;top:0;z-index:9999;'
        "background:#111827;color:#f9fafb;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;"
        'padding:10px 16px;font-size:14px;">'
        '<a href="../index.html" style="color:#93c5fd;text-decoration:none;">'
        "&larr; All editions &mdash; AI News Newsletter archive</a></div>\n"
    )
    m = re.search(r"<body[^>]*>", source, re.I)
    if m:
        source = source[: m.end()] + "\n" + bar + source[m.end():]
        path.write_text(source)


def main() -> None:
    entries = []
    for path in sorted(EDITIONS.glob("????-??-??.html"), reverse=True):
        stem = path.stem
        try:
            y, mo, d = (int(x) for x in stem.split("-"))
            pretty = date(y, mo, d).strftime("%A, %B %-d, %Y")
        except ValueError:
            continue
        inject_back_bar(path)
        entries.append(
            {
                "date": stem,
                "pretty": pretty,
                "headline": extract_headline(path.read_text(errors="ignore")),
                "href": f"editions/{path.name}",
            }
        )

    data_json = json.dumps(entries, ensure_ascii=False)
    gaps_html = (
        "<p class=\"gaps\">No edition was published on September 22, 2026.</p>"
    )
    if GAPS:
        gaps_html = (
            "<p class=\"gaps\">Archive gaps: the editions for "
            + ", ".join(GAPS)
            + " were delivered in chat but their HTML pages were not archived before the next day&rsquo;s edition replaced them. No edition was published on September 22, 2026.</p>"
        )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI News Newsletter — Archive</title>
<meta name="description" content="Every edition of Zain Aziz's daily AI news newsletter, newest first.">
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #111827; }}
  @media (prefers-color-scheme: dark) {{ body {{ background: #0b1220; color: #e5e7eb; }} .card {{ background: #111827 !important; border-color: #1f2937 !important; }} .date {{ color: #9ca3af !important; }} }}
  .wrap {{ max-width: 760px; margin: 0 auto; padding: 40px 20px 64px; }}
  header h1 {{ font-family: Georgia, "Times New Roman", serif; font-size: 40px; margin: 0 0 8px; }}
  header p {{ margin: 0 0 28px; color: #6b7280; font-size: 16px; }}
  .card {{ display: block; background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px 20px; margin: 0 0 12px; text-decoration: none; color: inherit; transition: border-color .15s ease, transform .15s ease; }}
  .card:hover {{ border-color: #93c5fd; transform: translateY(-1px); }}
  .date {{ font-size: 13px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; color: #6b7280; }}
  .latest {{ display: inline-block; margin-left: 8px; padding: 1px 8px; border-radius: 999px; background: #2563eb; color: #fff; font-size: 11px; letter-spacing: .03em; vertical-align: 2px; }}
  .headline {{ font-family: Georgia, "Times New Roman", serif; font-size: 21px; line-height: 1.35; margin-top: 6px; }}
  .pager {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; margin-top: 28px; }}
  .pager button {{ font: inherit; font-size: 14px; padding: 8px 14px; border-radius: 8px; border: 1px solid #d1d5db; background: transparent; color: inherit; cursor: pointer; }}
  .pager button[aria-current="page"] {{ background: #2563eb; border-color: #2563eb; color: #fff; }}
  .pager button:disabled {{ opacity: .4; cursor: default; }}
  .count {{ text-align: center; color: #6b7280; font-size: 14px; margin-top: 14px; }}
  footer {{ margin-top: 40px; color: #6b7280; font-size: 13px; line-height: 1.6; }}
  footer a {{ color: #2563eb; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>AI News Newsletter</h1>
    <p>A daily briefing on the biggest stories in AI &mdash; models, research, funding, products, and policy. Newest edition first.</p>
  </header>
  <main id="list" aria-live="polite"></main>
  <nav class="pager" id="pager" aria-label="Archive pages"></nav>
  <p class="count" id="count"></p>
  <footer>
    {gaps_html}
    <p>Published daily by Zain Aziz. Source on <a href="https://github.com/zanyaziz/ai-news-newsletter">GitHub</a>.</p>
  </footer>
</div>
<script>
const EDITIONS = {data_json};
const PAGE_SIZE = {PAGE_SIZE};
const listEl = document.getElementById('list');
const pagerEl = document.getElementById('pager');
const countEl = document.getElementById('count');
const totalPages = Math.max(1, Math.ceil(EDITIONS.length / PAGE_SIZE));
function currentPage() {{
  const p = parseInt(new URLSearchParams(location.search).get('page') || '1', 10);
  return Math.min(Math.max(1, isNaN(p) ? 1 : p), totalPages);
}}
function render() {{
  const page = currentPage();
  const start = (page - 1) * PAGE_SIZE;
  const items = EDITIONS.slice(start, start + PAGE_SIZE);
  listEl.innerHTML = items.map((e, i) => `
    <a class="card" href="${{e.href}}">
      <span class="date">${{e.pretty}}${{start + i === 0 ? '<span class="latest">Latest</span>' : ''}}</span>
      <div class="headline">${{e.headline}}</div>
    </a>`).join('');
  let buttons = `<button data-nav="prev" ${{page === 1 ? 'disabled' : ''}}>&larr; Newer</button>`;
  for (let p = 1; p <= totalPages; p++) {{
    buttons += `<button data-page="${{p}}" ${{p === page ? 'aria-current="page"' : ''}}>${{p}}</button>`;
  }}
  buttons += `<button data-nav="next" ${{page === totalPages ? 'disabled' : ''}}>Older &rarr;</button>`;
  pagerEl.innerHTML = buttons;
  countEl.textContent = `${{EDITIONS.length}} editions &middot; page ${{page}} of ${{totalPages}}`;
  pagerEl.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {{
    let target = page;
    if (btn.dataset.page) target = parseInt(btn.dataset.page, 10);
    if (btn.dataset.nav === 'prev') target = page - 1;
    if (btn.dataset.nav === 'next') target = page + 1;
    const url = new URL(location.href);
    if (target <= 1) url.searchParams.delete('page'); else url.searchParams.set('page', target);
    history.pushState(null, '', url);
    render();
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
  }}));
}}
window.addEventListener('popstate', render);
render();
</script>
</body>
</html>
"""
    (ROOT / "index.html").write_text(page)
    total_pages = max(1, -(-len(entries) // PAGE_SIZE))
    print(f"Wrote index.html with {len(entries)} editions, {total_pages} page(s) of {PAGE_SIZE}.")


if __name__ == "__main__":
    main()
