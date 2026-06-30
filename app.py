"""
Boundary Line — AFL Analytics
A personal portfolio app covering team performance, player rankings,
and a margin-prediction model, built on round-by-round AFL data.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

import data_loader as dl

st.set_page_config(
    page_title="Boundary Line — AFL Analytics",
    page_icon="🏉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# GLOBAL STYLE
# ----------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"]  { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }

h1, h2, h3 { font-family: 'Fraunces', Georgia, serif !important; font-weight: 600 !important; letter-spacing: -0.01em; }

.tabular-num { font-family: 'JetBrains Mono', monospace; }

[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace; }

.bl-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #1F6F50;
    margin-bottom: 0.3rem;
}

.bl-lede { font-size: 1.05rem; color: #3A3F45; max-width: 70ch; }

.bl-card {
    background: #FFFFFF;
    border: 1px solid #E3E1D9;
    border-radius: 6px;
    padding: 1.1rem 1.3rem;
    height: 100%;
}

.bl-card h4 { margin: 0 0 0.4rem 0; font-family: 'Fraunces', serif; font-size: 1.15rem; }
.bl-card p { margin: 0; color: #3A3F45; font-size: 0.92rem; }

.result-pill {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 1px 8px;
    border-radius: 3px;
}
.pill-W { background: #E8F0EA; color: #1F6F50; }
.pill-L { background: #F5E8E3; color: #B3492C; }
.pill-D { background: #EFE9DA; color: #B68A2E; }

hr { border-color: #E3E1D9 !important; }
</style>
""", unsafe_allow_html=True)

GREEN = "#1F6F50"
CLAY = "#B3492C"
GOLD = "#B68A2E"
SLATE = "#707B85"
INK = "#14171A"
PAPER_RAISED = "#FFFFFF"
HAIRLINE = "#E3E1D9"

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, sans-serif", color=INK),
    plot_bgcolor=PAPER_RAISED,
    paper_bgcolor=PAPER_RAISED,
    margin=dict(l=40, r=20, t=30, b=40),
    xaxis=dict(gridcolor=HAIRLINE, zeroline=False),
    yaxis=dict(gridcolor=HAIRLINE, zeroline=False),
)


def result_pill(result):
    return f'<span class="result-pill pill-{result}">{result}</span>'


def signed(n, decimals=0):
    if n is None or pd.isna(n):
        return "—"
    sign = "+" if n > 0 else ""
    return f"{sign}{n:.{decimals}f}"


# ----------------------------------------------------------------------
# DATA AVAILABILITY CHECK
# ----------------------------------------------------------------------

all_present, missing = dl.data_files_present()
if not all_present:
    st.error(
        "Some expected data files are missing from the `data/` folder:\n\n"
        + "\n".join(f"- `{m}`" for m in missing)
        + "\n\nDrop the matching CSV exports into `data/` and reload the app."
    )
    st.stop()

# ----------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ----------------------------------------------------------------------

