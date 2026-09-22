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
`talim_shakli` values `Kunduzgi`/`Kechki`/`Masofaviy`/`Dual` = full-time/evening/distance/dual,
`fanlar_juftligi` = ordered exam-subject pair (`1-fan + 2-fan`), `tuman kvotasi` = district-targeted quota.

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

`.gitignore` excludes `/data/` (root only — `src/data/` is tracked), `venv/` and `.env`. Hand-made inputs
that notebooks depend on must therefore live **outside** `data/` — currently `references/`.

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
APPLICANTS
data/raw/abiturents.csv    (1.79M rows = every 2026 selection participant × each program they chose,
                            ~5 choices each; min score 56.7)
  -> data/raw/abt_unique.csv          (one row per applicant ID, 357,561)
  -> 01: join with Fanlar_majmuasi_2025-2026.xlsx by program name to attach `1-fan`/`2-fan`,
         keep only ismi/ID/toplagan_bali/1-fan/2-fan (~13k unmatched applicants dropped)
  -> data/processed/real_abts.csv     (344,701)
  -> 03: data understanding (read-only)
  -> 04: unify "Kasbiy (ijodiy) imtihon" spelling, add `fanlar_juftligi` and `qoshimcha_ball` (>189),
         drop `ismi`
  -> data/processed/abts_prepared.csv (344,701 × 6)

PROGRAMS
data/raw/otm_2026.csv      (one row per program×language×form: quotas and cut-off scores, NaN = no seats)
  -> [no notebook in the repo any more] 6 missing `talim_shakli` hand-patched, fillna(0)
  -> data/processed/final_otm_2026.csv  (5,712)
  -> 05: data understanding (read-only)
  -> 06: drop duplicates and no-quota rows, merge TDIU "Davlat auditi" key collision (quotas summed),
         0 score -> NaN where quota is 0, add `asosiy_yunalish`/`tuman_kvotasi`/`tuman`, attach
         `1-fan`/`2-fan`/`fanlar_juftligi` (source recorded in `fan_moslik`), derive competition markets
         (`bozor`) from co-applications in abiturents.csv
  -> data/processed/otm_prepared.csv    (5,547 × 17)  +  data/processed/bozorlar.csv (juftlik -> bozor)

FEATURES
07: abiturents.csv + otm_prepared + bozorlar -> every applicant assigned to one market
  -> data/processed/nomzodlar.csv       (357,561: ID, bozor, toplagan_bali)
  -> market features, group-within-market features, relative targets (`grant_ulush`, `shartnoma_ulush`)
  -> data/processed/model_data.csv      (5,547 × 31)
```

**Competition unit is the `bozor`, not `fanlar_juftligi`.** An applicant has one score for all choices and
may apply to several subject pairs (e.g. `Matematika + Fizika` and `Fizika + Matematika`, or `Ingliz tili +
Ona tili` and `Chet tili + Ona tili`). Pairs sharing ≥ 30 applicants are merged by union-find: 38 pairs →
32 markets, and every applicant's choices fall in exactly one market. `abts_prepared.csv` (from `04`) lacks
12,860 applicants whose programs `01` could not match — use `nomzodlar.csv` for anything competition-related.
Subject aliases normalized everywhere: `Kasbiy (ijodiy) imtihon` → `Kasbiy (ijodiy imtihon)`,
`Oʻzbek tili va adabiyoti` → `Ona tili va adabiyoti`.

The two OTM-side tables connect to applicants **only through `bozor`**. Subject lookup in `06` is, in order:
exact match on a normalized name (lowercase, unified apostrophes, parentheses stripped) against the Fanlar
majmuasi xlsx; a small typo dictionary; `references/kirish_imtihon_fanlari.md` for 14 new 2026 programs
(parsed as Markdown tables; where it says "Fizika (yoki …)", the first option is used — user-confirmed);
finally the part before `:` (e.g. `Sport faoliyati: voleybol` → `Sport faoliyati`). Fuzzy matching was
rejected because it maps language programs to the wrong language (e.g. pushtu → rus).

Notebooks are numbered and run in order from `notebooks/`. `02` is a one-off scraping scratchpad.
Notebooks `03`–`06` were generated/extended with `nbformat` scripts and executed with
`jupyter nbconvert --to notebook --execute --inplace`, so committed notebooks include outputs. Each ends
with a markdown "Xulosa"/"Natija" section listing findings and decisions — keep it in sync when changing
cells.

## Modeling constraints (decided with the user)

- **Admission rules changed in 2026:** applicants now sit the exam first, learn their score, and only then
  choose programs; everyone with ≥ 56.7 can take part. Earlier years (choose first, then exam) are not
  comparable, and detailed applicant data exists only for 2026 — **model on 2026 only**.
- **Leakage:** applicants' program choices (`otm_nomi`, `yonalishi`, `shifr_kodi`, `talim_tili`,
  `talim_shakli` in `abiturents.csv`/`abt_unique.csv`) are published after the mandate and must never become
  features. Applicant **scores and subject pairs** are known before choosing, so competition features built
  from them (counts, score quantiles per `fanlar_juftligi`) are allowed.
- **Targets:** `grant_bali` and `shartnoma_bali`, modeled separately, each trained only on rows whose quota
  is > 0. Quotas, OTM, program, language, form, region and subject pair are known in advance and are
  valid features. Grant seats exist almost only for `Kunduzgi`.
- Because a 2026-trained model would be applied to a later year, a relative target (share of the subject
  pair's applicants scoring above the cut-off) is being considered alongside raw scores.

## Stale code

`scratch/create_ml_notebook.py` and `scratch/check_2025.py` target a multi-year (2021–2025)
`data/processed/admission_combined.csv` that was never built. That plan is **obsolete** given the
constraints above — don't revive it. `models/` and `reports/figures/` are empty.

`scratch/` also holds throwaway HTML-structure probes against abt.uz and oliygoh.uz (`inspect_*.py`,
`find_years.py`) — exploratory, not part of any pipeline.
