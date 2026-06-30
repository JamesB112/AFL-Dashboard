# TIPPO — AFL Analytics (Streamlit)

A personal app covering AFL team performance, player rankings, and a
margin-prediction model — built on round-by-round data from 2012 onwards.

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

## Comments 

This is a work in process, both in terms of the dashboard itself, and the modelling process.

Expect major updates when I get the change to work though implementing required changes


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
