import streamlit as st
import pandas as pd
import plotly.express as px

# Load Data
@st.cache_data
def load_data():
    df = pd.read_csv('Data Music Spotify.csv')
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['release_year'] = df['release_date'].dt.year
    df['release_month'] = df['release_date'].dt.month_name()
    df.dropna(subset=['release_year', 'release_month'], inplace=True)
    df['duration_min_sec'] = (df['duration_ms'] / 60000).round(2)
    return df

df = load_data()

# Page Styling
st.set_page_config(page_title="Spotify Dashboard", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #fff0f3;
    }
    .block-container {
        padding-top: 1rem;
    }
    .css-18e3th9 {
        background-color: #fff0f3;
    }
    .sidebar .sidebar-content, .sidebar .sidebar-content * {
        color: black !important;
    }
    .st-bb, .st-ef {
        color: black !important;
    }
    div[data-baseweb="select"] {
        background-color: #d9ffe8 !important;
        border-radius: 6px;
    }
    div[data-baseweb="select"] * {
        color: black !important;
    }
    div[role="radiogroup"] {
        background-color: #d9ffe8 !important;
        border-radius: 6px;
        padding: 10px;
    }
    div[role="radiogroup"] label {
        color: black !important;
    }
    .css-1d391kg, .css-1jqq78o {
        color: black !important;
    }
    svg {
        color: black !important;
    }
    .stSlider > div {
        background-color: #d9ffe8 !important;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# Warna Hijau Custom
color_ijo = ["#b2f7ef", "#9fe2bf", "#77dd77", "#99edc3", "#00a86b", "#228b22", "#006400"]

# Header
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style='display: flex; align-items: center; gap: 10px;'>
    <img src='https://upload.wikimedia.org/wikipedia/commons/8/84/Spotify_icon.svg' width='40'/>
    <h1 style='margin: 0;'>Spotify Songs Dashboard</h1>
</div>
""", unsafe_allow_html=True)

# Sidebar Filter
with st.sidebar:
    st.header("🎚️ Filters")
    year_options = ['Semua Tahun'] + sorted(df['release_year'].dropna().unique().astype(str).tolist())
    selected_year = st.radio("Tahun Rilis", year_options, index=0)
    artists = st.multiselect("Pilih Artis", df['artist'].unique())
    genres = st.multiselect("Pilih Genre", df['genre'].unique())
    popularity_range = st.slider("Popularitas", 0, 100, (30, 100))

# Filtering
filtered_df = df.copy()
if selected_year != 'Semua Tahun':
    filtered_df = filtered_df[filtered_df['release_year'] == int(selected_year)]
if artists:
    filtered_df = filtered_df[filtered_df['artist'].isin(artists)]
if genres:
    filtered_df = filtered_df[filtered_df['genre'].isin(genres)]
filtered_df = filtered_df[(filtered_df['popularity'] >= popularity_range[0]) & (filtered_df['popularity'] <= popularity_range[1])]

# Summary Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Lagu", f"{len(filtered_df):,}")
col2.metric("Jumlah Artis", f"{filtered_df['artist'].nunique():,}")
col3.metric("Total Genre", f"{filtered_df['genre'].nunique():,}")
col4.metric("Rata-Rata Popularitas", f"{filtered_df['popularity'].mean():.1f}" if not filtered_df.empty else "N/A")

st.markdown("---")

# Lagu Terpopuler
st.subheader("📌 Popularitas Lagu Tertinggi")
top_tracks = filtered_df.sort_values(by="popularity", ascending=False).head(10)
fig_tracks = px.bar(
    top_tracks,
    x="popularity",
    y="track",
    orientation='h',
    color="track",
    title="10 Lagu Terpopuler",
    color_discrete_sequence=color_ijo
)
fig_tracks.update_traces(
    customdata=top_tracks[['track']].values,
    hovertemplate="<b>%{y}</b><br>Popularity: %{x}"
)

st.plotly_chart(fig_tracks, use_container_width=True)

# Stream vs Bulan Rilis
st.subheader("📈 Stream vs Bulan Rilis")
month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
               'September', 'October', 'November', 'December']
stream_by_month = filtered_df.groupby("release_month")["estimated_spotify_streams"].sum().reindex(month_order).dropna().reset_index()
fig_line = px.line(
    stream_by_month,
    x="release_month",
    y="estimated_spotify_streams",
    title="Jumlah Stream per Bulan",
    markers=True,
    line_shape="spline",
    color_discrete_sequence=[color_ijo[2]]
)
st.plotly_chart(fig_line, use_container_width=True)

# Visualisasi Data: Genre Stream
st.subheader("🎵 Top Genre berdasarkan Stream")
genre_stream = filtered_df.groupby("genre")["estimated_spotify_streams"].sum().nlargest(10).reset_index()
genre_stream["scaled_streams"] = genre_stream["estimated_spotify_streams"] ** 0.5
genre_stream["tooltip"] = genre_stream.apply(
    lambda row: f"{row['genre']}<br>Stream Asli: {row['estimated_spotify_streams']:,}", axis=1
)
fig_genre = px.bar(
    genre_stream,
    x="genre",
    y="scaled_streams",
    color="genre",
    title="Genre Terpopuler",
    hover_name="tooltip",
    color_discrete_sequence=color_ijo 
)

fig_genre.update_traces(hovertemplate="%{hovertext}<extra></extra>")
st.plotly_chart(fig_genre, use_container_width=True)

# Distribusi Durasi
st.subheader("⏳ Distribusi Stream Berdasarkan Durasi Lagu")
def kategori_durasi(ms):
    menit = ms / 60000
    if menit <= 2:
        return "Pendek (<=2m)"
    elif menit <= 4:
        return "Sedang (2-4m)"
    else:
        return "Panjang (>4m)"

filtered_df['durasi_kategori'] = filtered_df['duration_ms'].apply(kategori_durasi)
stream_durasi = filtered_df.groupby("durasi_kategori")["estimated_spotify_streams"].sum().reset_index().sort_values(by="estimated_spotify_streams", ascending=False)
fig_durasi_pie = px.pie(
    stream_durasi,
    names='durasi_kategori',
    values='estimated_spotify_streams',
    title='Distribusi Jumlah Stream Berdasarkan Durasi Lagu',
    color_discrete_sequence=color_ijo
)
st.plotly_chart(fig_durasi_pie, use_container_width=True)

# Artis dengan Popularitas Tertinggi
st.subheader("🌟 Artis dengan Popularitas Tertinggi (Rata-rata)")

# Hitung rata-rata popularitas tiap artis
top_artists_popularity = filtered_df.groupby("artist")["popularity"].mean().nlargest(10).reset_index()

# Buat chart
fig_top_artists = px.bar(
    top_artists_popularity,
    x="popularity",
    y="artist",
    orientation='h',
    title="10 Artis dengan Rata-rata Popularitas Tertinggi",
    color="artist",
    color_discrete_sequence=color_ijo
)

fig_top_artists.update_traces(
    hovertemplate="<b>%{y}</b><br>Rata-rata Popularitas: %{x:.1f}"
)

st.plotly_chart(fig_top_artists, use_container_width=True)


# Tabel Lagu
st.markdown("#### 📄 Top 10 Lagu Teratas (Detail Lengkap)")
tabel_lengkap = top_tracks[
    ["track", "album", "artist", "genre", "popularity", "explicit",
     "release_date", "duration_ms", "duration_min_sec",
     "track_score", "estimated_spotify_streams"]
]
st.dataframe(tabel_lengkap.reset_index(drop=True))

st.markdown("---")
st.caption("By Dinda Maulidiyah")
