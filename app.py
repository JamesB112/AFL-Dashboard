"""
Tippo — AFL Analytics
A personal portfolio app covering team performance, player rankings,
ladder projections, and a margin/win-probability prediction model.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

import data_loader as dl

st.set_page_config(
    page_title="Tippo — AFL Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ----------------------------------------------------------------------
# GLOBAL STYLE
# ----------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Page background: White */
[data-testid="stAppViewContainer"] {
    background: #FFFFFF;
}
[data-testid="stHeader"] {
    background: rgba(238, 242, 243, 0);
}
section[data-testid="stSidebar"] {
    background: #E4EAEC;
    border-right: 1px solid #C7D3D6;
}

h1, h2, h3 { font-family: 'Fraunces', Georgia, serif !important; font-weight: 600 !important; letter-spacing: -0.01em; color: #1B2B2E; }

[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace; color: #1B2B2E; }

.bl-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #1F6F50;
    margin-bottom: 0.3rem;
}

.bl-lede { font-size: 1.05rem; color: #3A4A4F; max-width: 70ch; }

.bl-card {
    background: #FFFFFF;
    border: 1px solid #C7D3D6;
    border-top: 3px solid #3E6E82;
    border-radius: 6px;
    padding: 1.1rem 1.3rem;
    height: 100%;
}
.bl-card h4 { margin: 0 0 0.4rem 0; font-family: 'Fraunces', serif; font-size: 1.15rem; color: #1B2B2E; }
.bl-card p  { margin: 0; color: #3A4A4F; font-size: 0.92rem; }

.movement-up   { color: #1F6F50; font-weight: 600; }
.movement-down { color: #B3492C; font-weight: 600; }
.movement-flat { color: #5C6E76; }

hr, [data-testid="stDivider"] { border-color: #C7D3D6 !important; }
</style>
""", unsafe_allow_html=True)

GREEN    = "#1F6F50"
CLAY     = "#B3492C"
GOLD     = "#B68A2E"
SLATE    = "#5C6E76"
BLUE     = "#3E6E82"
INK      = "#1B2B2E"
PAPER    = "#FFFFFF"
HAIRLINE = "#C7D3D6"

