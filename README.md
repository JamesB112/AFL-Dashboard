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

The following app is used to visualise some of the analysis I have been doing, including:

1. Home - Page to summarise model performance for the season
2. Tip breakdown - A detailed page of each tipped game, including key drivers
3. Team Performance - A overview of how the team has been performining
4. Player Performance - A view on how each player has been ranked, as well as their historical progression over time
5. Model Performance - Analysis of how the model has performed across seasons and by team
6. Methodology - A summary of my approach
7. Q/A - Additional insights about the project

This is still a work in process, both in terms of the dashboard itself, and the modelling process, but still in a digestable form.

The actual end-to-end modelling process is run separately, but some of the key tables have been uploaded here to explore if you wish.

## Acknowledgements

I acknowledgements I have used the following data sources:

- fitzRoy (https://cran.r-project.org/web/packages/fitzRoy/index.html)
- Footywire (https://www.footywire.com/)
- Odds Portal (https://www.oddsportal.com/aussie-rules/australia/afl-2025/results/#/page/1/)
