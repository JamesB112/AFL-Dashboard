# TIPPO — AFL Analytics (Streamlit)

A personal web app to present my persobnal AFL analytics, covering AFL team performance, player rankings, and a
margin-prediction model. Includes data from 2012 onwards.

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
