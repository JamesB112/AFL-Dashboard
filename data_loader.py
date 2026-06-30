"""
data_loader.py
================
Cached data loading & aggregation for the Boundary Line AFL Analytics app.

All raw CSVs are read once per file (cached by Streamlit on file content),
then aggregated into the shapes each page needs. To update data, just
overwrite the CSVs in DATA_DIR with new exports of the same structure —
no separate build step required, Streamlit's cache invalidates automatically
when file contents change.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

FILES = {
    "predictions": "Predictions.csv",
    "coaches_votes": "STG_Coaches_Votes.csv",
    "fixture": "STG_Fixture.csv",
    "game_lookup": "STG_Game_Lookup.csv",
    "game_player_combined": "STG_Game_Player_Combined.csv",
    "game_positions": "STG_Game_Positions.csv",
    "game_results": "STG_Game_Results.csv",
    "game_scoreworm": "STG_Game_Scoreworm.csv",
    "player_linkage": "STG_Player_Linkage.csv",
    "player_rankings": "STG_Player_Rankings.csv",
}

NUMERIC_STAT_COLS = [
    "GA", "CP", "UP", "ED", "DE", "CM", "MI5", "One.Percenters", "BO", "TOG",
    "K", "HB", "D", "M", "G", "B", "T", "HO", "I50", "CL", "CG", "R50", "FF",
    "FA", "AF", "SC", "CCL", "SCL", "SI", "MG", "TO", "ITC", "T5",
]

STAT_LABELS = {
    "K": "Kicks", "HB": "Handballs", "D": "Disposals", "M": "Marks",
    "G": "Goals", "B": "Behinds", "T": "Tackles", "HO": "Hitouts",
    "I50": "Inside 50s", "CL": "Clearances", "CG": "Clangers",
    "R50": "Rebound 50s", "FF": "Frees For", "FA": "Frees Against",
    "AF": "AFL Fantasy", "SC": "SuperCoach", "CCL": "Centre Clearances",
    "SCL": "Stoppage Clearances", "SI": "Score Involvements",
    "MG": "Metres Gained", "TO": "Turnovers", "ITC": "Intercepts",
    "T5": "Tackles Inside 50", "CP": "Contested Possessions",
    "UP": "Uncontested Possessions", "ED": "Effective Disposals",
    "DE": "Disposal Efficiency %", "CM": "Contested Marks",
    "MI5": "Marks Inside 50", "One.Percenters": "One Percenters",
    "BO": "Bounces", "TOG": "Time on Ground %", "GA": "Goal Assists",
}


def _path(key):
    return os.path.join(DATA_DIR, FILES[key])


def data_files_present():
    """Returns (all_present: bool, missing: list[str])."""
    missing = [fname for fname in FILES.values() if not os.path.exists(os.path.join(DATA_DIR, fname))]
    return len(missing) == 0, missing


@st.cache_data(show_spinner=False)
def load_raw(key):
    return pd.read_csv(_path(key), low_memory=False)


# ----------------------------------------------------------------------
# TEAM PERFORMANCE
# ----------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_team_results():
    """Full game-level results, one row per team-perspective per game."""
    df = load_raw("game_results")
    df["Season"] = df["Season"].astype(str)
    df["RoundNumber"] = pd.to_numeric(df["RoundNumber"], errors="coerce")
    df["Margin"] = pd.to_numeric(df["Margin"], errors="coerce")
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")
    df["Opposition_Points"] = pd.to_numeric(df["Opposition_Points"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def get_team_season_summary():
    """One row per team per season: W/L/D, percentage, avg margin etc."""
    df = get_team_results()
    grp = df.groupby(["Team", "Season"], as_index=False).agg(
        Played=("Match_id", "count"),
        Wins=("Result", lambda s: (s == "W").sum()),
        Losses=("Result", lambda s: (s == "L").sum()),
        Draws=("Result", lambda s: (s == "D").sum()),
        Points_For=("Points", "sum"),
        Points_Against=("Opposition_Points", "sum"),
        Avg_Margin=("Margin", "mean"),
    )
    grp["Win_Pct"] = (grp["Wins"] / grp["Played"] * 100).round(1)
    grp["Percentage"] = (grp["Points_For"] / grp["Points_Against"].replace(0, np.nan) * 100).round(1)
    grp["Avg_Margin"] = grp["Avg_Margin"].round(1)
    return grp.sort_values(["Season", "Win_Pct"], ascending=[False, False])


@st.cache_data(show_spinner=False)
def get_all_teams():
    return sorted(get_team_results()["Team"].dropna().unique().tolist())


@st.cache_data(show_spinner=False)
def get_all_seasons():
    seasons = get_team_results()["Season"].dropna().unique().tolist()
    return sorted(seasons, reverse=True)


# ----------------------------------------------------------------------
# PLAYER PERFORMANCE
# ----------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_player_rankings():
    df = load_raw("player_rankings")
    df["Season"] = df["Season"].astype(str)
    df["RoundNumber"] = pd.to_numeric(df["RoundNumber"], errors="coerce")
    df["Rank_Overall"] = pd.to_numeric(df["Rank_Overall"], errors="coerce")
    df["composite_score"] = pd.to_numeric(df["composite_score"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def get_latest_rankings():
    """Rankings for the most recent season + round present in the data."""
    df = get_player_rankings()
    latest_season = df["Season"].max()
    latest_round = df.loc[df["Season"] == latest_season, "RoundNumber"].max()
    latest = df[(df["Season"] == latest_season) & (df["RoundNumber"] == latest_round)].copy()
    latest = latest.sort_values("Rank_Overall")
    return latest, latest_season, int(latest_round)


@st.cache_data(show_spinner=False)
def get_player_rank_history(draft_id, season):
    df = get_player_rankings()
    h = df[(df["Draft_Player_Id"] == draft_id) & (df["Season"] == season)].copy()
    return h.sort_values("RoundNumber")


@st.cache_data(show_spinner=False)
def get_player_game_log():
    df = load_raw("game_player_combined")
    df["Season"] = df["Season"].astype(str)
    df["RoundNumber"] = pd.to_numeric(df["RoundNumber"], errors="coerce")
    for col in NUMERIC_STAT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def get_player_season_leaderboard(season):
    df = get_player_game_log()
    season_df = df[df["Season"] == season].copy()

    agg_dict = {col: "sum" for col in NUMERIC_STAT_COLS if col in season_df.columns}
    grp = season_df.groupby("Player", as_index=False).agg(
        Games=("Match_id", "count"),
        Team=("Team", "last"),
        Position=("Position_Final", "last"),
        **{f"{c}_total": (c, "sum") for c in agg_dict},
    )
    for c in agg_dict:
        grp[f"{c}_avg"] = (grp[f"{c}_total"] / grp["Games"]).round(1)
        grp[f"{c}_total"] = grp[f"{c}_total"].round(1)
    return grp


@st.cache_data(show_spinner=False)
def get_player_career_log(player_name):
    df = get_player_game_log()
    log = df[df["Player"] == player_name].copy()
    return log.sort_values(["Season", "RoundNumber"])


# ----------------------------------------------------------------------
# MODEL PREDICTIONS
# ----------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_predictions():
    df = load_raw("predictions")
    df["Season"] = df["Season"].astype(str)
    df["RoundNumber"] = pd.to_numeric(df["RoundNumber"], errors="coerce")
    df["Margin"] = pd.to_numeric(df["Margin"], errors="coerce")
    df["Predicted_Margin"] = pd.to_numeric(df["Predicted_Margin"], errors="coerce")
    df["Predicted_Margin_Adjusted"] = pd.to_numeric(df.get("Predicted_Margin_Adjusted", df["Predicted_Margin"]), errors="coerce")
    df["Predicted_Margin_Adjusted"] = df["Predicted_Margin_Adjusted"].fillna(df["Predicted_Margin"])
    df["Abs_Error"] = (df["Margin"] - df["Predicted_Margin_Adjusted"]).abs()
    df["Correct"] = df["Prediction_Outcome"] == 1
    return df


@st.cache_data(show_spinner=False)
def get_prediction_summary():
    df = get_predictions()
    by_season = df.groupby("Season", as_index=False).agg(
        Games=("Match_id", "count"),
        Correct=("Correct", "sum"),
        Mean_Abs_Error=("Abs_Error", "mean"),
    )
    by_season["Accuracy_Pct"] = (by_season["Correct"] / by_season["Games"] * 100).round(1)
    by_season["Mean_Abs_Error"] = by_season["Mean_Abs_Error"].round(2)
    by_season = by_season.sort_values("Season")

    overall = {
        "games": int(df.shape[0]),
        "correct": int(df["Correct"].sum()),
        "accuracy_pct": round(df["Correct"].sum() / df.shape[0] * 100, 1) if df.shape[0] else None,
        "mean_abs_error": round(df["Abs_Error"].mean(), 2) if df.shape[0] else None,
        "model": df["Model"].iloc[0] if df.shape[0] else None,
    }
    return by_season, overall


@st.cache_data(show_spinner=False)
def get_upcoming_fixture():
    df = load_raw("fixture")
    upcoming = df[df["RoundStatus"].isin(["Next Round", "Future Round"])].copy()
    return upcoming.sort_values("Date")


# ----------------------------------------------------------------------
# GLOBAL META
# ----------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_meta():
    teams = get_all_teams()
    latest_rankings, latest_season, latest_round = get_latest_rankings()
    _, pred_overall = get_prediction_summary()
    return {
        "teams_tracked": len(teams),
        "latest_season": latest_season,
        "latest_round": latest_round,
        "model_accuracy_pct": pred_overall["accuracy_pct"],
        "model_mae": pred_overall["mean_abs_error"],
        "model_games_scored": pred_overall["games"],
        "players_tracked": len(latest_rankings),
    }
