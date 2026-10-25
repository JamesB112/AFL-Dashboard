# TIPPO — AFL Analytics (Streamlit)

A personal web app to present my persobnal AFL analytics, covering AFL team performance, player rankings, and a
margin-prediction model. Includes data from 2012 onwards.

Link to current website: https://tippo-afl-analytics.streamlit.app/


## Structure

```
afl-streamlit/
├── app.py               ← the main application
├── data_loader.py       ← data related functions used by the app
├── requirements.txt
├── .streamlit/
│   └── config.toml      ← theme (paper/green editorial look)
└── data/                ← data sources used by the app, but broadly by the prediction model
    ├── Predictions.csv                 ← all predictions
    ├── STG_Coaches_Votes.csv           ← scraped coaches votes
    ├── STG_Fixture.csv                 ← fixture
    ├── STG_Game_Lookup.csv             ← lookup table for games 
    ├── STG_Game_Player_Combined.csv    ← a player stats table with some additional data added to it (e.g. Age)
    ├── STG_Game_Positions.csv          ← positions for each game
    ├── STG_Game_Results.csv            ← game results
    ├── STG_Game_Scoreworm.csv          ← the scoring timeline of a game
    ├── STG_Player_Linkage.csv          ← a player lookup table to join from several sources
    ├── Ladder_Projection.csv           ← the projected ladder
    ├── FTG_Elo_Ratings.csv             ← each team's elo rating, across time
    ├── data_version.csv                ← meta data of when data was last retrieved
    └── STG_Player_Rankings.csv         ← my player ratings data
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
