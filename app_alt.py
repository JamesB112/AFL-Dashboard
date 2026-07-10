"""
app.py
======
Boundary Line AFL Analytics — single-file Streamlit app.

Everything (data loading, helpers, and both pages) lives in this one
script. Navigation between "pages" is done with a sidebar radio button
instead of Streamlit's native pages/ folder.

Run with:
    streamlit run app.py

Expects a `data/` folder next to this file containing:
    Predictions.csv, STG_Coaches_Votes.csv, STG_Fixture.csv,
    STG_Game_Lookup.csv, STG_Game_Player_Combined.csv,
    STG_Game_Positions.csv, STG_Game_Results.csv, STG_Game_Scoreworm.csv,
    STG_Player_Linkage.csv, STG_Player_Rankings.csv, Ladder_Projection.csv
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# =========================================================================
# ============================  DATA LOADER  =============================
# =========================================================================

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
    """Single source of truth for Round, Date and RoundStatus."""
    df = load_raw("game_lookup")
    df["Season"] = df["Season"].astype(str)

    if "RoundNumber" in df.columns:
        df["RoundNumber"] = pd.to_numeric(df["RoundNumber"], errors="coerce")

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(
            df["Date"], format="mixed", dayfirst=True, errors="coerce"
        )

    return df


def add_round_status(df):
    """
    Merge RoundStatus from STG_Game_Lookup.csv - the single source of
    truth for whether a game is Past Round / Next Round / Future Round.
    """
    lookup = get_game_lookup()
    cols = [c for c in ["Match_id", "RoundStatus"] if c in lookup.columns]
    lookup = lookup[cols].drop_duplicates()

    df = df.drop(columns=[c for c in ["RoundStatus"] if c in df.columns], errors="ignore")
    df = df.merge(lookup, on="Match_id", how="left")
    return df


def _detect_predictions_format(df):
    if "Predicted_Prob_LOGIT" in df.columns:
        return "new"
    return "old"


# ---- Team performance ----

@st.cache_data(show_spinner=False)
def get_team_results():
    df = load_raw("game_results")
    df = add_round_status(df)
    df = df[df["RoundStatus"] == "Past Round"].copy()

    df["Season"] = df["Season"].astype(str)
    df["RoundNumber"] = pd.to_numeric(df["RoundNumber"], errors="coerce")
    df["Margin"] = pd.to_numeric(df["Margin"], errors="coerce")
    df["Points"] = pd.to_numeric(df["Points"], errors="coerce")
    df["Opposition_Points"] = pd.to_numeric(df["Opposition_Points"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def get_team_season_summary():
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
    grp["Percentage"] = (
        grp["Points_For"] / grp["Points_Against"].replace(0, np.nan) * 100
    ).round(1)
    grp["Avg_Margin"] = grp["Avg_Margin"].round(1)
    return grp.sort_values(["Season", "Win_Pct"], ascending=[False, False])


@st.cache_data(show_spinner=False)
def get_all_teams():
    return sorted(get_team_results()["Team"].dropna().unique().tolist())


@st.cache_data(show_spinner=False)
def get_all_seasons():
    seasons = get_team_results()["Season"].dropna().unique().tolist()
    return sorted(seasons, reverse=True)


# ---- Player performance ----

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

    lookup = get_game_lookup()
    lookup = lookup[lookup["RoundStatus"] != "Future Round"]
    lookup = lookup[["RoundNumber", "Season"]].drop_duplicates()

    df = df.merge(lookup, on=["RoundNumber", "Season"])

    latest_season = df["Season"].max()
    latest_round = df.loc[df["Season"] == latest_season, "RoundNumber"].max()
    latest = df[
        (df["Season"] == latest_season) & (df["RoundNumber"] == latest_round)
    ].copy().sort_values("Rank_Overall")
    return latest, latest_season, int(latest_round)


@st.cache_data(show_spinner=False)
def get_player_rank_history(draft_id, season):
    df = get_player_rankings()
    df = add_round_status(df)
    df = df[df["RoundStatus"] != "Future Round"]

    h = df[(df["Draft_Player_Id"] == draft_id) & (df["Season"] == season)].copy()
    return h.sort_values("RoundNumber")


@st.cache_data(show_spinner=False)
def get_player_game_log():
    df = load_raw("game_player_combined")
    df = add_round_status(df)
    df = df[df["RoundStatus"] == "Past Round"].copy()

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
    grp = season_df.groupby("Player", as_index=False).agg(
        Games=("Match_id", "count"),
        Team=("Team", "last"),
        Position=("Position_Final", "last"),
        **{f"{c}_total": (c, "sum") for c in NUMERIC_STAT_COLS if c in season_df.columns},
    )
    for c in NUMERIC_STAT_COLS:
        if f"{c}_total" in grp.columns:
            grp[f"{c}_avg"] = (grp[f"{c}_total"] / grp["Games"]).round(1)
            grp[f"{c}_total"] = grp[f"{c}_total"].round(1)
    return grp


@st.cache_data(show_spinner=False)
def get_player_career_log(player_name):
    df = get_player_game_log()
    return df[df["Player"] == player_name].copy().sort_values(["Season", "RoundNumber"])


@st.cache_data(show_spinner=False)
def get_completed_predictions():
    df = get_predictions()
    return df[df["RoundStatus"] == "Past Round"].copy()


@st.cache_data(show_spinner=False)
def get_current_round_predictions():
    df = get_predictions()
    return df[df["RoundStatus"] == "Next Round"].copy()


@st.cache_data(show_spinner=False)
def get_future_predictions():
    df = get_predictions()
    return df[df["RoundStatus"] == "Future Round"].copy()


# ---- Model predictions (supports both old and new format) ----

@st.cache_data(show_spinner=False)
def get_predictions():
    df = load_raw("predictions")

    # df = add_round_status(df)
    df["Season"] = df["Season"].astype(str)
    df["RoundNumber"] = pd.to_numeric(df["RoundNumber"], errors="coerce")

    df = df[df["IsHome"] == 1]

    fmt = _detect_predictions_format(df)
    df["Margin"] = pd.to_numeric(df["Margin"], errors="coerce")

    if fmt == "new":
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

        df["Correct"] = df["Correct_OLS"]
        df["Abs_Error"] = df["Abs_Error_OLS"]
        df["Predicted_Margin_Adjusted"] = df["Predicted_Margin_OLS"]
    else:
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

    scored = df[df["RoundStatus"] == "Past Round"].copy()

    if fmt == "new":
        by_season_logit = scored.groupby("Season", as_index=False).agg(
            Games=("Match_id", "count"),
            Correct_LOGIT=("Correct_LOGIT", "sum"),
        )
        by_season_logit["Accuracy_LOGIT"] = (
            by_season_logit["Correct_LOGIT"] / by_season_logit["Games"] * 100
        ).round(1)

        by_season_ols = scored.groupby("Season", as_index=False).agg(
            Games=("Match_id", "count"),
            Correct_OLS=("Correct_OLS", "sum"),
            MAE_OLS=("Abs_Error_OLS", "mean"),
        )
        by_season_ols["Accuracy_OLS"] = (
            by_season_ols["Correct_OLS"] / by_season_ols["Games"] * 100
        ).round(1)
        by_season_ols["MAE_OLS"] = by_season_ols["MAE_OLS"].round(2)

        by_season = by_season_logit.merge(by_season_ols[["Season", "Accuracy_OLS", "MAE_OLS"]], on="Season")
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
            Games=("Match_id", "count"),
            Correct=("Correct", "sum"),
            MAE=("Abs_Error", "mean"),
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
    upcoming = df[df["RoundStatus"].isin(["Next Round", "Future Round"])].copy()
    return upcoming.sort_values("Date")


# ---- Ladder projection ----

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


# ---- Global meta ----

@st.cache_data(show_spinner=False)
def get_meta():
    teams = get_all_teams()
    latest_rankings, latest_season, latest_round = get_latest_rankings()
    _, pred_overall = get_prediction_summary()
    fmt = pred_overall.get("fmt", "old")

    if fmt == "new":
        acc = pred_overall.get("accuracy_logit")
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


# =========================================================================
# ===============================  UTILS  ================================
# =========================================================================

def first_col(df: pd.DataFrame, candidates: list, default=None):
    """Return the first column name in `candidates` that exists in df."""
    for c in candidates:
        if c in df.columns:
            return c
    return default


def safe_get(row, col, default="—"):
    if col is None or col not in row.index:
        return default
    val = row[col]
    if pd.isna(val):
        return default
    return val


def fmt_pct(x, decimals=1):
    if x is None or pd.isna(x):
        return "—"
    return f"{x:.{decimals}f}%"


def fmt_num(x, decimals=1):
    if x is None or pd.isna(x):
        return "—"
    return f"{x:.{decimals}f}"


TEAM_COL_CANDIDATES = ["Team", "Home_Team", "HomeTeam"]
OPP_COL_CANDIDATES = ["Opposition_Team", "Opposition", "Away_Team", "AwayTeam", "Opponent"]
DATE_COL_CANDIDATES = ["Date", "Match_Date", "Game_Date"]
VENUE_COL_CANDIDATES = ["Venue", "Ground"]


# =========================================================================
# ============================  HOME PAGE  ===============================
# =========================================================================

def render_home():
    st.title("🏉 Boundary Line AFL Analytics")
    st.caption("Model predictions, ladder projections, and player performance tracking.")

    ok, missing = data_files_present()
    if not ok:
        st.error(
            "Some data files are missing from `data/`. Pages won't load "
            "correctly until these are added:\n\n" + "\n".join(f"- `{m}`" for m in missing)
        )
        return

    meta = get_meta()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Latest Season", meta["latest_season"])
    col2.metric("Latest Round", meta["latest_round"])
    col3.metric(
        "Model Accuracy (season)",
        f"{meta['model_accuracy_pct']:.1f}%" if meta["model_accuracy_pct"] is not None else "—",
    )
    col4.metric("Players Tracked", meta["players_tracked"])

    st.divider()

    left, right = st.columns(2)
    with left:
        st.subheader("📊 Predictions")
        st.write(
            "Next Round predictions with drill-down detail per game, "
            "the projected ladder, and season-long model performance."
        )
    with right:
        st.subheader("🧍 Player Rankings")
        st.write(
            "Browse the latest player rankings, then click into any player "
            "to see their ranking trend and stat performance across the season."
        )

    st.divider()
    st.caption("Use the sidebar to switch pages.")


# =========================================================================
# ==========================  PREDICTIONS PAGE  ==========================
# =========================================================================

def render_predictions_page():
    st.title("🏉 Predictions")

    meta = get_meta()
    st.caption(f"Season {meta['latest_season']} · Round {meta['latest_round']}")

    current_df = get_current_round_predictions()

    if current_df.empty:
        st.info("No games marked as 'Next Round' in the data right now.")
    else:
        team_col = first_col(current_df, TEAM_COL_CANDIDATES)
        opp_col = first_col(current_df, OPP_COL_CANDIDATES)
        date_col = first_col(current_df, DATE_COL_CANDIDATES)
        venue_col = first_col(current_df, VENUE_COL_CANDIDATES)
        fmt = current_df["_fmt"].iloc[0] if len(current_df) else "old"

        if date_col:
            current_df = current_df.copy()
            current_df["_date_parsed"] = pd.to_datetime(
                current_df[date_col], format="mixed", dayfirst=True, errors="coerce"
            )
            current_df = current_df.sort_values("_date_parsed")

        if "selected_match" not in st.session_state:
            st.session_state.selected_match = current_df.iloc[0]["Match_id"]

        st.subheader("This round's games")

        for _, row in current_df.iterrows():
            match_id = row["Match_id"]
            team = safe_get(row, team_col, "Home")
            opp = safe_get(row, opp_col, "Away")
            venue = safe_get(row, venue_col, "")
            date_disp = ""
            if date_col and pd.notna(row.get("_date_parsed")):
                date_disp = row["_date_parsed"].strftime("%a %d %b")

            if fmt == "new":
                prob = row.get("Predicted_Prob_LOGIT")
                pred_margin = row.get("Predicted_Margin_OLS")
                prob_txt = fmt_pct(prob * 100) if pd.notna(prob) else "—"
                favourite = team if (pd.notna(prob) and prob >= 0.5) else opp
            else:
                pred_margin = row.get("Predicted_Margin_Adjusted")
                prob_txt = None
                favourite = team if (pd.notna(pred_margin) and pred_margin >= 0) else opp

            margin_txt = fmt_num(abs(pred_margin)) if pd.notna(pred_margin) else "—"

            cols = st.columns([3, 2, 2, 2])
            cols[0].markdown(f"**{team}** vs **{opp}**")
            cols[1].markdown(f"{date_disp}  📍 {venue}" if venue != "—" else date_disp)
            if prob_txt:
                cols[2].markdown(f"Win prob: **{prob_txt}**")
            cols[2].markdown(f"Predicted margin: **{margin_txt}** ({favourite})")
            if cols[3].button("View details", key=f"btn_{match_id}"):
                st.session_state.selected_match = match_id

        st.divider()

        sel = current_df[current_df["Match_id"] == st.session_state.selected_match]
        if not sel.empty:
            row = sel.iloc[0]
            team = safe_get(row, team_col, "Home")
            opp = safe_get(row, opp_col, "Away")

            st.subheader(f"🔍 {team} vs {opp}")

            odds_team = row.get("Team_Odds")
            odds_opp = row.get("Opposition_Team_Odds")
            if pd.notna(odds_team) and pd.notna(odds_opp):
                st.caption(
                    f"Market odds — {team}: **{fmt_num(odds_team, 2)}**  ·  "
                    f"{opp}: **{fmt_num(odds_opp, 2)}**"
                )

            detail_cols = st.columns(3)
            if fmt == "new":
                prob = row.get("Predicted_Prob_LOGIT")
                detail_cols[0].metric(
                    "LOGIT win probability",
                    fmt_pct(prob * 100) if pd.notna(prob) else "—",
                    help="Probability the home team wins, per the LOGIT model.",
                )
                pred_margin_ols = row.get("Predicted_Margin_OLS")
                detail_cols[1].metric(
                    "OLS predicted margin",
                    fmt_num(pred_margin_ols) if pd.notna(pred_margin_ols) else "—",
                    help="Positive = home team predicted to win by this many points.",
                )
                actual_margin = row.get("Margin")
                detail_cols[2].metric(
                    "Actual margin",
                    fmt_num(actual_margin) if pd.notna(actual_margin) else "TBD",
                )

                avail_importance = [c for c in IMPORTANCE_COLS if c in row.index and pd.notna(row[c])]
                if avail_importance:
                    st.markdown("**What's driving the OLS prediction**")
                    imp_df = pd.DataFrame({
                        "Factor": [IMPORTANCE_LABELS.get(c, c) for c in avail_importance],
                        "Importance": [row[c] for c in avail_importance],
                    }).sort_values("Importance", ascending=True)
                    fig = px.bar(imp_df, x="Importance", y="Factor", orientation="h", height=320)
                    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                pred_margin = row.get("Predicted_Margin_Adjusted")
                detail_cols[0].metric(
                    "Predicted margin", fmt_num(pred_margin) if pd.notna(pred_margin) else "—"
                )
                actual_margin = row.get("Margin")
                detail_cols[1].metric(
                    "Actual margin", fmt_num(actual_margin) if pd.notna(actual_margin) else "TBD"
                )
                abs_err = row.get("Abs_Error")
                detail_cols[2].metric("Abs. error", fmt_num(abs_err) if pd.notna(abs_err) else "—")

    st.divider()

    st.subheader("📈 Projected Ladder")

    ladder = get_ladder_projection()
    if ladder is None or ladder.empty:
        st.info("No ladder projection data available.")
    else:
        display_cols = [c for c in [
            "Current_Rank", "Team", "Current_Points", "Current_Percentage",
            "Projected_Rank_Median", "Rank_Range_Best", "Rank_Range_Worst",
            "Rank_Movement", "Games_Remaining",
        ] if c in ladder.columns]
        st.dataframe(
            ladder[display_cols].rename(columns={
                "Current_Rank": "Rank",
                "Current_Points": "Points",
                "Current_Percentage": "%",
                "Projected_Rank_Median": "Proj. Rank (median)",
                "Rank_Range_Best": "Best case",
                "Rank_Range_Worst": "Worst case",
                "Rank_Movement": "Movement",
                "Games_Remaining": "Games left",
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("🎯 Season Prediction Performance")

    by_season, overall = get_prediction_summary()

    if overall["games"] == 0:
        st.info("No completed games with known results yet this season.")
    else:
        if overall.get("fmt") == "new":
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Games scored", overall["games"])
            m2.metric("LOGIT accuracy", fmt_pct(overall["accuracy_logit"]))
            m3.metric("OLS accuracy", fmt_pct(overall["accuracy_ols"]))
            m4.metric("OLS mean abs. error", fmt_num(overall["mae_ols"]))

            fig = go.Figure()
            fig.add_bar(name="LOGIT accuracy", x=by_season["Season"], y=by_season["Accuracy_LOGIT"])
            fig.add_bar(name="OLS accuracy", x=by_season["Season"], y=by_season["Accuracy_OLS"])
            fig.update_layout(
                barmode="group", yaxis_title="Accuracy (%)", height=380,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("Games scored", overall["games"])
            m2.metric("Accuracy", fmt_pct(overall["accuracy_pct"]))
            m3.metric("Mean abs. error", fmt_num(overall["mae"]))

            fig = px.bar(by_season, x="Season", y="Accuracy_Pct", height=380)
            fig.update_layout(yaxis_title="Accuracy (%)", margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("Season-by-season detail"):
            st.dataframe(by_season, use_container_width=True, hide_index=True)


# =========================================================================
# =======================  PLAYER RANKINGS PAGE  =========================
# =========================================================================

def render_player_rankings_page():
    st.title("🧍 Player Rankings")

    latest, latest_season, latest_round = get_latest_rankings()
    st.caption(f"Season {latest_season} · Round {latest_round}")

    if latest.empty:
        st.info("No ranking data available.")
        return

    player_col = first_col(latest, ["Player", "Player_Name", "PlayerName"], default="Player")
    id_col = first_col(latest, ["Draft_Player_Id"], default="Draft_Player_Id")
    team_col = first_col(latest, ["Team"])
    position_col = first_col(latest, ["Position", "Position_Final"])

    search = st.text_input("Search player", placeholder="Start typing a player name…")

    filtered = latest
    if search:
        filtered = latest[latest[player_col].str.contains(search, case=False, na=False)]

    if team_col:
        teams = sorted(latest[team_col].dropna().unique().tolist())
        picked_teams = st.multiselect("Filter by team", teams)
        if picked_teams:
            filtered = filtered[filtered[team_col].isin(picked_teams)]

    st.subheader(f"Top players — Round {latest_round}")

    display_cols = [c for c in [
        "Rank_Overall", player_col, team_col, position_col, "composite_score",
    ] if c and c in filtered.columns]

    table = filtered[display_cols].rename(columns={
        "Rank_Overall": "Rank",
        player_col: "Player",
        team_col: "Team",
        position_col: "Position",
        "composite_score": "Composite Score",
    })

    st.dataframe(table, use_container_width=True, hide_index=True, height=380)

    st.divider()

    st.subheader("🔍 Player detail")

    player_names = filtered[player_col].dropna().unique().tolist()
    if not player_names:
        st.info("No players match your filters.")
        return

    selected_player = st.selectbox("Choose a player", sorted(player_names), index=0)

    player_row = filtered[filtered[player_col] == selected_player].iloc[0]
    draft_id = player_row.get(id_col)

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Current rank",
        int(player_row["Rank_Overall"]) if pd.notna(player_row.get("Rank_Overall")) else "—",
    )
    col2.metric("Composite score", fmt_num(player_row.get("composite_score")))
    if team_col:
        col3.metric("Team", player_row.get(team_col, "—"))

    st.markdown("**Ranking trend this season**")
    history = get_player_rank_history(draft_id, latest_season)

    if history.empty:
        st.info("No ranking history found for this player.")
    else:
        history = history.sort_values("RoundNumber")
        fig = px.line(history, x="RoundNumber", y="Rank_Overall", markers=True, height=350)
        fig.update_yaxes(autorange="reversed", title="Overall Rank")
        fig.update_xaxes(title="Round")
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

        if "composite_score" in history.columns:
            fig2 = px.line(history, x="RoundNumber", y="composite_score", markers=True, height=300)
            fig2.update_xaxes(title="Round")
            fig2.update_yaxes(title="Composite Score")
            fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            with st.expander("Composite score trend"):
                st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    st.markdown("**Performance across the season**")

    career = get_player_career_log(selected_player)
    season_log = career[career["Season"] == latest_season].copy() if not career.empty else career

    if season_log.empty:
        st.info("No game-by-game stats found for this player this season.")
    else:
        available_stats = [c for c in NUMERIC_STAT_COLS if c in season_log.columns]
        stat_options = {STAT_LABELS.get(c, c): c for c in available_stats}

        default_stats = [s for s in ["Disposals", "Goals", "Tackles"] if s in stat_options]
        picked_labels = st.multiselect(
            "Stats to chart",
            options=list(stat_options.keys()),
            default=default_stats or list(stat_options.keys())[:3],
        )

        if picked_labels:
            picked_cols = [stat_options[l] for l in picked_labels]
            chart_df = season_log[["RoundNumber"] + picked_cols].melt(
                id_vars="RoundNumber", var_name="Stat", value_name="Value"
            )
            chart_df["Stat"] = chart_df["Stat"].map(lambda c: STAT_LABELS.get(c, c))

            fig3 = px.line(
                chart_df.sort_values("RoundNumber"),
                x="RoundNumber", y="Value", color="Stat", markers=True, height=400,
            )
            fig3.update_xaxes(title="Round")
            fig3.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig3, use_container_width=True)

        with st.expander("Full game log"):
            log_cols = [c for c in ["RoundNumber", "Team", "Position_Final"] + available_stats if c in season_log.columns]
            st.dataframe(
                season_log[log_cols].sort_values("RoundNumber"),
                use_container_width=True,
                hide_index=True,
            )


# =========================================================================
# ================================  MAIN  ================================
# =========================================================================

def main():
    st.set_page_config(page_title="Boundary Line AFL Analytics", page_icon="🏉", layout="wide")

    st.sidebar.title("🏉 Boundary Line")
    page = st.sidebar.radio(
        "Navigate",
        ["Home", "Predictions", "Player Rankings"],
        label_visibility="collapsed",
    )

    if page == "Home":
        render_home()
    elif page == "Predictions":
        render_predictions_page()
    elif page == "Player Rankings":
        render_player_rankings_page()


if __name__ == "__main__":
    main()