PLOTLY_BASE = dict(
    font=dict(family="Inter, sans-serif", color=INK),
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
    st.markdown("### Tippo")
    st.caption("AFL Games Tipper")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["Home", "Team Performance", "Player Performance","Model Performance", "Methodology", "Blog / Q&A"],
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
                format="mixed",
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

        if fmt == "new":

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

        else:

            display_df["Prediction"] = np.where(
                current_disp["Predicted_Margin_Adjusted"] >= 0,
                current_disp[team_col],
                current_disp[opp_col],
            )

            display_df["Predicted Margin"] = (
                current_disp["Predicted_Margin_Adjusted"]
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
                    if fmt == "new"
                    else None
                ),
                "Predicted Margin": st.column_config.NumberColumn(
                    "Predicted Margin",
                    format="%.1f pts",
                ),
            },
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
            st.markdown("**On the bubble** *(best case makes finals)*")
            for _, row in bubble.iterrows():
                st.markdown(
                    f"**{row['Team']}** — proj. {int(row['Projected_Rank'])}, "
                    f"<span style='color:{SLATE};font-size:0.85rem;'>best case {int(row['Rank_Range_Best'])}</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown("**On the bubble**")
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

        elo_plot_df = elo_season_hist

        # Distinct categorical colors for team lines — separate from the brand
        # GREEN/CLAY/GOLD/SLATE palette, since those are semantic (win/loss,
        # correct/incorrect), not team identity, and won't scale to 18 lines.
        team_colors = px.colors.qualitative.Alphabet

        fig_elo = go.Figure()
        for i, team in enumerate(all_season_teams):
            if team not in elo_plot_df["Team"].unique():
                continue
            t_data = elo_plot_df[elo_plot_df["Team"] == team].sort_values("RoundNumber")
            fig_elo.add_trace(go.Scatter(
                x=t_data["RoundNumber"], y=t_data["Elo"],
                name=team, mode="lines",
                line=dict(color=team_colors[i % len(team_colors)], width=2),
                hovertemplate=f"{team}<br>" + "%{x|%d %b %Y}<br>Elo: %{y:.0f}<extra></extra>",
            ))

        layout_no_yaxis = {k: v for k, v in PLOTLY_BASE.items() if k != "yaxis"}
        fig_elo.update_layout(
            **layout_no_yaxis,
            height=460,
            xaxis_title="Round",
            yaxis=dict(**PLOTLY_BASE["yaxis"], title="Elo rating"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
            ),
            hovermode="closest",
        )
        st.plotly_chart(fig_elo, use_container_width=True)

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
        fig.update_layout(**PLOTLY_BASE, title=f"Margin by round — {team_sel}, {season_sel}", height=300,
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
        pc1,pc2,pc3,pc4 = st.columns(4)
        pc1.metric("Overall rank",    int(prow["Rank_Overall"]) if pd.notna(prow["Rank_Overall"]) else "—")
        pc2.metric("Position rank",   int(prow["Rank_By_Position"]) if pd.notna(prow["Rank_By_Position"]) else "—")
        pc3.metric("Club",            prow["Team"])
        pc4.metric("Composite score", f"{prow['composite_score']:.3f}" if pd.notna(prow["composite_score"]) else "—")

        hist = dl.get_player_rank_history(prow.get("Draft_Player_Id"), latest_season)
        if not hist.empty:
            fig = go.Figure(go.Scatter(
                x=hist["RoundNumber"], y=hist["Rank_Overall"],
                mode="lines+markers", line=dict(color=GREEN, width=2.5), marker=dict(size=6),
                hovertemplate="Round %{x}<br>Rank %{y}<extra></extra>",
            ))
            layout_no_yaxis = {k:v for k,v in PLOTLY_BASE.items() if k != "yaxis"}
            fig.update_layout(**layout_no_yaxis,
                              title=f"Rank trend, {latest_season} — {player_sel}", height=280,
                              xaxis_title="Round", yaxis_title="Overall rank",
                              yaxis=dict(**PLOTLY_BASE["yaxis"], autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

        career_log = dl.get_player_career_log(player_sel)
        if not career_log.empty:
            log_cols = ["Season","RoundNumber","Opposition","D","K","HB","M","G","T","AF"]
            log_cols = [c for c in log_cols if c in career_log.columns]
            st.dataframe(
                career_log[log_cols].rename(columns={"RoundNumber":"Rd","Opposition":"Opponent","AF":"Fantasy"})
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
    st.markdown('<div class="bl-eyebrow">04 / Model Performance</div>', unsafe_allow_html=True)
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
        if fmt == "new":
            outcome_opts = ["Correct & incorrect","LOGIT correct","LOGIT incorrect",
                            "OLS correct","OLS incorrect"]
        else:
            outcome_opts = ["Correct & incorrect","Correct only","Incorrect only"]
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

    if fmt == "new":
        if o_filter == "LOGIT correct":
            pg = pg[pg["Correct_LOGIT"]]
        elif o_filter == "LOGIT incorrect":
            pg = pg[~pg["Correct_LOGIT"]]
        elif o_filter == "OLS correct":
            pg = pg[pg["Correct_OLS"]]
        elif o_filter == "OLS incorrect":
            pg = pg[~pg["Correct_OLS"]]
    else:
        if o_filter == "Correct only":
            pg = pg[pg["Correct"]]
        elif o_filter == "Incorrect only":
            pg = pg[~pg["Correct"]]

    pg = pg.sort_values("Date", ascending=False)

    if fmt == "new":
        disp_cols = {
            "Date_str":"Date","Season":"Season","RoundNumber":"Rd","Team":"Home Team",
            "Opposition_Team":"Away Team","Margin":"Actual (Home)",
            "Predicted_Margin_OLS":"Pred Margin (Home)","Abs_Error_OLS":"Margin Err",
            "Predicted_Prob_LOGIT":"LOGIT Prob (Home)",
            "Correct_LOGIT":"LOGIT ✓","Correct_OLS":"OLS ✓",
        }
    else:
        disp_cols = {
            "Date_str":"Date","Season":"Season","RoundNumber":"Rd","Team":"Home Team",
            "Opposition_Team":"Away Team","Margin":"Actual (Home)",
            "Predicted_Margin_Adjusted":"Predicted (Home)","Abs_Error":"Error","Correct":"Correct",
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
    st.markdown('<div class="bl-eyebrow">Methodology</div>', unsafe_allow_html=True)
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

> Questions about a specific modelling decision? Ask on the **Blog / Q&A** page.
""")


# ========================================================================
# BLOG / Q&A
# ========================================================================

elif page == "Blog / Q&A":
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
            <div style="padding:1.1rem 0;border-bottom:1px solid #E3E1D9;">
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.74rem;color:#707B85;text-transform:uppercase;letter-spacing:0.04em;">
                    {p['tag']} &middot; {p['date']}
                </div>
                <h3 style="margin:0.3rem 0;">{p['title']}</h3>
                <p style="color:#3A3F45;margin:0;line-height:1.7;">
                    {formatted_excerpt}
                </p>
            </div>
            """, unsafe_allow_html=True)

    with side_col:
        st.markdown("""<div class="bl-card" style="margin-bottom:1rem;">
        <h4>Got a question?</h4>
        <p>Send an email to: rtdt87@outlook.com</p>
        </div>""", unsafe_allow_html=True)

st.divider()
st.caption("Tippo — a personal AFL analytics project. Data updated after each round.")
