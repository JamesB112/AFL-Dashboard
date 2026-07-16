"""
Tippo — AFL Analytics
A personal portfolio app covering team performance, player rankings,
ladder projections, and a margin/win-probability prediction model.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import base64
from pathlib import Path

import data_loader as dl

st.set_page_config(
    page_title="Tippo — AFL Analytics",
    layout="wide",
    page_icon="assets/favicon.png",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# THEME TOKENS
# ----------------------------------------------------------------------
# Single source of truth for color/type. Everything below — the CSS block,
# Plotly charts, and inline markdown — reads from these constants rather
# than hardcoding hex values in more than one place. To retheme the whole
# app, change values here (and the matching .streamlit/config.toml).

THEME = {
    # core surfaces
    "bg":            "#FFFFFF",   # page background
    "surface":       "#F5F8F6",   # card/table background
    "sidebar_bg":    "#1C2B27",   # deep forest rail — lighter than near-black, still reads as "dark"
    "sidebar_text":  "#EAF3EE",
    "sidebar_muted": "#8FA79D",
    "border":        "#E2E6E4",
    "header_bg":     "#1C2B27",   # matches sidebar for a cohesive scoreboard strip
    "header_text":   "#9CFFB0",   # slightly softer mint-neon than before

    "input_bg":      "#EEF2F0",

    # text
    "ink":           "#1E2B27",   # dark green-charcoal, lighter than pure black
    "body_text":     "#3F4F49",
    "muted":         "#6E8079",

    # accents
    "primary":       "#2FA968",   # lighter, more vibrant green than the old #128A4E
    "neon":          "#9CFFB0",   # softer mint-lime, less harsh than pure lime
    "accent_blue":   "#2F6FED",
    "accent_gold":   "#FFB020",
    "negative":      "#E14C63",   # slightly lighter crimson to match the softer palette

    # type — unchanged
    "font_display":  "Space Grotesk",
    "font_mono":     "JetBrains Mono",
    "font_body":     "Inter",
    "google_fonts_url": (
        "https://fonts.googleapis.com/css2?"
        "family=Space+Grotesk:wght@500;600;700"
        "&family=JetBrains+Mono:wght@400;500;600"
        "&family=Inter:wght@400;500;600"
        "&display=swap"
    ),
}

# Back-compat short names — used throughout the rest of the file (Plotly
# figures, inline st.markdown snippets, movement icons, etc). Keeping these
# aliases means the rest of the app didn't need a mechanical find/replace,
# while still only defining each color once, in THEME above.
GREEN    = THEME["primary"]
CLAY     = THEME["negative"]
GOLD     = THEME["accent_gold"]
SLATE    = THEME["muted"]
BLUE     = THEME["accent_blue"]
INK      = THEME["ink"]
PAPER    = THEME["surface"]
HAIRLINE = THEME["border"]
NEON     = THEME["neon"]

# ----------------------------------------------------------------------
# GLOBAL STYLE
# ----------------------------------------------------------------------

st.markdown(f"""
<style>
@import url('{THEME["google_fonts_url"]}');

/* Page background */
[data-testid="stAppViewContainer"] {{
    background: {THEME["bg"]};
}}
[data-testid="stHeader"] {{
    background: rgba(11, 15, 14, 0);
}}

/* ---- Sidebar: dark rail — the sports-tech signature against the light canvas ---- */
section[data-testid="stSidebar"] {{
    background: {THEME["sidebar_bg"]};
    border-right: 1px solid {THEME["sidebar_bg"]};
}}
section[data-testid="stSidebar"] * {{ color: {THEME["sidebar_text"]}; }}
section[data-testid="stSidebar"] .bl-eyebrow,
section[data-testid="stSidebar"] h3 {{ color: {THEME["neon"]} !important; }}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color: {THEME["sidebar_muted"]} !important; }}
section[data-testid="stSidebar"] hr {{ border-color: rgba(241,245,243,0.14) !important; }}

h1, h2, h3 {{
    font-family: '{THEME["font_display"]}', 'Inter', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    color: {THEME["ink"]};
}}

body, p, div, span, label {{
    font-family: '{THEME["font_body"]}', sans-serif;
}}

[data-testid="stMetricValue"] {{
    font-family: '{THEME["font_mono"]}', monospace;
    color: {THEME["ink"]};
}}

.bl-eyebrow {{
    font-family: '{THEME["font_mono"]}', monospace;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {THEME["primary"]};
    margin-bottom: 0.3rem;
}}

.bl-lede {{ font-size: 1.05rem; color: {THEME["body_text"]}; max-width: 70ch; }}

.bl-card {{
    background: {THEME["surface"]};
    border: 1px solid {THEME["border"]};
    border-top: 3px solid {THEME["accent_blue"]};
    border-radius: 6px;
    padding: 1.1rem 1.3rem;
    height: 100%;
}}
.bl-card h4 {{ margin: 0 0 0.4rem 0; font-family: '{THEME["font_display"]}', sans-serif; font-size: 1.15rem; color: {THEME["ink"]}; }}
.bl-card p  {{ margin: 0; color: {THEME["body_text"]}; font-size: 0.92rem; }}

.movement-up   {{ color: {THEME["primary"]};  font-weight: 700; }}
.movement-down {{ color: {THEME["negative"]}; font-weight: 700; }}
.movement-flat {{ color: {THEME["muted"]}; }}

hr, [data-testid="stDivider"] {{ border-color: {THEME["border"]} !important; }}

/* ---- Metrics as scoreboard chips: dark tile, neon mono readout ---- */
[data-testid="stMetric"] {{
    background: {THEME["ink"]};
    border: 1px solid {THEME["ink"]};
    border-radius: 8px;
    padding: 0.9rem 1.1rem 0.75rem 1.1rem;
    box-shadow: inset 0 0 0 1px rgba(140,255,79,0.12);
}}
[data-testid="stMetricLabel"] {{
    font-family: '{THEME["font_mono"]}', monospace;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {THEME["sidebar_muted"]} !important;
}}
[data-testid="stMetricValue"] {{
    font-size: 1.6rem;
    color: {THEME["neon"]} !important;
    text-shadow: 0 0 14px rgba(140,255,79,0.35);
}}
[data-testid="stMetricDelta"] {{ color: {THEME["sidebar_text"]} !important; }}

