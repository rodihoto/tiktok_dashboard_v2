
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="TikTok: Topp 10 kandidater", layout="wide")
st.title("TikTok – Topp 10 stortingskandidater (analyse)")
st.caption("Kilde: Brukerens tabell + NRK-sak (kontekst).")

@st.cache_data
def load_default():
    return pd.read_csv("data/candidates.csv")

uploaded = st.file_uploader("Last opp egen CSV (valgfritt). Må inneholde: Kandidat, Parti, Likerklikk, Kommentarer, Delinger, Visninger", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
else:
    df = load_default()

required = {"Kandidat","Parti","Likerklikk","Kommentarer","Delinger","Visninger"}
if not required.issubset(df.columns):
    st.error("CSV mangler nødvendige kolonner.")
    st.stop()

# derive metrics
df["Engasjement"] = df.get("Engasjement", df["Likerklikk"] + df["Kommentarer"] + df["Delinger"])
df["Engasjementsrate_%"] = (df["Engasjement"] / df["Visninger"] * 100).round(2)
df["Likes_per_1M_views"] = (df["Likerklikk"] / df["Visninger"] * 1_000_000).round(1)
df["Comments_per_1M_views"] = (df["Kommentarer"] / df["Visninger"] * 1_000_000).round(1)
df["Shares_per_1M_views"] = (df["Delinger"] / df["Visninger"] * 1_000_000).round(1)

with st.expander("Filtre", expanded=True):
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        partier = st.multiselect("Parti", sorted(df["Parti"].dropna().unique()), default=sorted(df["Parti"].dropna().unique()))
    with c2:
        log_y = st.checkbox("Log-skala for y-akse", value=False)
    with c3:
        søk = st.text_input("Søk kandidat", "")

mask = df["Parti"].isin(partier)
if søk:
    mask &= df["Kandidat"].astype(str).str.contains(søk, case=False, na=False)
fdf = df[mask].copy()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Sum visninger", f"{int(fdf['Visninger'].sum()):,}".replace(",", " "))
k2.metric("Sum likerklikk", f"{int(fdf['Likerklikk'].sum()):,}".replace(",", " "))
k3.metric("Sum kommentarer", f"{int(fdf['Kommentarer'].sum()):,}".replace(",", " "))
k4.metric("Sum delinger", f"{int(fdf['Delinger'].sum()):,}".replace(",", " "))
k5.metric("Total SUM", f"{int(fdf['SUM'].sum()):,}".replace(",", " ") if 'SUM' in fdf.columns else "—")

st.markdown("---")
left, right = st.columns(2)
with left:
    cols = ["Kandidat","Parti"] + [c for c in ["SUM","Visninger","Likerklikk","Kommentarer","Delinger"] if c in fdf.columns]
    ycol = "SUM" if "SUM" in fdf.columns else "Visninger"
    st.subheader(f"Rangering etter {ycol}")
    st.dataframe(fdf.sort_values(ycol, ascending=False)[cols].reset_index(drop=True))
with right:
    st.subheader("Engasjementsnøkler (per 1M visninger)")
    cols2 = ["Kandidat","Parti","Engasjementsrate_%","Likes_per_1M_views","Comments_per_1M_views","Shares_per_1M_views","Visninger"]
    st.dataframe(fdf.sort_values("Engasjementsrate_%", ascending=False)[cols2].reset_index(drop=True))

st.markdown("---")
c1, c2 = st.columns(2)
with c1:
    fig_sum = px.bar(fdf.sort_values(ycol, ascending=False), x="Kandidat", y=ycol, color="Parti", title=f"Total {ycol} per kandidat", log_y=log_y)
    st.plotly_chart(fig_sum, use_container_width=True)
with c2:
    fig_eng = px.bar(fdf.sort_values("Engasjementsrate_%", ascending=False), x="Kandidat", y="Engasjementsrate_%", color="Parti", title="Engasjementsrate (%) per kandidat")
    st.plotly_chart(fig_eng, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    party_agg = fdf.groupby("Parti", as_index=False)[["Visninger","Likerklikk","Kommentarer","Delinger"] + (["SUM"] if "SUM" in fdf.columns else [])].sum(numeric_only=True)
    p_ycol = "SUM" if "SUM" in party_agg.columns else "Visninger"
    fig_party = px.bar(party_agg.sort_values(p_ycol, ascending=False), x="Parti", y=p_ycol, title=f"{p_ycol} per parti", log_y=log_y)
    st.plotly_chart(fig_party, use_container_width=True)
with c4:
    fig_scatter = px.scatter(fdf, x="Visninger", y="Engasjementsrate_%", color="Parti",
                             hover_data=["Kandidat","Likerklikk","Kommentarer","Delinger"],
                             title="Visninger vs. Engasjementsrate")
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")
csv_bytes = fdf.to_csv(index=False).encode("utf-8")
st.download_button("Last ned filtrert data (CSV)", data=csv_bytes, file_name="filtered_candidates.csv", mime="text/csv")

st.markdown("### Datagrunnlag og beregninger")
st.write("Engasjement = Likerklikk + Kommentarer + Delinger. Engasjementsrate = Engasjement / Visninger. Normalisering per 1M visninger er inkludert.")
st.dataframe(fdf.reset_index(drop=True))
