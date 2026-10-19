# AI News Newsletter — Archive

Every edition of Zain Aziz's daily AI news newsletter, published as a static site:

**https://zanyaziz.github.io/ai-news-newsletter/**

- `index.html` — landing page listing all editions, newest first, paginated 10 per page.
- `editions/YYYY-MM-DD.html` — one self-contained HTML page per daily edition.
- `scripts/build_index.py` — regenerates `index.html` from `editions/` (and adds the
  "← All editions" bar to any edition page that lacks it). Run it after adding an edition:

  ```bash
  python3 scripts/build_index.py
  ```

A new edition is added every morning by the daily newsletter job: the day's page is
saved to `editions/`, the index is rebuilt, and the change is committed and pushed.

The editions for September 14, October 4, October 11, and October 12, 2026 were
originally delivered in chat without their HTML being archived; they were rebuilt from
the surviving research files on October 18, 2026 and are now part of the archive.
No edition was published on September 22, 2026.
