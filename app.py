"""
Boundary Line — AFL Analytics
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

h1, h2, h3 { font-family: 'Fraunces', Georgia, serif !important; font-weight: 600 !important; letter-spacing: -0.01em; }

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
.bl-card p  { margin: 0; color: #3A3F45; font-size: 0.92rem; }

.movement-up   { color: #1F6F50; font-weight: 600; }
.movement-down { color: #B3492C; font-weight: 600; }
.movement-flat { color: #707B85; }
</style>
""", unsafe_allow_html=True)

GREEN   = "#1F6F50"
CLAY    = "#B3492C"
GOLD    = "#B68A2E"
SLATE   = "#707B85"
INK     = "#14171A"
PAPER   = "#FFFFFF"
HAIRLINE= "#E3E1D9"

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
    st.markdown("### 🏉 Boundary Line")
    st.caption("AFL Analytics — a personal project")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["Home", "Team Performance", "Player Performance",
         "Ladder Projection", "Model Predictions", "Methodology", "Blog / Q&A"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    meta = dl.get_meta()
    st.caption(f"Data through **{meta['latest_season']}, Round {meta['latest_round']}**")
    st.caption(f"{meta['teams_tracked']} clubs · {meta['players_tracked']:,} players tracked")


# ========================================================================
# HOME
# ========================================================================

if page == "Home":
    col1, col2 = st.columns([1.4, 1])
    with col1:
        st.markdown('<div class="bl-eyebrow">A personal AFL analytics project</div>', unsafe_allow_html=True)
        st.title("Footy, measured.")
        st.markdown(
            '<p class="bl-lede">Fourteen seasons of AFL results, player box scores, a ladder projection '
            "model, and a win-probability + margin model, all graded in public.</p>",
            unsafe_allow_html=True,
        )
    with col2:
        acc = meta["model_accuracy_pct"]
        acc_label = f"{acc}%" if acc else "—"
        st.metric("Model win/loss accuracy, all-time", acc_label,
                  help=f"{meta['model_games_scored']:,} games scored")
        st.metric("Latest data", f"{meta['latest_season']} · Round {meta['latest_round']}")

    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    seasons = dl.get_all_seasons()
    c1.metric("Seasons covered", f"{seasons[-1]}–{seasons[0]}")
    if meta["model_mae"]:
        c2.metric("Model MAE (OLS margin)", f"{meta['model_mae']:.1f} pts")
    c3.metric("Predictions graded", f"{meta['model_games_scored']:,}")
    c4.metric("Clubs tracked", meta["teams_tracked"])

    st.divider()
    st.subheader("Explore the data")

    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        st.markdown("""<div class="bl-card">
        <span style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:#707B85;">01 / Team Performance</span>
        <h4>Club form, season by season</h4>
        <p>Wins, margins, percentage and trends for all 18 clubs back to 2012.</p>
        </div>""", unsafe_allow_html=True)
    with r1c2:
        st.markdown("""<div class="bl-card">
        <span style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:#707B85;">02 / Player Performance</span>
        <h4>Season-long player rankings</h4>
        <p>Composite ranking model + raw stat leaderboards for every player.</p>
        </div>""", unsafe_allow_html=True)
    with r1c3:
        st.markdown("""<div class="bl-card">
        <span style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:#707B85;">03 / Ladder Projection</span>
        <h4>Where every club is likely to finish</h4>
        <p>Projected final ladder position with best/worst case range per club.</p>
        </div>""", unsafe_allow_html=True)

    st.write("")
    r2c1, r2c2, _ = st.columns(3)
    with r2c1:
        st.markdown("""<div class="bl-card">
        <span style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:#707B85;">04 / Model Predictions</span>
        <h4>Grading the model, in public</h4>
        <p>Win probability (LOGIT) and margin (OLS) — every prediction scored, wins and misses both shown.</p>
        </div>""", unsafe_allow_html=True)
    with r2c2:
        st.markdown("""<div class="bl-card">
        <span style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:#707B85;">05 / Methodology</span>
        <h4>How this is actually built</h4>
        <p>The data pipeline, player ranking composite, and prediction models explained in plain terms.</p>
        </div>""", unsafe_allow_html=True)


# ========================================================================
# TEAM PERFORMANCE
# ========================================================================

elif page == "Team Performance":
    st.markdown('<div class="bl-eyebrow">01 / Team Performance</div>', unsafe_allow_html=True)
    st.title("Club form, season by season")
    st.markdown('<p class="bl-lede">Every club\'s results since 2012 — wins, margins, percentage, '
                'and trends. Pick a season to compare clubs, or select a club to see its full game log.</p>',
                unsafe_allow_html=True)
    st.divider()

    seasons = dl.get_all_seasons()
    summary = dl.get_team_season_summary()

    season_sel = st.selectbox("Season", seasons, index=0)
    season_rows = summary[summary["Season"] == season_sel].sort_values("Win_Pct", ascending=False)

    st.dataframe(
        season_rows[["Team","Played","Wins","Losses","Draws","Win_Pct",
                     "Points_For","Points_Against","Percentage","Avg_Margin"]
        ].rename(columns={"Win_Pct":"Win %","Points_For":"PF",
                           "Points_Against":"PA","Avg_Margin":"Avg Margin"}),
        use_container_width=True, hide_index=True, height=460,
        column_config={
            "Win %":      st.column_config.NumberColumn(format="%.1f%%"),
            "Avg Margin": st.column_config.NumberColumn(format="%+.1f"),
            "Pct":        st.column_config.NumberColumn(format="%.1f"),
        },
    )

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
    st.title("Who's actually playing well")
    st.markdown('<p class="bl-lede">A composite ranking model scores every player after each round. '
                'Raw leaderboards for box-score stats sit underneath.</p>', unsafe_allow_html=True)
    st.divider()

    latest, latest_season, latest_round = dl.get_latest_rankings()

    st.subheader("Composite ranking — current round")
    st.caption(f"Season {latest_season}, Round {latest_round} · {len(latest)} players ranked")
    st.markdown("Rank is season-to-date, recalculated every round. Composite score normalised 0–1 within the round. "
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
# LADDER PROJECTION
# ========================================================================

elif page == "Ladder Projection":
    st.markdown('<div class="bl-eyebrow">03 / Ladder Projection</div>', unsafe_allow_html=True)
    st.title("Where every club is likely to finish")
    st.markdown(
        '<p class="bl-lede">Projected final ladder position for all 18 clubs, based on current standings '
        "and simulated remaining games. The range shows best-case and worst-case finishing positions "
        "from the simulation runs.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    ladder = dl.get_ladder_projection()
    if ladder is None:
        st.info("Ladder projection data not found — add `Ladder_Projection.csv` to the `data/` folder.")
        st.stop()

    meta = dl.get_meta()
    c1, c2, c3 = st.columns(3)
    c1.metric("Current round",       f"{meta['latest_season']} R{meta['latest_round']}")
    c2.metric("Games remaining",      int(ladder["Games_Remaining"].iloc[0]) if not ladder.empty else "—")
    c3.metric("Clubs in finals range","10")  # top 8

    st.divider()

    # --- range chart ---
    st.subheader("Projected finish — range chart")
    st.caption("Bar = projected median rank. Error bars show best/worst case from simulation.")

    df_chart = ladder.sort_values("Projected_Rank_Median")

    fig = go.Figure()

    # range bars (worst → best, plotted as low-opacity filled region via error bars)
    fig.add_trace(go.Scatter(
        x=df_chart["Team"],
        y=df_chart["Projected_Rank_Median"],
        error_y=dict(
            type="data",
            symmetric=False,
            array=(df_chart["Rank_Range_Worst"] - df_chart["Projected_Rank_Median"]).clip(lower=0),
            arrayminus=(df_chart["Projected_Rank_Median"] - df_chart["Rank_Range_Best"]).clip(lower=0),
            color=SLATE,
            thickness=4,
            width=8,
        ),
        mode="markers",
        marker=dict(
            size=12,
            color=[GREEN if r <= 10 else SLATE for r in df_chart["Projected_Rank_Median"]],
            symbol="diamond",
        ),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Projected: %{y:.0f}<br>"
            "Best case: %{customdata[0]}<br>"
            "Worst case: %{customdata[1]}<extra></extra>"
        ),
        customdata=df_chart[["Rank_Range_Best","Rank_Range_Worst"]].values,
        name="Projected rank",
    ))

    # finals cut line
    fig.add_hline(y=10.5, line_dash="dot", line_color=CLAY, line_width=1.5,
                  annotation_text="Finals cut", annotation_position="top right",
                  annotation_font_color=CLAY)

    layout_no_yaxis = {k:v for k,v in PLOTLY_BASE.items() if k != "yaxis"}
    fig.update_layout(
        **layout_no_yaxis,
        height=420,
        xaxis_title=None,
        yaxis=dict(**PLOTLY_BASE["yaxis"], autorange="reversed", title="Ladder position",
                   tickvals=list(range(1,19))),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- detailed table ---
    st.subheader("Full projection table")

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
    display["In Finals?"] = display["Projected_Rank_Median"].apply(
        lambda r: "✅ Yes" if r <= 10 else "⬜ No"
    )

    show_cols = {
        "Team": "Club",
        "Current_Rank": "Current Rank",
        "Movement": "Movement",
        "Played": "Played",
        "Wins": "W",
        "Draws": "D",
        "Losses": "L",
        "Current_Points": "Points",
        "Current_Percentage": "Pct",
        "Games_Remaining": "Remaining",
        "Projected_Rank_Median": "Proj. Rank",
        "Proj. Range": "Range (Best–Worst)",
        "In Finals?": "Finals?",
    }

    st.dataframe(
        display[list(show_cols.keys())].rename(columns=show_cols),
        use_container_width=True, hide_index=True,
        column_config={
            "Current Rank":   st.column_config.NumberColumn(format="%d"),
            "Proj. Rank":     st.column_config.NumberColumn(format="%.1f"),
            "Pct":            st.column_config.NumberColumn(format="%.2f"),
        },
        height=560,
    )

    st.divider()

    # --- top 10 probability callout ---
    st.subheader("Finals picture")
    top10 = ladder[ladder["Projected_Rank_Median"] <= 10].sort_values("Projected_Rank_Median")
    bubble = ladder[(ladder["Rank_Range_Best"] <= 10) & (ladder["Projected_Rank_Median"] > 10)].sort_values("Projected_Rank_Median")

    col_top, col_bub = st.columns(2)
    with col_top:
        st.markdown("**Projected top 10**")
        for _, row in top10.iterrows():
            st.markdown(
                f"**{int(row['Projected_Rank_Median'])}.** {row['Team']} "
                f"<span style='color:{SLATE};font-size:0.85rem;'>({int(row['Rank_Range_Best'])}–{int(row['Rank_Range_Worst'])})</span>",
                unsafe_allow_html=True,
            )
    with col_bub:
        if not bubble.empty:
            st.markdown("**On the bubble** *(best case makes finals)*")
            for _, row in bubble.iterrows():
                st.markdown(
                    f"**{row['Team']}** — proj. {int(row['Projected_Rank_Median'])}, "
                    f"<span style='color:{SLATE};font-size:0.85rem;'>best case {int(row['Rank_Range_Best'])}</span>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown("**On the bubble**")
            st.caption("No clubs outside the projected top 10 have a best-case finals finish.")


# ========================================================================
# MODEL PREDICTIONS
# ========================================================================

elif page == "Model Predictions":
    st.markdown('<div class="bl-eyebrow">04 / Model Predictions</div>', unsafe_allow_html=True)
    st.title("Grading the model, in public")

    predictions = dl.get_predictions()
    by_season, overall = dl.get_prediction_summary()
    fmt = overall.get("fmt","old")

    if fmt == "new":
        st.markdown(
            '<p class="bl-lede">Two models run on every game: a <strong>LOGIT</strong> classifier for '
            "win/loss probability, and an <strong>OLS</strong> regression for predicted margin. "
            "Both are graded below — wins and misses included.</p>",
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

        st.subheader("Accuracy by season — both models")

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

        season_disp = by_season.rename(columns={
            "Games":"Games","Correct_LOGIT":"LOGIT Correct","Accuracy_LOGIT":"LOGIT Acc.",
            "Accuracy_OLS":"OLS Acc.","MAE_OLS":"OLS MAE",
        }).sort_values("Season", ascending=False)
        st.dataframe(season_disp, use_container_width=True, hide_index=True,
                     column_config={
                         "LOGIT Acc.": st.column_config.NumberColumn(format="%.1f%%"),
                         "OLS Acc.":   st.column_config.NumberColumn(format="%.1f%%"),
                         "OLS MAE":    st.column_config.NumberColumn(format="%.1f pts"),
                     })

        # Feature importance section
        imp_cols_present = [c for c in dl.IMPORTANCE_COLS if c in predictions.columns]
        if imp_cols_present:
            st.divider()
            st.subheader("What's driving the OLS predictions?")
            st.caption("Average feature group importance across all scored games (team perspective)")

            scored = dl.get_completed_predictions()            
            imp_means = scored[imp_cols_present].mean()
            imp_labels = [dl.IMPORTANCE_LABELS.get(c, c) for c in imp_cols_present]

            fig_imp = go.Figure(go.Bar(
                x=imp_means.values,
                y=imp_labels,
                orientation="h",
                marker_color=GREEN,
                hovertemplate="%{y}: %{x:,.1f}<extra></extra>",
            ))
            layout_no_yaxis = {
                k: v
                for k, v in PLOTLY_BASE.items()
                if k != "yaxis"
            }

            fig_imp.update_layout(
                **layout_no_yaxis,
                height=320,
                xaxis_title="Average importance (sum of marginal contributions)",
                yaxis=dict(
                    **PLOTLY_BASE["yaxis"],
                    autorange="reversed"
                )
            )
            st.plotly_chart(fig_imp, use_container_width=True)

    else:
        # Old single-model format
        st.markdown(
            '<p class="bl-lede">An XGBoost model predicts the margin of every game. '
            "Graded on win/loss accuracy and margin error, season by season.</p>",
            unsafe_allow_html=True,
        )
        st.divider()

        oc1, oc2 = st.columns(2)
        correct_count = overall.get("correct", overall.get("games", 0))
        oc1.metric("Win/loss accuracy, all-time", f"{overall['accuracy_pct']}%",
                   help=f"{correct_count:,} of {overall['games']:,} games correct")
        oc2.metric("Mean abs. margin error",      f"{overall['mae']:.1f} pts")

        st.subheader("Accuracy by season")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=by_season["Season"], y=by_season["Accuracy_Pct"],
                                 name="Win/loss accuracy", mode="lines+markers",
                                 line=dict(color=GREEN, width=2.5), marker=dict(size=7)))
        fig.add_trace(go.Scatter(x=by_season["Season"], y=by_season["MAE"],
                                 name="MAE", mode="lines+markers",
                                 line=dict(color=CLAY, width=2, dash="dot"), marker=dict(size=6),
                                 yaxis="y2"))
        layout_no_yaxis = {k:v for k,v in PLOTLY_BASE.items() if k not in ("yaxis",)}
        fig.update_layout(**layout_no_yaxis, height=360,
                          yaxis=dict(title="Accuracy (%)", gridcolor=HAIRLINE, zeroline=False),
                          yaxis2=dict(title="MAE (pts)", overlaying="y", side="right", showgrid=False),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(by_season.rename(columns={"Accuracy_Pct":"Accuracy","MAE":"Mean Abs Error"})
                     .sort_values("Season", ascending=False),
                     use_container_width=True, hide_index=True,
                     column_config={
                         "Accuracy":       st.column_config.NumberColumn(format="%.1f%%"),
                         "Mean Abs Error": st.column_config.NumberColumn(format="%.1f pts"),
                     })

    # --- upcoming fixture (both formats) ---
    st.divider()
    st.subheader("Upcoming fixture")
    st.caption("Predictions populate once the round is complete")
    upcoming = dl.get_upcoming_fixture()
    if upcoming.empty:
        st.info("No upcoming fixture in the current export.")
    else:
        up_cols = ["Date","Round","HomeTeam","AwayTeam","Venue"]
        up_cols = [c for c in up_cols if c in upcoming.columns]
        st.dataframe(upcoming[up_cols].rename(columns={"HomeTeam":"Home","AwayTeam":"Away"}).head(12),
                     use_container_width=True, hide_index=True)

    # --- game explorer (both formats) ---
    st.divider()
    st.subheader("Every prediction")

    scored_games = dl.get_predictions()    
    st.caption(f"{len(scored_games):,} scored predictions")

    fc1, fc2, fc3, fc4 = st.columns(4)

    with fc1:
        all_seasons = ["All seasons"] + sorted(scored_games["Season"].unique().tolist(), reverse=True)
        s_filter = st.selectbox("Season", all_seasons, key="pred_season")

    with fc2:
        all_teams = ["All teams"] + sorted(scored_games["Team"].dropna().unique().tolist())
        t_filter = st.selectbox("Team", all_teams, key="pred_team")

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

    if s_filter != "All seasons": pg = pg[pg["Season"] == s_filter]
    if t_filter != "All teams":   pg = pg[pg["Team"] == t_filter]
    if r_filter != "All rounds":  pg = pg[pg["RoundNumber"] == r_filter]
    if fmt == "new":
        if o_filter == "LOGIT correct":    pg = pg[pg["Correct_LOGIT"]]
        elif o_filter == "LOGIT incorrect": pg = pg[~pg["Correct_LOGIT"]]
        elif o_filter == "OLS correct":    pg = pg[pg["Correct_OLS"]]
        elif o_filter == "OLS incorrect":  pg = pg[~pg["Correct_OLS"]]
    else:
        if o_filter == "Correct only":    pg = pg[pg["Correct"]]
        elif o_filter == "Incorrect only": pg = pg[~pg["Correct"]]

    pg = pg.sort_values("Date", ascending=False)

    if fmt == "new":
        disp_cols = {
            "Date_str":"Date","Season":"Season","RoundNumber":"Rd","Team":"Team",
            "Opposition_Team":"Opponent","Margin":"Actual",
            "Predicted_Margin_OLS":"Pred Margin","Abs_Error_OLS":"Margin Err",
            "Predicted_Prob_LOGIT":"LOGIT Prob",
            "Correct_LOGIT":"LOGIT ✓","Correct_OLS":"OLS ✓",
        }
    else:
        disp_cols = {
            "Date_str":"Date","Season":"Season","RoundNumber":"Rd","Team":"Team",
            "Opposition_Team":"Opponent","Margin":"Actual",
            "Predicted_Margin_Adjusted":"Predicted","Abs_Error":"Error","Correct":"Correct",
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
    for c in ["Actual","Predicted","Pred Margin"]:
        if c in pg_disp.columns:
            col_cfg[c] = st.column_config.NumberColumn(format="%+d")
    for c in ["Error","Margin Err"]:
        if c in pg_disp.columns:
            col_cfg[c] = st.column_config.NumberColumn(format="%.1f")
    if "LOGIT Prob" in pg_disp.columns:
        col_cfg["LOGIT Prob"] = st.column_config.NumberColumn(format="%.3f")

    st.dataframe(pg_disp, use_container_width=True, hide_index=True, height=460,
                 column_config=col_cfg)


# ========================================================================
# METHODOLOGY
# ========================================================================

elif page == "Methodology":
    st.markdown('<div class="bl-eyebrow">Methodology</div>', unsafe_allow_html=True)
    st.title("How this is actually built")
    st.markdown(
        '<p class="bl-lede">Four things sit behind the site: a data pipeline, a player ranking composite, '
        "a ladder projection model, and win-probability + margin prediction models.</p>",
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("""
### 1. The data pipeline

Match results, player box scores, fixtures, coaches' votes, and player rankings are pulled from round-by-round
exports going back to 2012. This app reads those CSVs directly and caches the aggregations in memory — to
update the data after a new round, just overwrite the CSVs in the `data/` folder and reload the app.

### 2. The player ranking composite

Each player gets a `composite_score` calculated after every round, normalised 0–1 within that round. Overall
rank, position rank, and club rank are all derived from the same score. It's season-to-date — rankings settle
as the season progresses and early small-sample ties wash out.

### 3. The ladder projection model

The ladder projection simulates the remaining games of the season to produce a projected finishing rank for
each club, along with a best-case and worst-case range across simulation runs. Updated each round when the
new `Ladder_Projection.csv` export is dropped in.

### 4. The prediction models

Two models run on every game:

- **LOGIT** — a logistic regression that outputs a win probability (0–1). Graded on whether the predicted
  winner matched the actual result.
- **OLS (margin regression)** — a linear model predicting the final margin. Graded both on win/loss
  accuracy (sign of predicted margin) and mean absolute error (how many points off the prediction was).

Feature importances for the OLS model are decomposed into seven groups: External Factors, In-Game Tempo,
Midfield Control, Offensive Output, Player Ranking, Ruck & Ball Movement, and Team Defense — visible in the
Predictions page for any game where the model has scored it.

> Questions about a specific modelling decision? Ask on the **Blog / Q&A** page.
""")


# ========================================================================
# BLOG / Q&A
# ========================================================================

elif page == "Blog / Q&A":
    st.markdown('<div class="bl-eyebrow">05 / Blog &amp; Q&amp;A</div>', unsafe_allow_html=True)
    st.title("Notes on building this")
    st.markdown(
        '<p class="bl-lede">Write-ups on modelling decisions, data quirks, and reader Q&A. '
        "Posts below are placeholders — swap them for your own as you publish.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    main_col, side_col = st.columns([2, 1])
    posts = [
        {"tag":"Modelling","date":"Placeholder",
         "title":"Why I score the model on margin error, not just win/loss",
         "excerpt":"Picking winners is the easy headline. Here's why MAE matters just as much."},
        {"tag":"Modelling","date":"Placeholder",
         "title":"LOGIT vs OLS — why run two models on the same game?",
         "excerpt":"Each optimises for a different thing. Here's what you learn from comparing them."},
        {"tag":"Data pipeline","date":"Placeholder",
         "title":"How the weekly data refresh actually works",
         "excerpt":"A walkthrough of the CSV-in, cached-aggregation-out pattern."},
        {"tag":"Q&A","date":"Placeholder",
         "title":'"Why is my favourite player ranked so low?"',
         "excerpt":"A reader question about the composite ranking system and what it does (and doesn't) reward."},
    ]

    with main_col:
        for p in posts:
            st.markdown(f"""
            <div style="padding:1.1rem 0;border-bottom:1px solid #E3E1D9;">
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.74rem;color:#707B85;text-transform:uppercase;letter-spacing:0.04em;">
                    {p['tag']} &middot; {p['date']}
                </div>
                <h3 style="margin:0.3rem 0;">{p['title']}</h3>
                <p style="color:#3A3F45;margin:0;">{p['excerpt']}</p>
            </div>
            """, unsafe_allow_html=True)

    with side_col:
        st.markdown("""<div class="bl-card" style="margin-bottom:1rem;">
        <h4>Got a question?</h4>
        <p>Ask anything about the model, the data, or a specific prediction — answers get added here.</p>
        </div>""", unsafe_allow_html=True)

st.divider()
st.caption("Boundary Line — a personal AFL analytics project. Data updated after each round.")
