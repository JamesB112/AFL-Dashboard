"""
data_loader.py
================
Cached data loading & aggregation for the Boundary Line AFL Analytics app.

Predictions format (current):
  - Two models: LOGIT (win/loss probability) and OLS (margin regression)
  - Feature importances per game for the OLS model
  - Dates in DD/MM/YYYY format
  - RoundStatus column present

To update data after each round, overwrite the CSVs in data/ and reload.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

FILES = {
    "predictions":          "Predictions.csv",
    "coaches_votes":        "STG_Coaches_Votes.csv",
    "fixture":              "STG_Fixture.csv",
    "game_lookup":          "STG_Game_Lookup.csv",
    "game_player_combined": "STG_Game_Player_Combined.csv",
    "game_positions":       "STG_Game_Positions.csv",
    "game_results":         "STG_Game_Results.csv",
    "game_scoreworm":       "STG_Game_Scoreworm.csv",
    "player_linkage":       "STG_Player_Linkage.csv",
    "player_rankings":      "STG_Player_Rankings.csv",
    "ladder_projection":    "Ladder_Projection.csv",
}

NUMERIC_STAT_COLS = [
    "GA","CP","UP","ED","DE","CM","MI5","One.Percenters","BO","TOG",
    "K","HB","D","M","G","B","T","HO","I50","CL","CG","R50","FF",
    "FA","AF","SC","CCL","SCL","SI","MG","TO","ITC","T5",
]

STAT_LABELS = {
    "K":"Kicks","HB":"Handballs","D":"Disposals","M":"Marks",
    "G":"Goals","B":"Behinds","T":"Tackles","HO":"Hitouts",
    "I50":"Inside 50s","CL":"Clearances","CG":"Clangers",
    "R50":"Rebound 50s","FF":"Frees For","FA":"Frees Against",
    "AF":"AFL Fantasy","SC":"SuperCoach","CCL":"Centre Clearances",
    "SCL":"Stoppage Clearances","SI":"Score Involvements",
    "MG":"Metres Gained","TO":"Turnovers","ITC":"Intercepts",
    "T5":"Tackles Inside 50","CP":"Contested Possessions",
    "UP":"Uncontested Possessions","ED":"Effective Disposals",
    "DE":"Disposal Efficiency %","CM":"Contested Marks",
    "MI5":"Marks Inside 50","One.Percenters":"One Percenters",
    "BO":"Bounces","TOG":"Time on Ground %","GA":"Goal Assists",
}

# Feature importance columns in the new predictions format
IMPORTANCE_COLS = [
    "Importance_External Factors_OLS",
    "Importance_In-Game Tempo_OLS",
    "Importance_Midfield Control_OLS",
    "Importance_Offensive Output_OLS",
    "Importance_Player Ranking_OLS",
    "Importance_Ruck & Ball Movement_OLS",
    "Importance_Team Defense_OLS",
]

IMPORTANCE_LABELS = {
    "Importance_External Factors_OLS":    "External Factors",
    "Importance_In-Game Tempo_OLS":       "In-Game Tempo",
    "Importance_Midfield Control_OLS":    "Midfield Control",
    "Importance_Offensive Output_OLS":    "Offensive Output",
    "Importance_Player Ranking_OLS":      "Player Ranking",
    "Importance_Ruck & Ball Movement_OLS":"Ruck & Ball Movement",
    "Importance_Team Defense_OLS":        "Team Defense",
}


def _path(key):
    return os.path.join(DATA_DIR, FILES[key])


def data_files_present():
    missing = [
        fname for key, fname in FILES.items()
        if not os.path.exists(os.path.join(DATA_DIR, fname))
    ]
    return len(missing) == 0, missing


def _optional_file_present(key):
    return os.path.exists(_path(key))


@st.cache_data(show_spinner=False)
def load_raw(key):
    return pd.read_csv(_path(key), low_memory=False)

@st.cache_data(show_spinner=False)
def get_game_lookup():
    """
    Game lookup is the single source of truth for
    Round, Date and RoundStatus.
    """
    df = load_raw("game_lookup")

    df["Season"] = df["Season"].astype(str)

    if "RoundNumber" in df.columns:
        df["RoundNumber"] = pd.to_numeric(df["RoundNumber"], errors="coerce")

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(
            df["Date"],
            format="mixed",
            dayfirst=True,
            errors="coerce"
        )

    return df

def add_round_status(df):
    """
    Merge RoundStatus, Round and Date from
    STG_Game_Lookup.csv.

    This becomes the single source of truth for
    whether a game is:

    - Past Round
    - Current Round
    - Future Round
    """

    lookup = get_game_lookup()

    cols = [
        c for c in [
            "Match_id",
            "RoundStatus"
        ]
        if c in lookup.columns
    ]

    lookup = lookup[cols].drop_duplicates()

    df = df.drop(
        columns=[
            c for c in [
                "RoundStatus"
            ]
            if c in df.columns
        ],
        errors="ignore"
    )

    df = df.merge(
        lookup,
        on="Match_id",
        how="left"
    )

    # if "Date" in df.columns:
    #     df["Date_str"] = df["Date"].dt.strftime("%Y-%m-%d")

    return df

def _detect_predictions_format(df):
    """
    Returns 'new' if the df has the LOGIT/OLS multi-model columns,
    'old' if it has the original xgboost_margin single-model format.
    """
    if "Predicted_Prob_LOGIT" in df.columns:
        return "new"
    return "old"


# ----------------------------------------------------------------------
# TEAM PERFORMANCE
# ----------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_team_results():
    df = load_raw("game_results")

    df = add_round_status(df)

    df = df[
        df["RoundStatus"] == "Past Round"
    ].copy()

    df["Season"] = df["Season"].astype(str)
    df["RoundNumber"] = pd.to_numeric(df["RoundNumber"], errors="coerce")
    df["Margin"] = pd.to_numeric(df["Margin"], errors="coerce")
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")
    df["Opposition_Points"] = pd.to_numeric(df["Opposition_Points"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def get_team_season_summary():
    df = get_team_results()
    grp = df.groupby(["Team","Season"], as_index=False).agg(
        Played=("Match_id","count"),
        Wins=("Result", lambda s: (s=="W").sum()),
        Losses=("Result", lambda s: (s=="L").sum()),
        Draws=("Result", lambda s: (s=="D").sum()),
        Points_For=("Points","sum"),
        Points_Against=("Opposition_Points","sum"),
        Avg_Margin=("Margin","mean"),
    )
    grp["Win_Pct"] = (grp["Wins"] / grp["Played"] * 100).round(1)
    grp["Percentage"] = (
        grp["Points_For"] / grp["Points_Against"].replace(0, np.nan) * 100
    ).round(1)
    grp["Avg_Margin"] = grp["Avg_Margin"].round(1)
    return grp.sort_values(["Season","Win_Pct"], ascending=[False,False])


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
    df = get_player_rankings()

    # Add the Round Status manually
    lookup = get_game_lookup()

    lookup = lookup[lookup['RoundStatus'] != 'Future Round']
    lookup = lookup[['RoundNumber', 'Season']].drop_duplicates()

    df = df.merge(lookup, on = ['RoundNumber', 'Season'])

    latest_season = df["Season"].max()
    latest_round = df.loc[df["Season"]==latest_season, "RoundNumber"].max()
    latest = df[
        (df["Season"]==latest_season) & (df["RoundNumber"]==latest_round)
    ].copy().sort_values("Rank_Overall")
    return latest, latest_season, int(latest_round)


@st.cache_data(show_spinner=False)
def get_player_rank_history(draft_id, season):
    df = get_player_rankings()
    df = add_round_status(df)

    df = df[
        df["RoundStatus"] != "Future Round"
    ]

    h = df[(df["Draft_Player_Id"]==draft_id) & (df["Season"]==season)].copy()
    return h.sort_values("RoundNumber")


@st.cache_data(show_spinner=False)
def get_player_game_log():
    df = load_raw("game_player_combined")

    df = add_round_status(df)

    df = df[
        df["RoundStatus"] == "Past Round"
    ].copy()

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
    season_df = df[df["Season"]==season].copy()
    grp = season_df.groupby("Player", as_index=False).agg(
        Games=("Match_id","count"),
        Team=("Team","last"),
        Position=("Position_Final","last"),
        **{f"{c}_total": (c,"sum") for c in NUMERIC_STAT_COLS if c in season_df.columns},
    )
    for c in NUMERIC_STAT_COLS:
        if f"{c}_total" in grp.columns:
            grp[f"{c}_avg"] = (grp[f"{c}_total"] / grp["Games"]).round(1)
            grp[f"{c}_total"] = grp[f"{c}_total"].round(1)
    return grp


@st.cache_data(show_spinner=False)
def get_player_career_log(player_name):
    df = get_player_game_log()
    return df[df["Player"]==player_name].copy().sort_values(["Season","RoundNumber"])

@st.cache_data(show_spinner=False)
def get_completed_predictions():

    df = get_predictions()

    return df[
        df["RoundStatus"] == "Past Round"
    ].copy()


@st.cache_data(show_spinner=False)
def get_current_round_predictions():

    df = get_predictions()

    return df[
        df["RoundStatus"] == "Current Round"
    ].copy()


@st.cache_data(show_spinner=False)
def get_future_predictions():

    df = get_predictions()

    return df[
        df["RoundStatus"] == "Future Round"
    ].copy()

# ----------------------------------------------------------------------
# MODEL PREDICTIONS  (supports both old and new format)
# ----------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_predictions():
    df = load_raw("predictions")

    df = add_round_status(df)
    df["Season"] = df["Season"].astype(str)
    df["RoundNumber"] = pd.to_numeric(df["RoundNumber"], errors="coerce")

    # Filter to only include the home row
    df = df[df['IsHome'] == 1]

    fmt = _detect_predictions_format(df)

    df["Margin"] = pd.to_numeric(df["Margin"], errors="coerce")

    if fmt == "new":
        # ---- NEW FORMAT: LOGIT + OLS models ----
        df["Predicted_Prob_LOGIT"] = pd.to_numeric(df.get("Predicted_Prob_LOGIT"), errors="coerce")
        df["Predicted_Result_LOGIT"] = pd.to_numeric(df.get("Predicted_Result_LOGIT"), errors="coerce")
        df["Prediction_Outcome_LOGIT"] = pd.to_numeric(df.get("Prediction_Outcome_LOGIT"), errors="coerce")
        df["Correct_LOGIT"] = df["Prediction_Outcome_LOGIT"] == 1

        df["Predicted_Margin_OLS"] = pd.to_numeric(df.get("Predicted_Margin_OLS"), errors="coerce")
        df["Predicted_Result_OLS"] = pd.to_numeric(df.get("Predicted_Result_OLS"), errors="coerce")
        df["Prediction_Outcome_OLS"] = pd.to_numeric(df.get("Prediction_Outcome_OLS"), errors="coerce")
        df["Correct_OLS"] = df["Prediction_Outcome_OLS"] == 1

        df["Abs_Error_OLS"] = (df["Margin"] - df["Predicted_Margin_OLS"]).abs()

        for col in IMPORTANCE_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Canonical columns for backward-compat with summary/chart code
        df["Correct"] = df["Correct_OLS"]
        df["Abs_Error"] = df["Abs_Error_OLS"]
        df["Predicted_Margin_Adjusted"] = df["Predicted_Margin_OLS"]

    else:
        # ---- OLD FORMAT: single xgboost_margin model ----
        df["Predicted_Margin"] = pd.to_numeric(df["Predicted_Margin"], errors="coerce")
        df["Predicted_Margin_Adjusted"] = pd.to_numeric(
            df.get("Predicted_Margin_Adjusted", df["Predicted_Margin"]), errors="coerce"
        ).fillna(df["Predicted_Margin"])
        df["Abs_Error"] = (df["Margin"] - df["Predicted_Margin_Adjusted"]).abs()
        df["Correct"] = df["Prediction_Outcome"] == 1
        df["Correct_LOGIT"] = None
        df["Correct_OLS"] = None
        df["Predicted_Prob_LOGIT"] = None
        df["Predicted_Margin_OLS"] = None
        df["Abs_Error_OLS"] = df["Abs_Error"]

    df["_fmt"] = fmt
    return df


@st.cache_data(show_spinner=False)
def get_prediction_format():
    df = load_raw("predictions")
    return _detect_predictions_format(df)


@st.cache_data(show_spinner=False)
def get_prediction_summary():
    df = get_predictions()
    fmt = df["_fmt"].iloc[0] if len(df) else "old"

    # Scored games only (where Margin is known)
    scored = df[
        df["RoundStatus"] == "Past Round"
    ].copy()

    if fmt == "new":
        by_season_logit = scored.groupby("Season", as_index=False).agg(
            Games=("Match_id","count"),
            Correct_LOGIT=("Correct_LOGIT","sum"),
        )
        by_season_logit["Accuracy_LOGIT"] = (
            by_season_logit["Correct_LOGIT"] / by_season_logit["Games"] * 100
        ).round(1)

        by_season_ols = scored.groupby("Season", as_index=False).agg(
            Games=("Match_id","count"),
            Correct_OLS=("Correct_OLS","sum"),
            MAE_OLS=("Abs_Error_OLS","mean"),
        )
        by_season_ols["Accuracy_OLS"] = (
            by_season_ols["Correct_OLS"] / by_season_ols["Games"] * 100
        ).round(1)
        by_season_ols["MAE_OLS"] = by_season_ols["MAE_OLS"].round(2)

        # Merge
        by_season = by_season_logit.merge(by_season_ols[["Season","Accuracy_OLS","MAE_OLS"]], on="Season")
        by_season = by_season.sort_values("Season")

        n = len(scored)
        overall = {
            "games": n,
            "accuracy_logit": round(scored["Correct_LOGIT"].sum() / n * 100, 1) if n else None,
            "accuracy_ols":   round(scored["Correct_OLS"].sum()   / n * 100, 1) if n else None,
            "mae_ols":        round(scored["Abs_Error_OLS"].mean(), 2) if n else None,
            "fmt": "new",
        }
    else:
        by_season = scored.groupby("Season", as_index=False).agg(
            Games=("Match_id","count"),
            Correct=("Correct","sum"),
            MAE=("Abs_Error","mean"),
        )
        by_season["Accuracy_Pct"] = (by_season["Correct"] / by_season["Games"] * 100).round(1)
        by_season["MAE"] = by_season["MAE"].round(2)
        by_season = by_season.sort_values("Season")

        n = len(scored)
        overall = {
            "games": n,
            "correct": int(scored["Correct"].sum()),
            "accuracy_pct": round(scored["Correct"].sum() / n * 100, 1) if n else None,
            "mae": round(scored["Abs_Error"].mean(), 2) if n else None,
            "fmt": "old",
        }

    return by_season, overall


@st.cache_data(show_spinner=False)
def get_upcoming_fixture():
    df = load_raw("fixture")
    upcoming = df[
        df["RoundStatus"].isin(
            [
                "Current Round",
                "Future Round"
            ]
        )
    ].copy()
    return upcoming.sort_values("Date")


# ----------------------------------------------------------------------
# LADDER PROJECTION
# ----------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_ladder_projection():
    if not _optional_file_present("ladder_projection"):
        return None
    df = load_raw("ladder_projection")
    df["Current_Rank"] = pd.to_numeric(df["Current_Rank"], errors="coerce")
    df["Projected_Rank_Median"] = pd.to_numeric(df["Projected_Rank_Median"], errors="coerce")
    df["Rank_Movement"] = pd.to_numeric(df["Rank_Movement"], errors="coerce")
    df["Rank_Range_Best"] = pd.to_numeric(df["Rank_Range_Best"], errors="coerce")
    df["Rank_Range_Worst"] = pd.to_numeric(df["Rank_Range_Worst"], errors="coerce")
    df["Current_Points"] = pd.to_numeric(df["Current_Points"], errors="coerce")
    df["Current_Percentage"] = pd.to_numeric(df["Current_Percentage"], errors="coerce")
    df["Games_Remaining"] = pd.to_numeric(df["Games_Remaining"], errors="coerce")
    return df.sort_values("Current_Rank")


# ----------------------------------------------------------------------
# GLOBAL META
# ----------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_meta():
    teams = get_all_teams()
    latest_rankings, latest_season, latest_round = get_latest_rankings()
    _, pred_overall = get_prediction_summary()
    fmt = pred_overall.get("fmt","old")

    if fmt == "new":
        acc = pred_overall.get("accuracy_logit")  # headline: LOGIT accuracy
        mae = pred_overall.get("mae_ols")
        games = pred_overall.get("games", 0)
    else:
        acc = pred_overall.get("accuracy_pct")
        mae = pred_overall.get("mae")
        games = pred_overall.get("games", 0)

    return {
        "teams_tracked":        len(teams),
        "latest_season":        latest_season,
        "latest_round":         latest_round,
        "model_accuracy_pct":   acc,
        "model_mae":            mae,
        "model_games_scored":   games,
        "players_tracked":      len(latest_rankings),
        "predictions_fmt":      fmt,
    }
