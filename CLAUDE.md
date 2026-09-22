# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Predicting admission cut-off scores ("o'tish ballari") for Uzbek higher-education institutions (OTM) from
mandat.uzbmb.uz data. The repo is a data pipeline + notebook analysis project, not an application.

`classify_reviews.py` is a **separate, unrelated task**: sentiment classification of Yelp reviews via the
TypeSafe System One (Jev) API. It shares only the venv and `data/processed/`.

## Language conventions

All code comments, docstrings, log messages, CLI help text, and notebook prose are written in **Uzbek**.
Column names are Uzbek too (`otm_nomi`, `yunalish_nomi`, `talim_tili`, `talim_shakli`, `toplagan_bali`,
`grant_bali`, `shartnoma_bali`). Follow this when adding code — do not switch to English.

Domain terms: `grant` = state-funded seat, `shartnoma` = contract/paid seat, `kvota` = seat count,
`abituriyent` = applicant, `yunalish`/`yonalishi` = degree program, `hudud` = region,
`Kunduzgi`/`Kechki`/`Sirtqi` = full-time/evening/correspondence.

## Environment & commands

```powershell
.\venv\Scripts\Activate.ps1          # Python 3.13 venv (created from Anaconda base)
pip install -r requirements.txt
```

Always run scripts **from the project root** — `src/data/otm_data_scrape.py` and `classify_reviews.py`
use paths relative to the current working directory (`scrape_all.py` is the exception; it resolves the
project root from `__file__`).

```powershell
python src\data\scrape_all.py                    # applicant-level scrape -> data/raw/abiturents.csv
python src\data\otm_data_scrape.py               # program-level scrape  -> data/raw/otm_2026.csv
python classify_reviews.py --limit 10            # sentiment run on a small slice
python classify_reviews.py -t "some review"      # single-text smoke test, no CSV needed
python scratch\test_classify.py                  # only test in the repo; plain asserts, no pytest
jupyter lab                                      # notebooks read ../data/..., run them from notebooks/
```

`requirements.txt` lists `selenium`, but `src/data/otm_data_scrape.py` actually uses **Playwright**, which is
neither in requirements nor installed in `venv`. Install it (`pip install playwright && playwright install
chromium`) before running that scraper, or the import fails.

`.env` (git-ignored, project root) holds `TYPESAFE_API_KEY` and `OPENROUTER_API_KEY`. Only the first is used
by current code. `.claudeignore` excludes `data/`, so CSVs are not auto-read into context — inspect them with
explicit `head`/pandas calls.

## Windows/UTF-8 requirement

Uzbek and Russian text breaks on the default cp1252 console. Every script that prints starts with
`sys.stdout.reconfigure(encoding='utf-8')`, and every `to_csv`/`open` passes `encoding='utf-8'`. Keep doing
this in new scripts; when running one-off Python from the shell, set `PYTHONIOENCODING=utf-8`.

## Resume/checkpoint architecture

Every long-running job is designed to be killed and restarted — this is the dominant design constraint,
since full scrapes take hours and the API classification run covers ~28k rows.

- `scrape_all.py` — appends rows to `abiturents.csv` as it goes and `f.flush()`es each page. On restart it
  re-reads the CSV, builds a `completed_groups` set of `(otm, yunalish, til, shakl)` tuples, and **drops the
  last group** from that set because it may have been written half-finished.
- `otm_data_scrape.py` — two-phase: first enumerates every region×university×program×language×form dropdown
  combination into `data/raw/combinations.json`, then iterates it, writing `data/raw/progress.json`
  (`{"last_index": i}`) after each combination. Deleting `combinations.json` forces re-enumeration; deleting
  `progress.json` restarts the scrape from index 0. It also retries CSV writes in a loop because the output
  is often open in Excel on Windows.
- `classify_reviews.py` — async with an `asyncio.Semaphore` for concurrency, processes `pending_indices` in
  chunks and rewrites the whole output CSV every `--checkpoint-interval` rows. On restart it merges prior
  results back in by `review_id` when present, else positionally. `--no-resume` starts clean.

Rate limiting is deliberate (`time.sleep(0.3)` per program, `asyncio.sleep(1)` per combination) to avoid
hammering the government site — don't remove it.

## Data flow

```
data/raw/abiturents.csv    (1.8M rows, one row per admitted applicant, with duplicates across programs)
  -> data/raw/abt_unique.csv        (deduplicated, ~357k)
  -> notebooks/01: join with Fanlar_majmuasi_2025-2026.xlsx on a lowercased/stripped `join_key`
                   built from program name, to attach the two subject columns (`1-fan`, `2-fan`)
  -> data/processed/real_abts.csv

data/raw/otm_2026.csv      (one row per program×language×form, with quota counts and cut-off scores)
  -> notebooks/03: hand-patches ~6 rows with a missing `talim_shakli` by index, then fillna(0)
  -> data/processed/final_otm_2026.csv
```

Notebooks are numbered and meant to be run in order: `01` builds `real_abts.csv`, `02` is a scraping
scratchpad, `03` cleans the OTM table, `04` is EDA on applicant scores. Several were generated by the
`scratch/create_*_notebook.py` scripts via `nbformat` rather than authored in Jupyter; if you need to
regenerate one wholesale, edit the generator, otherwise edit the `.ipynb` directly.

## Unbuilt / in-progress work

`scratch/create_ml_notebook.py` and `scratch/check_2025.py` reference
`data/processed/admission_combined.csv` — a multi-year (2021–2025) table with `yil`, `grant_ball`,
`shartnoma_ball`, `is_grant_available`, `is_shartnoma_available` columns. **That file does not exist yet**,
and neither does the ML notebook it would feed. `models/` and `reports/figures/` are empty.

The intended modeling split, per the generator script: XGBoost regression with label-encoded language/form
and target-encoded university name; grant model trains on 2021–2023 and tests on 2024 (2025 has no grant
data), contract model trains on 2021–2024 and tests on 2025.

`scratch/` also holds throwaway HTML-structure probes against abt.uz and oliygoh.uz (`inspect_*.py`,
`find_years.py`) — exploratory, not part of any pipeline.