with st.sidebar:
    st.markdown("### 🏉 Boundary Line")
    st.caption("AFL Analytics — a personal project")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["Home", "Team Performance", "Player Performance", "Model Predictions", "Methodology", "Blog / Q&A"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    meta = dl.get_meta()
    st.caption(f"Data through **{meta['latest_season']}, Round {meta['latest_round']}**")
    st.caption(f"{meta['teams_tracked']} clubs · {meta['players_tracked']:,} players tracked")


# ========================================================================
# PAGE: HOME
# ========================================================================

if page == "Home":
    meta = dl.get_meta()

    col1, col2 = st.columns([1.4, 1])
    with col1:
        st.markdown('<div class="bl-eyebrow">A personal AFL analytics project</div>', unsafe_allow_html=True)
        st.title("Footy, measured.")
        st.markdown(
            '<p class="bl-lede">Fourteen seasons of AFL results, player box scores, and a margin-prediction '
            "model I built and keep grading in public. Explore the data, see how the model is tracking, "
            "and read the methodology behind it.</p>",
            unsafe_allow_html=True,
        )
        st.write("")
        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("See the model's record →", use_container_width=True, type="primary"):
                st.session_state["_nav_request"] = "Model Predictions"
        with bcol2:
            if st.button("Read the methodology →", use_container_width=True):
                st.session_state["_nav_request"] = "Methodology"

    with col2:
        st.metric("Model win/loss accuracy, all-time", f"{meta['model_accuracy_pct']}%",
                   help=f"{meta['model_games_scored']:,} games scored since 2015")
        st.metric("Latest data", f"{meta['latest_season']} · Round {meta['latest_round']}",
                   help=f"{meta['teams_tracked']} clubs, {meta['players_tracked']:,} players tracked this round")

    st.divider()

    lcol1, lcol2, lcol3, lcol4 = st.columns(4)
    seasons = dl.get_all_seasons()
    lcol1.metric("Seasons covered", f"{seasons[-1]}–{seasons[0]}")
    lcol2.metric("Model MAE", f"{meta['model_mae']:.1f} pts")
    lcol3.metric("Predictions graded", f"{meta['model_games_scored']:,}")
    lcol4.metric("Clubs tracked", meta["teams_tracked"])

    st.divider()
    st.subheader("Explore the data")
    st.caption("Four ways into the same dataset")

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown("""
        <div class="bl-card">
        <span style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#707B85;">01 / Team Performance</span>
        <h4>How every club is actually playing</h4>
        <p>Ladder form, scoring margins, and quarter-by-quarter trends for all 18 clubs back to 2012 — sortable, season by season.</p>
        </div>
        """, unsafe_allow_html=True)
    with r1c2:
        st.markdown("""
        <div class="bl-card">
        <span style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#707B85;">02 / Player Performance</span>
        <h4>A season-long player ranking model</h4>
        <p>My composite ranking system applied to every player, every round, plus raw leaderboards for disposals, goals, Fantasy and more.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown("""
        <div class="bl-card">
        <span style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#707B85;">03 / Model Predictions</span>
        <h4>Grading the margin model, in public</h4>
        <p>Every prediction the model has made since 2015, scored against what actually happened. No cherry-picking — wins and misses both shown.</p>
        </div>
        """, unsafe_allow_html=True)
    with r2c2:
        st.markdown("""
        <div class="bl-card">
        <span style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#707B85;">04 / Blog &amp; Q&amp;A</span>
        <h4>Notes on building this</h4>
        <p>Write-ups on the modelling choices, the data pipeline, and answers to questions readers send in.</p>
        </div>
        """, unsafe_allow_html=True)

    st.info("Use the sidebar to navigate to any section — the buttons above just set context for next time you click across.")


# ========================================================================
# PAGE: TEAM PERFORMANCE
# ========================================================================

elif page == "Team Performance":
    st.markdown('<div class="bl-eyebrow">01 / Team Performance</div>', unsafe_allow_html=True)
    st.title("Club form, season by season")
    st.markdown(
        '<p class="bl-lede">Every club\'s results since 2012 — wins, margins, percentage, and quarter-by-quarter '
        "trends. Pick a season to compare clubs, or select a club below to see its full game log.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    seasons = dl.get_all_seasons()
    summary = dl.get_team_season_summary()

    fcol1, fcol2 = st.columns([1, 3])
    with fcol1:
        season_sel = st.selectbox("Season", seasons, index=0)

    season_rows = summary[summary["Season"] == season_sel].copy()
    season_rows = season_rows.sort_values("Win_Pct", ascending=False)

    display_cols = {
        "Team": "Club", "Played": "P", "Wins": "W", "Losses": "L", "Draws": "D",
        "Win_Pct": "Win %", "Points_For": "PF", "Points_Against": "PA",
        "Percentage": "Pct", "Avg_Margin": "Avg Margin",
    }
    show_df = season_rows[list(display_cols.keys())].rename(columns=display_cols)

    st.dataframe(
        show_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Win %": st.column_config.NumberColumn(format="%.1f%%"),
            "Avg Margin": st.column_config.NumberColumn(format="%+.1f"),
            "Pct": st.column_config.NumberColumn(format="%.1f"),
        },
        height=460,
    )

    st.divider()
    st.subheader("Club detail")
    team_sel = st.selectbox("Select a club to drill in", dl.get_all_teams())

    team_games = dl.get_team_results()
    team_games = team_games[(team_games["Team"] == team_sel) & (team_games["Season"] == season_sel)].sort_values("RoundNumber")

    if team_games.empty:
        st.warning(f"No games found for {team_sel} in {season_sel}.")
    else:
        season_summary_row = summary[(summary["Team"] == team_sel) & (summary["Season"] == season_sel)].iloc[0]

        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        record = f"{int(season_summary_row['Wins'])}-{int(season_summary_row['Losses'])}"
        if season_summary_row["Draws"] > 0:
            record += f"-{int(season_summary_row['Draws'])}"
        mcol1.metric("Record", record)
        mcol2.metric("Win %", f"{season_summary_row['Win_Pct']:.1f}%")
        mcol3.metric("Avg margin", signed(season_summary_row["Avg_Margin"], 1))
        mcol4.metric("Percentage", f"{season_summary_row['Percentage']:.1f}" if pd.notna(season_summary_row["Percentage"]) else "—")

        # margin chart
        fig = go.Figure()
        colors = [GREEN if m >= 0 else CLAY for m in team_games["Margin"]]
        fig.add_trace(go.Bar(
            x=team_games["RoundNumber"], y=team_games["Margin"],
            marker_color=colors,
            hovertemplate="Round %{x}<br>Margin: %{y:+}<extra></extra>",
        ))
        fig.update_layout(**PLOTLY_LAYOUT, title=f"Margin by round — {team_sel}, {season_sel}", height=320,
                           xaxis_title="Round", yaxis_title="Margin")
        st.plotly_chart(fig, use_container_width=True)

        gcols = ["RoundNumber", "Date", "Opposition_Team", "Venue", "Result", "Points", "Opposition_Points", "Margin"]
        gdisp = team_games[gcols].rename(columns={
            "RoundNumber": "Rd", "Opposition_Team": "Opponent",
            "Points": "For", "Opposition_Points": "Against",
        })
        st.dataframe(
            gdisp, use_container_width=True, hide_index=True,
            column_config={"Margin": st.column_config.NumberColumn(format="%+d")},
        )


# ========================================================================
# PAGE: PLAYER PERFORMANCE
# ========================================================================

elif page == "Player Performance":
    st.markdown('<div class="bl-eyebrow">02 / Player Performance</div>', unsafe_allow_html=True)
    st.title("Who's actually playing well")
    st.markdown(
        '<p class="bl-lede">A composite ranking model scores every player after each round — built from form, '
        "output, and role rather than any single stat. Raw leaderboards sit underneath for anyone who wants "
        "the box-score numbers directly.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    latest, latest_season, latest_round = dl.get_latest_rankings()

    st.subheader("Composite ranking — current round")
    st.caption(f"Season {latest_season}, Round {latest_round} · {len(latest)} players ranked")
    st.markdown(
        "Rank is season-to-date, recalculated every round. Composite score is normalised 0–1 within the round; "
        "ties at the top are common early in a season. See the **Methodology** page for how it's built."
    )

    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        positions = ["All positions"] + sorted(latest["Position"].dropna().unique().tolist())
        pos_sel = st.selectbox("Position", positions)
    with fcol2:
        teams = ["All clubs"] + sorted(latest["Team"].dropna().unique().tolist())
        team_sel = st.selectbox("Club", teams)
    with fcol3:
        search = st.text_input("Search player", placeholder="e.g. Bontempelli")

    filtered = latest.copy()
    if pos_sel != "All positions":
        filtered = filtered[filtered["Position"] == pos_sel]
    if team_sel != "All clubs":
        filtered = filtered[filtered["Team"] == team_sel]
    if search:
        filtered = filtered[filtered["Player"].str.contains(search, case=False, na=False)]

    rank_disp = filtered[["Rank_Overall", "Player", "Team", "Position", "Rank_By_Position", "Rank_By_Team", "composite_score"]].rename(
        columns={
            "Rank_Overall": "Rank", "Rank_By_Position": "Rank (Pos)",
            "Rank_By_Team": "Rank (Club)", "composite_score": "Composite",
        }
    )
    st.dataframe(
        rank_disp, use_container_width=True, hide_index=True, height=420,
        column_config={"Composite": st.column_config.NumberColumn(format="%.3f")},
    )

    st.divider()
    st.subheader("Player detail")
    player_sel = st.selectbox("Select a player", sorted(latest["Player"].dropna().unique().tolist()))

    if player_sel:
        prow = latest[latest["Player"] == player_sel].iloc[0]
        pcol1, pcol2, pcol3, pcol4 = st.columns(4)
        pcol1.metric("Overall rank", int(prow["Rank_Overall"]) if pd.notna(prow["Rank_Overall"]) else "—")
        pcol2.metric("Position rank", int(prow["Rank_By_Position"]) if pd.notna(prow["Rank_By_Position"]) else "—")
        pcol3.metric("Club", prow["Team"])
        pcol4.metric("Composite score", f"{prow['composite_score']:.3f}" if pd.notna(prow["composite_score"]) else "—")

        draft_id = prow.get("Draft_Player_Id")
        hist = dl.get_player_rank_history(draft_id, latest_season)
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist["RoundNumber"], y=hist["Rank_Overall"], mode="lines+markers",
                line=dict(color=GREEN, width=2.5), marker=dict(size=6, color=GREEN),
                hovertemplate="Round %{x}<br>Rank %{y}<extra></extra>",
            ))
            layout_kwargs = {k: v for k, v in PLOTLY_LAYOUT.items() if k != "yaxis"}
            fig.update_layout(
                **layout_kwargs,
                title=f"Rank trend, {latest_season} — {player_sel}", height=300,
                xaxis_title="Round", yaxis_title="Overall rank",
                yaxis=dict(**PLOTLY_LAYOUT["yaxis"], autorange="reversed"),
            )
            st.plotly_chart(fig, use_container_width=True)

        career_log = dl.get_player_career_log(player_sel)
        if not career_log.empty:
            log_cols = ["Season", "RoundNumber", "Opposition", "D", "K", "HB", "M", "G", "T", "AF"]
            log_cols = [c for c in log_cols if c in career_log.columns]
            log_disp = career_log[log_cols].rename(columns={"RoundNumber": "Rd", "Opposition": "Opponent", "AF": "Fantasy"})
            log_disp = log_disp.sort_values(["Season", "Rd"], ascending=[False, False])
            st.dataframe(log_disp, use_container_width=True, hide_index=True, height=350)

    st.divider()
    st.subheader("Raw stat leaderboards")
    st.caption(f"Season {latest_season}")

    leaderboard = dl.get_player_season_leaderboard(latest_season)

    lcol1, lcol2, lcol3 = st.columns(3)
    with lcol1:
        stat_sel = st.selectbox("Sort by", list(dl.STAT_LABELS.keys()), format_func=lambda k: dl.STAT_LABELS[k], index=list(dl.STAT_LABELS.keys()).index("D"))
    with lcol2:
        mode_sel = st.radio("Mode", ["Per game average", "Season total"], horizontal=True)
    with lcol3:
        lb_search = st.text_input("Search player ", placeholder="e.g. Daicos", label_visibility="visible")

    mode_suffix = "avg" if mode_sel == "Per game average" else "total"
    stat_col = f"{stat_sel}_{mode_suffix}"

    lb_filtered = leaderboard.copy()
    if lb_search:
        lb_filtered = lb_filtered[lb_filtered["Player"].str.contains(lb_search, case=False, na=False)]
    lb_filtered = lb_filtered.sort_values(stat_col, ascending=False)

    lb_disp = lb_filtered[["Player", "Team", "Position", "Games", stat_col]].rename(
        columns={stat_col: dl.STAT_LABELS[stat_sel]}
    )
    st.dataframe(lb_disp, use_container_width=True, hide_index=True, height=460)


# ========================================================================
# PAGE: MODEL PREDICTIONS
# ========================================================================

elif page == "Model Predictions":
    st.markdown('<div class="bl-eyebrow">03 / Model Predictions</div>', unsafe_allow_html=True)
    st.title("Grading the model, in public")
    st.markdown(
        '<p class="bl-lede">An XGBoost model predicts the margin of every game before it\'s played. This page '
        "tracks how it's actually done — win/loss accuracy and average margin error, season by season — with "
        "every individual prediction available to inspect below.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    by_season, overall = dl.get_prediction_summary()

    ocol1, ocol2, ocol3 = st.columns(3)
    ocol1.metric("Win/loss accuracy, all-time", f"{overall['accuracy_pct']}%",
                 help=f"{overall['correct']:,} of {overall['games']:,} games called correctly")
    ocol2.metric("Mean absolute margin error", f"{overall['mean_abs_error']:.1f} pts",
                 help="Average distance between predicted and actual margin")
    ocol3.metric("Model", overall["model"], help="Gradient-boosted regression on margin")

    st.subheader("Accuracy by season")
    st.caption("Win/loss accuracy and mean absolute margin error")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=by_season["Season"], y=by_season["Accuracy_Pct"], name="Win/loss accuracy",
        mode="lines+markers", line=dict(color=GREEN, width=2.5), marker=dict(size=7),
        yaxis="y1", hovertemplate="%{x}<br>Accuracy: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=by_season["Season"], y=by_season["Mean_Abs_Error"], name="Mean abs. margin error",
        mode="lines+markers", line=dict(color=CLAY, width=2, dash="dot"), marker=dict(size=6),
        yaxis="y2", hovertemplate="%{x}<br>MAE: %{y:.1f} pts<extra></extra>",
    ))
    fig.update_layout(
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("yaxis",)},
        height=380,
        yaxis=dict(title="Win/loss accuracy (%)", gridcolor=HAIRLINE, zeroline=False),
        yaxis2=dict(title="Mean abs. error (pts)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    season_disp = by_season.rename(columns={
        "Season": "Season", "Games": "Games", "Correct": "Correct",
        "Accuracy_Pct": "Accuracy", "Mean_Abs_Error": "Mean Abs Error",
    }).sort_values("Season", ascending=False)
    st.dataframe(
        season_disp, use_container_width=True, hide_index=True,
        column_config={
            "Accuracy": st.column_config.NumberColumn(format="%.1f%%"),
            "Mean Abs Error": st.column_config.NumberColumn(format="%.1f pts"),
        },
    )

    st.divider()
    st.subheader("Upcoming fixture")
    st.caption("Not yet scored — predictions populate once the round is complete")

    upcoming = dl.get_upcoming_fixture()
    if upcoming.empty:
        st.info("No upcoming fixture data in the current export.")
    else:
        up_disp = upcoming[["Date", "Round", "HomeTeam", "AwayTeam", "Venue"]].rename(
            columns={"HomeTeam": "Home", "AwayTeam": "Away"}
        ).head(12)
        st.dataframe(up_disp, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Every prediction")

    predictions = dl.get_predictions()
    st.caption(f"{len(predictions):,} predictions, {overall['model']}")

    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        seasons_pred = ["All seasons"] + sorted(predictions["Season"].unique().tolist(), reverse=True)
        season_filter = st.selectbox("Season", seasons_pred, key="pred_season")
    with fcol2:
        teams_pred = ["All teams"] + sorted(predictions["Team"].dropna().unique().tolist())
        team_filter = st.selectbox("Team", teams_pred, key="pred_team")
    with fcol3:
        outcome_filter = st.selectbox("Outcome", ["Correct & incorrect", "Correct only", "Incorrect only"])

    pred_filtered = predictions.copy()
    if season_filter != "All seasons":
        pred_filtered = pred_filtered[pred_filtered["Season"] == season_filter]
    if team_filter != "All teams":
        pred_filtered = pred_filtered[pred_filtered["Team"] == team_filter]
    if outcome_filter == "Correct only":
        pred_filtered = pred_filtered[pred_filtered["Correct"]]
    elif outcome_filter == "Incorrect only":
        pred_filtered = pred_filtered[~pred_filtered["Correct"]]

    pred_filtered = pred_filtered.sort_values("Date", ascending=False)
    pred_disp = pred_filtered[[
        "Date", "Season", "RoundNumber", "Team", "Opposition_Team", "Margin",
        "Predicted_Margin_Adjusted", "Abs_Error", "Correct",
    ]].rename(columns={
        "RoundNumber": "Rd", "Opposition_Team": "Opponent", "Margin": "Actual",
        "Predicted_Margin_Adjusted": "Predicted", "Abs_Error": "Error",
    })
    pred_disp["Correct"] = pred_disp["Correct"].map({True: "Correct", False: "Missed"})

    st.dataframe(
        pred_disp, use_container_width=True, hide_index=True, height=460,
        column_config={
            "Actual": st.column_config.NumberColumn(format="%+d"),
            "Predicted": st.column_config.NumberColumn(format="%+.1f"),
            "Error": st.column_config.NumberColumn(format="%.1f"),
        },
    )


# ========================================================================
# PAGE: METHODOLOGY
# ========================================================================

elif page == "Methodology":
    st.markdown('<div class="bl-eyebrow">Methodology</div>', unsafe_allow_html=True)
    st.title("How this is actually built")
    st.markdown(
        '<p class="bl-lede">Three things sit behind the site: a data pipeline, a player ranking composite, '
        "and a margin-prediction model. This page explains each in plain terms — replace the specifics below "
        "with your own write-up as the model evolves.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("""
### 1. The data pipeline

Match results, player box scores, fixtures, coaches' votes, and player rankings are pulled from round-by-round
exports going back to 2012. This app reads those CSVs directly and caches the aggregations in memory — to
update the data after a new round, just overwrite the CSVs in the `data/` folder and reload the app; nothing
else needs to change.

The box-score data covers the usual disposal counts (kicks, handballs, marks) as well as more granular touches
— contested vs uncontested possessions, score involvements, intercepts, metres gained, and both AFL Fantasy and
SuperCoach points — which is what feeds the leaderboards on the **Player Performance** page.

### 2. The player ranking composite

Rather than rank players by a single stat, each player gets a `composite_score` calculated after every round,
normalised between 0 and 1 within that round. Overall rank, position rank, and club rank are all derived from
the same underlying score.

Two details worth knowing if you're digging into the numbers on the **Player Performance** page:

- **It's season-to-date, not single-game.** A player's rank reflects their form across the whole season up to
  that round, which is why rankings settle down (fewer ties) as the season progresses and small sample sizes
  wash out.
- **Missed games are handled explicitly.** An `absence_multiplier` and `missed_games_balance` adjust for
  players who've missed time, and a `low_confidence` flag marks rounds where the ranking is based on too
  little data to be reliable — early-season rankings should be read with that in mind.

### 3. The margin prediction model

The headline model on the **Model Predictions** page is a gradient-boosted regression (XGBoost) trained to
predict the final margin of a game — not just the winner. Inputs include team form, head-to-head history,
home ground advantage, interstate travel, and the betting market's own implied margin via team odds.

Because it predicts a continuous margin rather than a simple win/loss flag, the model gets graded two ways:

- **Win/loss accuracy** — did the sign of the predicted margin match the actual result? This is the simpler,
  more intuitive number.
- **Mean absolute error (MAE)** — on average, how many points off was the predicted margin from the actual
  one? This rewards calibration, not just picking winners.

Both are tracked season by season on the predictions page, with every individual prediction available in the
explorer table — including the misses. A model that's only shown when it's right isn't telling you anything
useful.

### What this page doesn't claim

This is a personal project, not a betting service or financial advice. The accuracy figures shown are
historical and don't guarantee future performance — AFL has enough randomness (injuries, weather, a
contentious free kick) that no model gets close to perfect, and that's expected rather than a flaw to fix away.

> If you've got questions about a specific modelling choice, ask it on the **Blog / Q&A** page — happy to dig
> into the details there.
""")


# ========================================================================
# PAGE: BLOG / Q&A
# ========================================================================

elif page == "Blog / Q&A":
    st.markdown('<div class="bl-eyebrow">04 / Blog &amp; Q&amp;A</div>', unsafe_allow_html=True)
    st.title("Notes on building this")
    st.markdown(
        '<p class="bl-lede">Write-ups on modelling decisions, data quirks, and answers to questions readers '
        "send in. The posts below are placeholders — swap them for your own as you publish.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    main_col, side_col = st.columns([2, 1])

    posts = [
        {
            "tag": "Modelling",
            "date": "Placeholder",
            "title": "Why I score the model on margin error, not just win/loss",
            "excerpt": "Picking winners is the easy headline number, but it hides how confident — or how "
                       "wrong — a prediction really was. Here's why mean absolute error matters just as much.",
        },
        {
            "tag": "Data pipeline",
            "date": "Placeholder",
            "title": "How the weekly data refresh actually works",
            "excerpt": "A walkthrough of the CSV-in, cached-aggregation-out pattern that keeps this app up "
                       "to date without a database.",
        },
        {
            "tag": "Q&A",
            "date": "Placeholder",
            "title": '"Why is my favourite player ranked so low?"',
            "excerpt": "A reader question about the composite ranking system, and what it does (and doesn't) "
                       "reward.",
        },
    ]

    with main_col:
        for p in posts:
            st.markdown(f"""
            <div style="padding: 1.1rem 0; border-bottom: 1px solid #E3E1D9;">
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:#707B85; text-transform:uppercase; letter-spacing:0.04em;">
                    {p['tag']} &middot; {p['date']}
                </div>
                <h3 style="margin: 0.3rem 0;">{p['title']}</h3>
                <p style="color:#3A3F45; margin:0;">{p['excerpt']}</p>
            </div>
            """, unsafe_allow_html=True)

    with side_col:
        st.markdown("""
        <div class="bl-card" style="margin-bottom: 1rem;">
        <h4>Got a question?</h4>
        <p>Ask anything about the model, the data, or a specific prediction — answers get added here as Q&amp;A posts.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="bl-card">
        <h4>Topics</h4>
        <p>Modelling &middot; Data pipeline &middot; Q&amp;A &middot; Season review</p>
        </div>
        """, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------

st.divider()
st.caption("Boundary Line — a personal AFL analytics project. Data updated after each round.")
