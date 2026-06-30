# Boundary Line — AFL Analytics (Streamlit)

A personal portfolio app covering AFL team performance, player rankings, and a
margin-prediction model — built on round-by-round data since 2012.

## Structure

```
afl-streamlit/
├── app.py              ← the whole app (sidebar nav + all page sections)
├── data_loader.py       ← cached CSV loading & aggregation
├── requirements.txt
├── .streamlit/
│   └── config.toml      ← theme (paper/green editorial look)
└── data/                ← put your CSV exports here
    ├── Predictions.csv
    ├── STG_Coaches_Votes.csv
    ├── STG_Fixture.csv
    ├── STG_Game_Lookup.csv
    ├── STG_Game_Player_Combined.csv
    ├── STG_Game_Positions.csv
    ├── STG_Game_Results.csv
    ├── STG_Game_Scoreworm.csv
    ├── STG_Player_Linkage.csv
    └── STG_Player_Rankings.csv
```

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`.

## Updating data after each round

Just overwrite the CSVs in `data/` with your new exports — same filenames,
same column structure. Reload the app (or it'll pick up the change
automatically on the next interaction) and everything downstream — tables,
charts, leaderboards, accuracy stats — recalculates from the new data.

There's no separate build step. Streamlit caches each file's processed
result by content hash (`@st.cache_data`), so loading is fast on repeat
visits but always reflects whatever's currently in `data/`.

If you ever want to force a full cache clear (e.g. after a structural change
to one of the CSVs), use the "⋮" menu in the running app → **Clear cache**,
or just restart the app.

## Deploying

The easiest path is **Streamlit Community Cloud** (free, made for exactly
this): push this folder to a GitHub repo and connect it at
share.streamlit.io. It installs `requirements.txt` automatically and gives
you a public URL.

Alternatively, any host that can run a long-lived Python process works
(Render, Railway, a VPS, etc.) — just run `streamlit run app.py --server.port
$PORT --server.address 0.0.0.0`.

**Note on data size:** `STG_Game_Player_Combined.csv` (~54MB),
`STG_Game_Scoreworm.csv` (~28MB), and `STG_Player_Rankings.csv` (~33MB) are
the largest files. If you're on GitHub, check your repo's file size limits —
GitHub blocks individual files over 100MB outright and warns above 50MB. All
three of these are currently under that ceiling, but worth keeping an eye on
as more seasons accumulate. If they grow past it, Git LFS or an external
storage bucket (S3, GCS) the app downloads from on startup are the usual
fixes.

## Notes on the app

- **Caching**: every load/aggregation function in `data_loader.py` is wrapped
  in `@st.cache_data`, so the expensive parses (the 50MB+ files) only run
  once per unique file content — not once per click.
- **Charts**: built with Plotly for interactive hover/zoom. The shared
  `PLOTLY_LAYOUT` dict in `app.py` controls the consistent paper/green look
  across all charts — tweak it once to restyle everywhere.
- **Player detail game logs**: pulled live from `STG_Game_Player_Combined.csv`
  for whichever player is selected, so there's no "top N players only"
  limitation like a pre-baked static site would need — every player in the
  dataset has a full detail view.
- **Blog/Q&A posts**: currently hardcoded placeholders in the `posts` list
  inside the Blog/Q&A page section of `app.py`. Swap in your real write-ups,
  or — if you want to manage posts without touching code — let me know and
  I can wire that section up to read from a `posts.csv` or similar instead.

## Known data note

One row in `STG_Game_Results.csv` (Collingwood vs Port Adelaide, 2026-06-20,
Match 11530) shows a 1–0 final score with 0 goals each — looks like a
partially-updated live row in the source export rather than an app issue.
Worth checking on your next refresh.