/* ---- Inputs & selects: give them a real fill so they don't disappear into a white page ---- */
div[data-baseweb="select"] > div,
.stTextInput input,
.stNumberInput input,
.stMultiSelect div[data-baseweb="select"] > div {{
    background-color: {THEME["input_bg"]} !important;
    border-color: {THEME["border"]} !important;
    border-radius: 5px !important;
}}
div[data-baseweb="select"]:focus-within > div,
.stTextInput input:focus {{
    border-color: {THEME["primary"]} !important;
    box-shadow: 0 0 0 1px {THEME["primary"]}, 0 0 8px rgba(140,255,79,0.35) !important;
}}
.stTextInput input:focus, .stNumberInput input:focus {{ outline-color: {THEME["primary"]} !important; }}

/* Multiselect tags in the house accent rather than default Streamlit red */
span[data-baseweb="tag"] {{
    background-color: {THEME["primary"]} !important;
}}

/* ---- Sidebar nav: neon-lit active feel on the dark rail ---- */
section[data-testid="stSidebar"] div[role="radiogroup"] label {{
    padding: 0.35rem 0.5rem;
    border-radius: 4px;
    transition: background 0.15s ease, box-shadow 0.15s ease;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
    background: rgba(140,255,79,0.10);
}}
section[data-testid="stSidebar"] div[role="radiogroup"] input:checked + div {{
    box-shadow: 0 0 0 1px {THEME["neon"]} inset;
}}
section[data-testid="stSidebar"] div[data-baseweb="radio"] > div:first-child {{
    border-color: {THEME["sidebar_muted"]} !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="radio"] input:checked ~ div:first-child {{
    border-color: {THEME["neon"]} !important;
    background: {THEME["neon"]} !important;
}}

/* ---- Tables: dark scoreboard strip for headers ---- */
[data-testid="stDataFrame"] thead tr th,
[data-testid="stTable"] thead tr th {{
    background: {THEME["header_bg"]} !important;
    color: {THEME["header_text"]} !important;
    font-family: '{THEME["font_mono"]}', monospace !important;
    font-size: 0.74rem !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}

/* Radio pills used inline (e.g. per-game mode toggle) */
div[role="radiogroup"] label[data-baseweb="radio"] {{ margin-right: 0.4rem; }}
</style>
""", unsafe_allow_html=True)

# Curated club colors for the Elo chart — real club identity reads far
# better across 18 lines than an arbitrary qualitative palette. Keys are
# matched case-sensitively against the "Team" column; add/adjust aliases
# here if your data uses different club name strings. Unmatched teams
# fall back to SLATE automatically (see get_team_elo_history usage below).
TEAM_COLORS = {
    "Adelaide": "#0F1E44", "Adelaide Crows": "#0F1E44",
    "Brisbane Lions": "#7A1A3B", "Brisbane": "#7A1A3B",
    "Carlton": "#031440", "Carlton Blues": "#031440",
    "Collingwood": "#2B2B2B", "Collingwood Magpies": "#2B2B2B",
    "Essendon": "#CC2031", "Essendon Bombers": "#CC2031",
    "Fremantle": "#4A0E63", "Fremantle Dockers": "#4A0E63",
    "Geelong": "#153157", "Geelong Cats": "#153157",
    "Gold Coast": "#E8380D", "Gold Coast Suns": "#E8380D",
    "GWS Giants": "#F58220", "Greater Western Sydney": "#F58220", "GWS": "#F58220",
    "Hawthorn": "#6B3410", "Hawthorn Hawks": "#6B3410",
    "Melbourne": "#00285E", "Melbourne Demons": "#00285E",
    "North Melbourne": "#0F49A6", "North Melbourne Kangaroos": "#0F49A6", "Kangaroos": "#0F49A6",
    "Port Adelaide": "#00879B", "Port Adelaide Power": "#00879B",
    "Richmond": "#C9A227", "Richmond Tigers": "#C9A227",
    "St Kilda": "#ED0F05", "St Kilda Saints": "#ED0F05",
    "Sydney": "#A31F2C", "Sydney Swans": "#A31F2C",
    "West Coast": "#003087", "West Coast Eagles": "#003087",
    "Western Bulldogs": "#014896", "Bulldogs": "#014896",
}

PLOTLY_BASE = dict(
    font=dict(family=f'{THEME["font_body"]}, sans-serif', color=INK),
    plot_bgcolor=PAPER,
    paper_bgcolor=PAPER,
    margin=dict(l=40, r=20, t=30, b=40),
    xaxis=dict(gridcolor=HAIRLINE, zeroline=False),
    yaxis=dict(gridcolor=HAIRLINE, zeroline=False),
)

def signed(n, decimals=0):
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "—"
    sign = "+" if n > 0 else ""
    return f"{sign}{n:.{decimals}f}"


def movement_icon(n):
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return ""
    if n > 0:
        return f'<span class="movement-up">▲ {abs(int(n))}</span>'
    elif n < 0:
        return f'<span class="movement-down">▼ {abs(int(n))}</span>'
    return '<span class="movement-flat">—</span>'

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

@st.cache_data
def _img_data_uri(path: str) -> str:
    """Base64-encode a local image so it can be embedded in st.markdown HTML.
    st.markdown can only render images from a URL — not a filesystem path —
    so any local logo/icon needs to go through this to appear inline."""
    data = Path(path).read_bytes()
    return f"data:image/png;base64,{base64.b64encode(data).decode()}"

# ----------------------------------------------------------------------
# DATA CHECK
# ----------------------------------------------------------------------

all_present, missing = dl.data_files_present()
if not all_present:
    st.error(
        "Some expected data files are missing from the `data/` folder:\n\n"
        + "\n".join(f"- `{m}`" for m in missing)
        + "\n\nDrop the matching CSV exports into `data/` and reload."
    )
    st.stop()

# ----------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:0.55rem;margin-bottom:0.1rem;">
            <img src="{_img_data_uri('assets/favicon.png')}" width="30" style="border-radius:7px;">
            <span style="font-family:'{THEME['font_display']}',sans-serif;
                         font-weight:600;font-size:1.6rem;color:{THEME['sidebar_text']};">
                Tippo
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("AFL Games Tipper")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["Home", "Team Performance", "Player Performance","Model Performance", "Methodology", "Q&A"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    meta = dl.get_meta()
    st.caption(f"Data through **{meta['latest_season']}, Round {meta['latest_round']}**")


# ========================================================================
# HOME
# ========================================================================

if page == "Home":

    # ---------------------------------------------------
    # HERO
    # ---------------------------------------------------

    col1, col2 = st.columns([1.6, 1])

    with col1:
        st.markdown(
            '<div class="bl-eyebrow">A personal AFL analytics project</div>',
            unsafe_allow_html=True,
        )

        st.title("Tipping made easy")

        st.markdown(
            """
            <p class="bl-lede">
            Predicting every game, projecting the final ladder,
            and providing easy acess team and player performace.

            Data is refreshed every Thursday and Friday, once lineups are released.
            </p>
            """,
            unsafe_allow_html=True,
        )

    with col2:
            acc = round((meta['current_season_correct'] / meta['current_season_games']) * 100.0,2) 
            acc_label = f"{acc}%" if acc else "—"

            c_correct = meta["current_season_correct"]
            c_model_type = meta["current_season_correct_label"]
            c_games = meta["current_season_games"]
            fraction_label = f"{c_correct}/{c_games} {c_model_type}" if c_games else "—"

            st.metric(
                "Model Accuracy",
                acc_label,
                delta=fraction_label,
                delta_color="off",
                help=f"{meta['model_games_scored']:,} games graded all-time · {fraction_label} correct this season",
            )

            st.metric(
                "Current Round",
                f"{meta['latest_season']} · Round {meta['latest_round']}",
            )

    # st.divider()
    
    # ===================================================
    # CURRENT ROUND
    # ===================================================

    st.subheader("Upcoming Predictions")

    current_df = dl.get_current_round_predictions()

    if current_df.empty:
        st.info("No games marked as 'Next Round' in the data right now.")

    else:
        team_col = first_col(current_df, TEAM_COL_CANDIDATES)
        opp_col = first_col(current_df, OPP_COL_CANDIDATES)
        date_col = first_col(current_df, DATE_COL_CANDIDATES)
        venue_col = first_col(current_df, VENUE_COL_CANDIDATES)
        fmt = current_df["_fmt"].iloc[0]

        # -----------------
        # Filters
        # -----------------

        fc1, fc2 = st.columns(2)

        with fc1:
            teams = sorted(
                set(current_df[team_col].dropna())
                | set(current_df[opp_col].dropna())
            )

            t_filter = st.selectbox(
                "Team",
                ["All teams"] + teams,
                key="current_round_team",
            )

        with fc2:


            all_rounds = ["All rounds"] + sorted(
                current_df["RoundNumber"].dropna().unique().tolist()
            )

            default_round = meta['latest_round']

            default_index = (
                all_rounds.index(default_round)
                if default_round in all_rounds
                else 0
            )

            if "RoundNumber" in current_df.columns:
                r_filter = st.selectbox(
                    "Round",
                    all_rounds,
                    index=default_index,
                    key="current_round_round",
                )
            else:
                r_filter = "All rounds"

        # -----------------
        # Apply filters
        # -----------------

        current_disp = current_df.copy()

        if t_filter != "All teams":
            current_disp = current_disp[
                (current_disp[team_col] == t_filter)
                | (current_disp[opp_col] == t_filter)
            ]

        if r_filter != "All rounds":
            current_disp = current_disp[
                current_disp["RoundNumber"] == r_filter
            ]

        # Parse and sort by date
        if date_col:
            current_disp["_date_parsed"] = pd.to_datetime(
                current_disp[date_col],
                format="%Y-%m-%d",
                dayfirst=True,
                errors="coerce",
            )
            current_disp = current_disp.sort_values("_date_parsed")

        display_df = pd.DataFrame()

        # Match
        display_df["Match"] = (
            current_disp[team_col].astype(str)
            + " vs "
            + current_disp[opp_col].astype(str)
        )

        # Date
        if date_col:
            display_df["Date"] = current_disp["_date_parsed"].dt.strftime("%a %d %b")

        # Venue
        if venue_col:
            display_df["Venue"] = current_disp[venue_col]

        display_df["Prediction"] = np.where(
            current_disp["Predicted_Margin_OLS"] >= 0.5,
            current_disp[team_col],
            current_disp[opp_col],
        )

        display_df["Win Probability"] = np.where(
            current_disp["Predicted_Prob_LOGIT"] >= 0.5,
            current_disp["Predicted_Prob_LOGIT"],
            1 - current_disp["Predicted_Prob_LOGIT"],
        ) * 100

        display_df["Predicted Margin"] = np.where(
            current_disp["Predicted_Margin_OLS"] >= 0,
            current_disp["Predicted_Margin_OLS"],
            -current_disp["Predicted_Margin_OLS"],
        )

        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Date": st.column_config.TextColumn(
                    "Date",
                    width="small",
                ),
                "Match": st.column_config.TextColumn(
                    "Match",
                    width="medium",
                ),
                "Venue": st.column_config.TextColumn(
                    "Venue",
                    width="medium",
                ),
                "Prediction": st.column_config.TextColumn(
                    "Prediction",
                    width="medium",
                ),
                "Win Probability": (
                    st.column_config.ProgressColumn(
                        "Win Probability",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    )
                ),
                "Predicted Margin": st.column_config.NumberColumn(
                    "Predicted Margin",
                    format="%.1f pts",
                ),
            },
        use_container_width=True
        )

    st.divider()

    # ===================================================
    # PROJECTED LADDER
    # ===================================================

    left, right = st.columns([1.8, 1])

    with left:

        st.subheader("Projected Final Ladder")
        st.caption("Modelled finishing position for every club.")


    ladder = dl.get_ladder_projection()
    if ladder is None:
        st.info("Ladder projection data not found — add `Ladder_Projection.csv` to the `data/` folder.")
        st.stop()

    def fmt_movement(row):
        m = row["Rank_Movement"]
        if pd.isna(m) or m == 0:
            return "—"
        return f"▲{abs(int(m))}" if m > 0 else f"▼{abs(int(m))}"

    def fmt_range(row):
        return f"{int(row['Rank_Range_Best'])}–{int(row['Rank_Range_Worst'])}"

    display = ladder.copy()
    display["Movement"] = display.apply(fmt_movement, axis=1)
    display["Proj. Range"] = display.apply(fmt_range, axis=1)
    display["In Finals?"] = display["Projected_Rank"].apply(
        lambda r: "✅ Yes" if r <= 10 else "⬜ No"
    )

    show_cols = {
        "Team": "Club",
        "Current_Rank": "Rank",
        "Wins": "W",
        "Draws": "D",
        "Losses": "L",
        "Current_Points": "Pts",
        "Current_Percentage": "%",
        "Games_Remaining": "Left",
        "Projected_Rank": "Proj.",
        "Proj. Range": "Range",
        "In Finals?": "Finals?",
    }

    st.dataframe(
        display[list(show_cols.keys())].rename(columns=show_cols),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank":   st.column_config.NumberColumn(format="%d", width="small"),
            "W":      st.column_config.NumberColumn(width="small"),
            "D":      st.column_config.NumberColumn(width="small"),
            "L":      st.column_config.NumberColumn(width="small"),
            "Pts":    st.column_config.NumberColumn(width="small"),
            "%":      st.column_config.NumberColumn(format="%.1f", width="small"),
            "Left":   st.column_config.NumberColumn(width="small"),
            "Proj.":  st.column_config.NumberColumn(format="%d", width="small"),
            "Range":  st.column_config.TextColumn(width="medium"),
            "Finals?": st.column_config.TextColumn(width="small"),
            "Club":   st.column_config.TextColumn(width="medium"),
        },
        height=560,
    )

    st.divider()

    # --- top 10 probability callout ---
    st.subheader("Finals picture")
    top10 = ladder[ladder["Projected_Rank"] <= 10].sort_values("Projected_Rank")
    bubble = ladder[(ladder["Rank_Range_Best"] <= 10) & (ladder["Projected_Rank"] > 10)].sort_values("Projected_Rank")

    col_top, col_bub = st.columns(2)
    with col_top:
        st.markdown("**Projected top 10**")
        for _, row in top10.iterrows():
            st.markdown(
                f"**{int(row['Projected_Rank'])}.** {row['Team']} "
                f"<span style='color:{SLATE};font-size:0.85rem;'>({int(row['Rank_Range_Best'])}–{int(row['Rank_Range_Worst'])})</span>",
                unsafe_allow_html=True,
            )
    with col_bub:
        if not bubble.empty:
            st.markdown("**Outside chance** *(best case makes finals)*")
            for _, row in bubble.iterrows():
                st.markdown(
                    f"**{row['Team']}** — proj. {int(row['Projected_Rank'])}, "
                    f"<span style='color:{SLATE};font-size:0.85rem;'>best case {int(row['Rank_Range_Best'])}</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown("**Outside chance**")
            st.caption("No clubs outside the projected top 10 have a best-case finals finish.")

# ========================================================================
# TEAM PERFORMANCE
# ========================================================================
elif page == "Team Performance":
    st.markdown('<div class="bl-eyebrow">01 / Team Performance</div>', unsafe_allow_html=True)
    st.title("Team Performance and Rankings")
    st.markdown('<p class="bl-lede">Every club\'s standings since 2012.'
                ' Pick a season to compare clubs, or select a club to see its full game log.</p>',
                unsafe_allow_html=True)
    st.divider()

    seasons = dl.get_all_seasons()
    summary = dl.get_team_season_summary()

    season_sel = st.selectbox("Season", seasons, index=0)
    season_rows = summary[summary["Season"] == season_sel].sort_values("Win_Pct", ascending=False)

    # --- Elo rating history (replaces the season standings table) ---
    st.subheader("Elo rating history")
    st.caption("Team strength over time tracked using the [Elo model framework](https://thestatwire.com/guides/elo-ratings-explained).")

    elo_season_hist = dl.get_team_elo_history(season=season_sel)

    if elo_season_hist.empty:
        st.info(f"No Elo data found for {season_sel}.")
    else:
        all_season_teams = sorted(elo_season_hist["Team"].unique().tolist())

        # # Default to the teams actually worth looking at right now — the
        # # top 3 and bottom 3 by their most recent Elo this season — rather
        # # than an arbitrary/alphabetical subset.
        # latest_by_team = (
        #     elo_season_hist.sort_values("RoundNumber")
        #     .groupby("Team")["Elo"].last()
        #     .sort_values(ascending=False)
        # )
        # default_highlight = latest_by_team.head(3).index.tolist() + latest_by_team.tail(3).index.tolist()

        # highlight_sel = st.multiselect(
        #     "Highlight clubs",
        #     all_season_teams,
        #     default=[t for t in default_highlight if t in all_season_teams],
        #     help="The rest fade into the background so the chart stays readable with 18 lines on it.",
        # )
        highlight = set(all_season_teams)

        fig_elo = go.Figure()
        label_teams = []  # collect end-of-line label candidates, position them after the loop

        for team in all_season_teams:
            t_data = elo_season_hist[elo_season_hist["Team"] == team].sort_values("RoundNumber")
            if t_data.empty:
                continue
            is_hl = team in highlight
            color = TEAM_COLORS.get(team, SLATE)
            fig_elo.add_trace(go.Scatter(
                x=t_data["RoundNumber"], y=t_data["Elo"],
                name=team, mode="lines",
                line=dict(color=color if is_hl else HAIRLINE, width=2.6 if is_hl else 1.3),
                opacity=1.0 if is_hl else 0.7,
                hovertemplate=f"<b>{team}</b><br>" + "Round %{x}<br>Elo: %{y:.0f}<extra></extra>",
                showlegend=is_hl,
            ))
            if is_hl:
                last = t_data.iloc[-1]
                label_teams.append({
                    "team": team, "color": color,
                    "x": last["RoundNumber"], "y": last["Elo"],
                })

        # League-average reference line so a club's trajectory reads against
        # the competition, not just in isolation.
        league_avg = elo_season_hist.groupby("RoundNumber", as_index=True)["Elo"].mean()
        fig_elo.add_trace(go.Scatter(
            x=league_avg.index, y=league_avg.values,
            name="League average", mode="lines",
            line=dict(color=INK, width=1, dash="dot"),
            hovertemplate="League average<br>Round %{x}<br>Elo: %{y:.0f}<extra></extra>",
        ))

        # ---- De-overlap end-of-line labels ----
        # Without this, clubs that finish the season with similar Elo ratings
        # get labels stacked on top of each other. We convert the chart's
        # Elo range into an approximate pixel scale, then greedily push
        # labels apart (highest to lowest) so each keeps a minimum gap from
        # the one above it. A thin leader line marks any label nudged far
        # enough from its true value that the connection isn't obvious.
        CHART_HEIGHT_PX = 480
        PLOT_HEIGHT_PX = CHART_HEIGHT_PX - 30 - 40  # minus top/bottom margins
        LABEL_PX_HEIGHT = 16                        # ~11px font + padding

        if label_teams:
            y_min, y_max = elo_season_hist["Elo"].min(), elo_season_hist["Elo"].max()
            data_per_px = (y_max - y_min) / PLOT_HEIGHT_PX if PLOT_HEIGHT_PX else 1
            min_gap = LABEL_PX_HEIGHT * data_per_px

            label_teams.sort(key=lambda d: d["y"], reverse=True)
            for i, item in enumerate(label_teams):
                if i == 0:
                    item["y_label"] = item["y"]
                else:
                    item["y_label"] = min(item["y"], label_teams[i - 1]["y_label"] - min_gap)

            for item in label_teams:
                fig_elo.add_annotation(
                    x=item["x"], y=item["y_label"],
                    text=f"  {item['team']}", showarrow=False, xanchor="left", align="left",
                    font=dict(size=11, color=item["color"], family=f'{THEME["font_mono"]}, monospace'),
                )
                if abs(item["y_label"] - item["y"]) > min_gap * 0.5:
                    fig_elo.add_shape(
                        type="line",
                        x0=item["x"], x1=item["x"] + 0.4,
                        y0=item["y"], y1=item["y_label"],
                        line=dict(color=item["color"], width=0.75),
                        opacity=0.5,
                    )

        layout_no_yaxis_margin = {k: v for k, v in PLOTLY_BASE.items() if k not in ("yaxis", "margin")}
        fig_elo.update_layout(
            **layout_no_yaxis_margin,
            height=CHART_HEIGHT_PX,
            margin=dict(l=40, r=105, t=30, b=40),  # slightly wider — room for longer club names
            xaxis_title="Round",
            yaxis=dict(**PLOTLY_BASE["yaxis"], title="Elo rating"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            hovermode="closest",
        )
        st.plotly_chart(fig_elo, use_container_width=True)
        st.caption(f"Highlighting {len(highlight)} of {len(all_season_teams)} clubs. Pick clubs above to compare specific rivalries or premiership form.")

    st.divider()
    st.subheader("Club detail")
    team_sel = st.selectbox("Select a club", dl.get_all_teams())

    team_games = dl.get_team_results()

    tg = team_games[(team_games["Team"]==team_sel) & (team_games["Season"]==season_sel)].sort_values("RoundNumber")

    if tg.empty:
        st.warning(f"No games found for {team_sel} in {season_sel}.")
    else:
        sr = summary[(summary["Team"]==team_sel) & (summary["Season"]==season_sel)].iloc[0]
        record = f"{int(sr['Wins'])}-{int(sr['Losses'])}"
        if sr["Draws"] > 0:
            record += f"-{int(sr['Draws'])}"
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Record", record)
        c2.metric("Win %", f"{sr['Win_Pct']:.1f}%")
        c3.metric("Avg margin", signed(sr["Avg_Margin"],1))
        c4.metric("Percentage", f"{sr['Percentage']:.1f}" if pd.notna(sr["Percentage"]) else "—")

        colors = [GREEN if m >= 0 else CLAY for m in tg["Margin"]]
        fig = go.Figure(go.Bar(
            x=tg["RoundNumber"], y=tg["Margin"], marker_color=colors,
            hovertemplate="Round %{x}<br>Margin: %{y:+}<extra></extra>",
        ))
        fig.update_layout(**PLOTLY_BASE, 
                          title=f"Margin by round — {team_sel}, {season_sel}", 
                          height=300,
                          xaxis_title="Round", yaxis_title="Margin")
        st.plotly_chart(fig, use_container_width=True)

        gcols = ["RoundNumber","Date","Opposition_Team","Venue","Result","Points","Opposition_Points","Margin"]
        gcols = [c for c in gcols if c in tg.columns]
        st.dataframe(
            tg[gcols].rename(columns={"RoundNumber":"Rd","Opposition_Team":"Opponent",
                                       "Points":"For","Opposition_Points":"Against"}),
            use_container_width=True, hide_index=True,
            column_config={"Margin": st.column_config.NumberColumn(format="%+d")},
        )


# ========================================================================
# PLAYER PERFORMANCE
# ========================================================================

elif page == "Player Performance":
    st.markdown('<div class="bl-eyebrow">02 / Player Performance</div>', unsafe_allow_html=True)
    st.title("Player Performance and Rankings")
    st.markdown('<p class="bl-lede">Custom player ranking model plus stats leaderboard </p>', unsafe_allow_html=True)
    st.divider()

    latest, latest_season, latest_round = dl.get_latest_rankings()

    st.subheader("Composite ranking")
    st.markdown("Ranks as at current, calculated on a Team, Position and Overall basis. "
                "See **Methodology** for how it's built.")

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        pos_opts = ["All positions"] + sorted(latest["Position"].dropna().unique().tolist())
        pos_sel = st.selectbox("Position", pos_opts)
    with fc2:
        team_opts = ["All clubs"] + sorted(latest["Team"].dropna().unique().tolist())
        team_sel = st.selectbox("Club", team_opts)
    with fc3:
        search = st.text_input("Search player", placeholder="e.g. Bontempelli")

    filt = latest.copy()
    if pos_sel  != "All positions": filt = filt[filt["Position"] == pos_sel]
    if team_sel != "All clubs":     filt = filt[filt["Team"] == team_sel]
    if search:                      filt = filt[filt["Player"].str.contains(search, case=False, na=False)]

    st.dataframe(
        filt[["Rank_Overall","Player","Team","Position","Rank_By_Position","Rank_By_Team","composite_score"]
        ].rename(columns={"Rank_Overall":"Rank","Rank_By_Position":"Rank (Pos)",
                           "Rank_By_Team":"Rank (Club)","composite_score":"Composite"}),
        use_container_width=True, hide_index=True, height=420,
        column_config={"Composite": st.column_config.NumberColumn(format="%.3f")},
    )

    st.divider()
    st.subheader("Player detail")
    player_sel = st.selectbox("Select a player", sorted(latest["Player"].dropna().unique().tolist()))

    if player_sel:
        prow = latest[latest["Player"]==player_sel].iloc[0]
        draft_id = prow.get("Draft_Player_Id")

        pc1,pc2,pc3,pc4 = st.columns(4)
        pc1.metric("Overall rank",    int(prow["Rank_Overall"]) if pd.notna(prow["Rank_Overall"]) else "—")
        pc2.metric("Position rank",   int(prow["Rank_By_Position"]) if pd.notna(prow["Rank_By_Position"]) else "—")
        pc3.metric("Club",            prow["Team"])
        pc4.metric("Composite score", f"{prow['composite_score']:.3f}" if pd.notna(prow["composite_score"]) else "—")

        season_summary = dl.get_player_season_rank_summary(draft_id)

        trend_col, summary_col = st.columns([2, 1])

        with trend_col:
            available_seasons = (
                sorted(season_summary["Season"].unique().tolist(), reverse=True)
                if not season_summary.empty else [latest_season]
            )
            default_idx = available_seasons.index(latest_season) if latest_season in available_seasons else 0
            trend_season = st.selectbox(
                "Season", available_seasons, index=default_idx, key="player_trend_season",
                help="Independent of the composite ranking table above — pick any season this player has data for.",
            )

            hist = dl.get_player_rank_history(draft_id, trend_season)
            if not hist.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hist["RoundNumber"], y=hist["Rank_Overall"],
                    name="Overall rank", mode="lines+markers",
                    line=dict(color=GREEN, width=2.5), marker=dict(size=6),
                    hovertemplate="Round %{x}<br>Overall rank: %{y}<extra></extra>",
                ))
                if "Rank_By_Position" in hist.columns and hist["Rank_By_Position"].notna().any():
                    fig.add_trace(go.Scatter(
                        x=hist["RoundNumber"], y=hist["Rank_By_Position"],
                        name="Position rank", mode="lines+markers",
                        line=dict(color=BLUE, width=2, dash="dot"), marker=dict(size=5),
                        hovertemplate="Round %{x}<br>Position rank: %{y}<extra></extra>",
                    ))
                layout_no_yaxis = {k:v for k,v in PLOTLY_BASE.items() if k != "yaxis"}
                fig.update_layout(**layout_no_yaxis,
                                title=dict(
                                    text=f"Rank trend, {trend_season} — {player_sel}",
                                    y=0.98,          # move title higher (0-1)
                                    x=0.5,           # center title
                                    xanchor="center",
                                    yanchor="top",
                                ),
                                height=500,
                                xaxis_title="Round", yaxis_title="Rank",
                                yaxis=dict(**PLOTLY_BASE["yaxis"], autorange="reversed"),
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No ranking data for {player_sel} in {trend_season}.")

        with summary_col:
            st.markdown("**Average rank by season**")
            if season_summary.empty:
                st.caption("No historical ranking data available for this player.")
            else:
                for _, srow in season_summary.iterrows():
                    change_html = (
                        movement_icon(srow["Change"])
                        if pd.notna(srow["Change"])
                        else '<span class="movement-flat"></span>'
                    )
                    st.markdown(
                        f"""<div style="
                            display:grid;
                            grid-template-columns:1fr auto 1fr;
                            align-items:baseline;
                            padding:0.45rem 0;
                            border-bottom:1px solid {HAIRLINE};
                        ">
                            <span style="justify-self:start;">{srow['Season']}</span>
                            <span style="justify-self:center;font-weight:600;">
                                {srow['Avg_Rank_Overall']:.0f}
                            </span>
                            <span style="justify-self:end;">
                                {change_html}
                            </span>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                st.caption("Change vs. the previous season's average. ▲ = rank improved (lower number).")

        career_log = dl.get_player_career_log(player_sel)
        if not career_log.empty:
            log_cols = ["Season","RoundNumber","Opposition","D","K","HB","M","G","T","SC"]
            log_cols = [c for c in log_cols if c in career_log.columns]
            st.dataframe(
                career_log[log_cols].rename(columns={"RoundNumber":"Rd","Opposition":"Opponent","SC":"SuperCoach"})
                          .sort_values(["Season","Rd"], ascending=[False,False]),
                use_container_width=True, hide_index=True, height=350,
            )

    st.divider()
    st.subheader("Raw stat leaderboards")
    st.caption(f"Season {latest_season}")

    lb = dl.get_player_season_leaderboard(latest_season)
    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        stat_sel = st.selectbox("Sort by", list(dl.STAT_LABELS.keys()),
                                format_func=lambda k: dl.STAT_LABELS[k],
                                index=list(dl.STAT_LABELS.keys()).index("D"))
    with lc2:
        mode_sel = st.radio("Mode", ["Per game average","Season total"], horizontal=True)
    with lc3:
        lb_search = st.text_input("Search player ", placeholder="e.g. Daicos")

    suffix = "avg" if mode_sel == "Per game average" else "total"
    stat_col = f"{stat_sel}_{suffix}"
    lb_filt = lb.copy()
    if lb_search:
        lb_filt = lb_filt[lb_filt["Player"].str.contains(lb_search, case=False, na=False)]
    lb_filt = lb_filt.sort_values(stat_col, ascending=False)

    st.dataframe(
        lb_filt[["Player","Team","Position","Games",stat_col]
        ].rename(columns={stat_col: dl.STAT_LABELS[stat_sel]}),
        use_container_width=True, hide_index=True, height=460,
    )

# ========================================================================
# MODEL Performance
# ========================================================================

elif page == "Model Performance":
    st.markdown('<div class="bl-eyebrow">03 / Model Performance</div>', unsafe_allow_html=True)
    st.title("Model Performance")

    predictions = dl.get_predictions()
    by_season, overall = dl.get_prediction_summary()
    fmt = overall.get("fmt","old")

    st.markdown(
        '<p class="bl-lede">Two regression models run for each game: a <strong>LOGIT</strong> classifier for '
        "win/loss probability, and an <strong>OLS</strong> regression for predicted margin. "
        "</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    oc1, oc2, oc3 = st.columns(3)
    oc1.metric("LOGIT win/loss accuracy", f"{overall['accuracy_logit']}%",
                help="Did the predicted winner match the actual result?")
    oc2.metric("OLS win/loss accuracy",   f"{overall['accuracy_ols']}%",
                help="Did the sign of the OLS margin match the actual result?")
    oc3.metric("OLS mean abs. error",     f"{overall['mae_ols']:.1f} pts",
                help="Average distance between predicted and actual margin")

    st.subheader("Accuracy by season")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=by_season["Season"], y=by_season["Accuracy_LOGIT"],
        name="LOGIT accuracy", mode="lines+markers",
        line=dict(color=GREEN, width=2.5), marker=dict(size=7),
        hovertemplate="%{x}<br>LOGIT: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=by_season["Season"], y=by_season["Accuracy_OLS"],
        name="OLS accuracy", mode="lines+markers",
        line=dict(color=GOLD, width=2, dash="dot"), marker=dict(size=6),
        hovertemplate="%{x}<br>OLS accuracy: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=by_season["Season"], y=by_season["MAE_OLS"],
        name="OLS MAE (pts)", mode="lines+markers",
        line=dict(color=CLAY, width=2, dash="dash"), marker=dict(size=6),
        yaxis="y2",
        hovertemplate="%{x}<br>MAE: %{y:.1f} pts<extra></extra>",
    ))
    layout_no_yaxis = {k:v for k,v in PLOTLY_BASE.items() if k not in ("yaxis",)}
    fig.update_layout(
        **layout_no_yaxis, height=380,
        yaxis=dict(title="Win/loss accuracy (%)", gridcolor=HAIRLINE, zeroline=False),
        yaxis2=dict(title="Mean abs. error (pts)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- team accuracy by season (new format) ---
    st.subheader("Accuracy by Team")

    scored_games_ts = dl.get_completed_predictions()
    all_seasons_ts = sorted(scored_games_ts["Season"].unique().tolist(), reverse=True)
    ts_season = st.selectbox(
        "Season", all_seasons_ts, index=0, key="team_season_filter"
    )

    team_season = dl.get_team_season_accuracy(ts_season)

    overall_acc = team_season["Accuracy"].mean().round(1) if len(team_season) else 0

    fig_ts = go.Figure(go.Bar(
        x=team_season["Accuracy"],
        y=team_season["Team"],
        orientation="h",
        marker_color=[GREEN if v >= 50 else CLAY for v in team_season["Accuracy"]],
        text=team_season["Accuracy"].map(lambda v: f"{v:.1f}%"),
        textposition="outside",
        customdata=team_season["Games"],
        hovertemplate="%{y}<br>Accuracy: %{x:.1f}%<br>Games: %{customdata}<extra></extra>",
    ))
    fig_ts.add_vline(x=50, line_dash="dot", line_color=HAIRLINE)

    # Strip BOTH axes from the base layout, then merge our overrides on top
    # of PLOTLY_BASE's own axis settings (dict(**a, key=val) fails if `key`
    # already exists in `a`, so use a plain dict merge instead).
    layout_no_axes = {k: v for k, v in PLOTLY_BASE.items() if k not in ("xaxis", "yaxis")}
    fig_ts.update_layout(
        **layout_no_axes,
        height=max(320, 28 * len(team_season)),
        xaxis={
            **PLOTLY_BASE.get("xaxis", {}),
            "title": "Accuracy (%)",
            "range": [0, 105],
            "gridcolor": HAIRLINE,
            "zeroline": False,
        },
        yaxis={
            **PLOTLY_BASE.get("yaxis", {}),
            "autorange": "reversed",
        },
        showlegend=False,
    )
    st.plotly_chart(fig_ts, use_container_width=True)
    st.caption(f"{ts_season} average across teams: {overall_acc}%")
    

    # --- game explorer (both formats) ---
    st.divider()
    st.subheader("Past prediction")

    scored_games = dl.get_completed_predictions()    
    # st.caption(f"{len(scored_games):,} scored predictions")
    st.caption("All margins and predictions below are in respect to the **home team**. "
               "I.e. a positive margin or predicted margin means the home team is favoured/won.")

    fc1, fc2, fc3, fc4 = st.columns(4)

    with fc1:
        all_seasons = ["All seasons"] + sorted(scored_games["Season"].unique().tolist(), reverse=True)
        s_filter = st.selectbox("Season", all_seasons, key="pred_season")

    with fc2:
        teams = sorted(
            set(scored_games["Team"].dropna())
            | set(scored_games["Opposition_Team"].dropna())
        )

        all_teams = ["All teams"] + teams

        t_filter = st.selectbox(
            "Team",
            all_teams,
            key="pred_team",
            help="Filters games where this team appears as either home or away.",
        )

    with fc3:
        all_rounds = ["All rounds"] + sorted(scored_games["RoundNumber"].dropna().unique().tolist())
        r_filter = st.selectbox("Round", all_rounds, key="pred_round")

    with fc4:
        outcome_opts = ["Correct & incorrect","LOGIT correct","LOGIT incorrect",
                        "OLS correct","OLS incorrect"]
        o_filter = st.selectbox("Outcome", outcome_opts)

    pg = scored_games.copy()

    if s_filter != "All seasons":
        pg = pg[pg["Season"] == s_filter]

    if t_filter != "All teams":
        pg = pg[
            (pg["Team"] == t_filter) |
            (pg["Opposition_Team"] == t_filter)
        ]

    if r_filter != "All rounds":
        pg = pg[pg["RoundNumber"] == r_filter]

    if o_filter == "LOGIT correct":
        pg = pg[pg["Correct_LOGIT"]]
    elif o_filter == "LOGIT incorrect":
        pg = pg[~pg["Correct_LOGIT"]]
    elif o_filter == "OLS correct":
        pg = pg[pg["Correct_OLS"]]
    elif o_filter == "OLS incorrect":
        pg = pg[~pg["Correct_OLS"]]

    pg = pg.sort_values("Date", ascending=False)

    disp_cols = {
        "Date_str":"Date","Season":"Season","RoundNumber":"Rd","Team":"Home Team",
        "Opposition_Team":"Away Team","Margin":"Actual (Home)",
        "Predicted_Margin_OLS":"Pred Margin (Home)","Abs_Error_OLS":"Margin Err",
        "Predicted_Prob_LOGIT":"LOGIT Prob (Home)",
        "Correct_LOGIT":"LOGIT ✓","Correct_OLS":"OLS ✓",
    }

    avail = {k:v for k,v in disp_cols.items() if k in pg.columns}
    pg_disp = pg[list(avail.keys())].rename(columns=avail)
    if "Correct" in pg_disp.columns:
        pg_disp["Correct"] = pg_disp["Correct"].map({True:"✅",False:"❌"})
    if "LOGIT ✓" in pg_disp.columns:
        pg_disp["LOGIT ✓"] = pg_disp["LOGIT ✓"].map({True:"✅",False:"❌"})
    if "OLS ✓" in pg_disp.columns:
        pg_disp["OLS ✓"] = pg_disp["OLS ✓"].map({True:"✅",False:"❌"})

    col_cfg = {}
    for c in ["Actual (Home)","Predicted (Home)","Pred Margin (Home)"]:
        if c in pg_disp.columns:
            col_cfg[c] = st.column_config.NumberColumn(
                format="%+d", help="Positive = home team win/favoured margin."
            )
    for c in ["Error","Margin Err"]:
        if c in pg_disp.columns:
            col_cfg[c] = st.column_config.NumberColumn(format="%.1f")
    if "LOGIT Prob (Home)" in pg_disp.columns:
        col_cfg["LOGIT Prob (Home)"] = st.column_config.NumberColumn(
            format="%.3f", help="Model's estimated probability that the home team wins."
        )

    st.dataframe(pg_disp, use_container_width=True, hide_index=True, height=460,
                 column_config=col_cfg)

# ========================================================================
# METHODOLOGY
# ========================================================================

elif page == "Methodology":
    st.markdown('<div class="bl-eyebrow">04 / Methodology</div>', unsafe_allow_html=True)
    st.title("How this is actually built")
    st.markdown(
        '<p class="bl-lede">The end to end modelling pipeline operates across five core stages, moving from raw data acquisition through to feature construction, '
        "selection, and rolling window prediction.</p>",
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("""
### 1. Web Scraping & Data Collection

Primary AFL datasets, including player statistics, coaches’ votes, match results, and historical performance, 
are sourced via the Fitzroy R package, supplemented by custom scrapers for:
                
- Player bios (Footywire)
- Market odds (OddsPortal)

### 2. Data Standardisation, Adjustments & Imputation

Due to variations in the source data, a structured process has been delevoped to ensure compatibility, as well as applying certain adjustments.
                
This process includes:
                
- **Standardisation**: Alignment of round numbers, team names and venue labels.
- **Name Matching Framework**: A multi layered system iterates from strict (exact match) to flexible (fuzzy match) methods, with a validation layer that flags uncertain cases for manual review.
- **Data Adjustments**: Targeted corrections are applied to account for:
    - Early game injuries
    - Non standard seasons (e.g., shortened quarters in 2020)
    - Ambiguous or inconsistent positional data (e.g., substitutes)
- **Imputation**: Where datasets are incomplete for specific games, imputation strategies have been applied, including:
    - Scoreworm simulations based on historical team scoring profiles
    - Coaches’ votes inferred from player performance metrics

### 3. Feature Engineering

Features are generated across four major domains:
                
- **Player Statistics**: Player ratings and projected performance for listed players
- **Team Statistics**: Team level metrics, historical form, and Elo ratings
- **Scoreworm Dynamics**: Momentum indicators and in game scoring pattern features
- **Game Results & Market Data**: Win/loss trends and odds movements
                
Features are aggregated across multiple time horizons (e.g., last 3 games) and multiple grains (e.g. venue, matchup). Additional scaling is applied using team Elo ratings, reducing inflation from strong performances against weaker opponents.

### 4. Feature Selection

A cross season evaluation framework is used to identify the most predictive and consistent variables. Shapley Additive Explanations (SHAP) values had been used on refine the feature set down to 25 high impact predictors.

### 5. Modelling & Prediction

Both the linear and logistic models are trained and deployed using a rolling season‑round window, where all matches prior to the target round form the training set. Predictions are then generated for the upcoming round, with all outputs stored and surfaced through this dashboard.

> Want further insights? See the **Q&A** page.
""")


# ========================================================================
# Q&A
# ========================================================================

elif page == "Q&A":
    st.markdown('<div class="bl-eyebrow">05 / Blog &amp; Q&amp;A</div>', unsafe_allow_html=True)
    st.title("Notes on building this")
    st.markdown(
        '<p class="bl-lede">Write-ups on modelling decisions, data quirks, and insights. </p>',
        unsafe_allow_html=True,
    )
    st.divider()

    main_col, side_col = st.columns([2, 1])
    posts = [
        {
            "tag": "Q&A",
            "date": "12/07/2026",
            "title": "Why is my favourite player ranked so low?",
            "excerpt": """
    The ranking methodology is built upon a weighted, three-season lookback window.

    Feature importance is position-dependent, with differential weighting used to prioritise the statistics most relevant to each role. For example, disposal volume is given greater importance for midfielders than forwards.

    Each player's performance is converted into a game score for every match, with games significantly impacted by injury adjusted accordingly. These game scores are then aggregated into a cumulative player score that is recalculated after every round.

    To account for absences through injury or non-selection, a decay factor is applied based on the player's most recent performance. This prevents long periods without games from leaving a player's ranking artificially unchanged.

    Finally, player scores are standardised against others in the same position, producing a normalised rating between 0 and 1.

    I don't claim this methodology is perfect, but it performs well as a practical way of distinguishing between stronger and weaker players.
    """
        },
        {
            "tag": "Q&A",
            "date": "12/07/2026",
            "title": "Why have you included the 2020 season?",
            "excerpt": """
    I'm still not completely convinced that the 2020 season should be included, but it wasn't added without careful consideration.

    To minimise the season's unique effects, each feature was scaled relative to the surrounding seasons (2019 and 2021). This helps reduce distributional shifts and keeps the data closer to the rest of the training set.

    The main reason for retaining 2020 is that the model only has data back to 2015. Removing an entire season would significantly reduce the amount of training data available.
    """
        }
    ]

    with main_col:
        for p in posts:
            formatted_excerpt = "<br><br>".join(
                paragraph.strip()
                for paragraph in p["excerpt"].strip().split("\n\n")
            )

            st.markdown(f"""
            <div style="padding:1.1rem 0;border-bottom:1px solid {HAIRLINE};">
                <div style="font-family:'{THEME["font_mono"]}',monospace;font-size:0.74rem;color:{THEME["muted"]};text-transform:uppercase;letter-spacing:0.04em;">
                    {p['tag']} &middot; {p['date']}
                </div>
                <h3 style="margin:0.3rem 0;">{p['title']}</h3>
                <p style="color:{THEME["body_text"]};margin:0;line-height:1.7;">
                    {formatted_excerpt}
                </p>
            </div>
            """, unsafe_allow_html=True)

    with side_col:
        st.markdown("""<div class="bl-card" style="margin-bottom:1rem;">
        <h4>Got a query?</h4>
        <p>Send an email to: rtdt87@outlook.com</p>
        </div>""", unsafe_allow_html=True)

st.divider()
st.caption("Tippo — a personal AFL analytics project. Data updated after each round.")
