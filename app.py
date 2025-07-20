import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi halaman HARUS berada sebelum komponen Streamlit lainnya
st.set_page_config(page_title="Spotify Dashboard", layout="wide")

# Load dan siapkan data
@st.cache_data
def load_data():
    df = pd.read_csv("Data_Spotify.csv")
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['release_year'] = df['release_date'].dt.year
    df['release_month'] = df['release_date'].dt.month_name()
    df['duration_min'] = df['duration_ms'] / 60000
    df['estimated_streams'] = df['track_score'] * 100000
    df.dropna(subset=['release_year', 'release_month'], inplace=True)
    return df

df = load_data()

# Styling
st.markdown("""
    <style>
    /* Ganti latar belakang utama */
    .stApp {
        background-color: #F0F8FF !important;
    }

    /* Ganti warna sidebar */
    section[data-testid="stSidebar"] {
        background-color: #E0ECFF !important;
    }

    /* Ukuran heading sidebar biar tidak ikut kecil */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-size: 22px !important;
        font-weight: bold;
    }

    /* Ukuran elemen lain di sidebar tetap kecil */
    section[data-testid="stSidebar"] *:not(h1):not(h2):not(h3) {
        color: black !important;
        font-size: 14px !important;
    }

    .block-container { padding-top: 3rem; padding-left: 2rem; padding-right: 2rem; }

    html, body, div, p, span, label {
        font-size: 16px !important;
    }

    .block-container h1, .block-container h2, .block-container h3 {
        font-size: 40px !important;
    }

    h2, h3 {
        font-size: 32px !important;
    }

    div[data-testid="metric-container"] {
        font-size: 30px !important;
    }

    div[data-testid="metric-container"] > label {
        font-size: 24px !important;
    }

    div[data-testid="metric-container"] > div {
        font-size: 36px !important;
        font-weight: bold;
        color: #1DB954;
    }
</style>
""", unsafe_allow_html=True)

# Warna hijau custom ala Spotify
color_ijo = ["#b2f7ef", "#9fe2bf", "#77dd77", "#99edc3", "#00a86b", "#228b22", "#006400"]

# Header dengan logo Spotify
st.markdown("""
<div style='display: flex; align-items: center; gap: 10px; margin-bottom: 30px;'>
    <img src='https://upload.wikimedia.org/wikipedia/commons/8/84/Spotify_icon.svg' width='60'/>
    <h1 style='margin: 0; font-size: 65px; font-weight: bold;'>Spotify Music Dashboard</h1>
</div>
""", unsafe_allow_html=True)

# Sidebar Filter
with st.sidebar:
    st.markdown("### 🎛️ Filter Lagu")
    year_options = ['Semua'] + sorted(df['release_year'].dropna().unique().astype(int).tolist())
    selected_year = st.selectbox("Pilih Tahun Rilis", year_options)
    artists = st.multiselect("Pilih Artis", df['artist'].unique())
    genres = st.multiselect("Pilih Genre", df['genre'].unique())
    popularity_range = st.slider("Popularitas", 0, 100, (30, 100))

# Filter Data
filtered_df = df.copy()
if selected_year != 'Semua':
    filtered_df = filtered_df[filtered_df['release_year'] == int(selected_year)]
if artists:
    filtered_df = filtered_df[filtered_df['artist'].isin(artists)]
if genres:
    filtered_df = filtered_df[filtered_df['genre'].isin(genres)]
filtered_df = filtered_df[(filtered_df['popularity'] >= popularity_range[0]) & (filtered_df['popularity'] <= popularity_range[1])]

# Ringkasan
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Lagu", f"{len(filtered_df):,}")
col2.metric("Total Genre", f"{filtered_df['genre'].nunique():,}")
col3.metric("Total Artis", f"{filtered_df['artist'].nunique():,}")
col4.metric("Rata-Rata Popularitas", f"{filtered_df['popularity'].mean():.1f}" if not filtered_df.empty else "N/A")

st.markdown("---")

# TOP 10 Lagu Terpopuler
st.markdown("### 🎵 Top 10 Lagu Terpopuler")

top_tracks = (
    filtered_df
    .drop_duplicates(subset='track')
    .sort_values(by="popularity", ascending=False)
    .head(10)
    .sort_values(by="popularity", ascending=True)
)

fig_popular = px.bar(
    top_tracks,
    x="popularity",
    y="track",
    orientation="h",
    color="track",
    color_discrete_sequence=color_ijo
)

fig_popular.update_layout(
    yaxis=dict(title="Track", autorange="reversed"),
    xaxis=dict(title="Popularitas")
)

st.plotly_chart(fig_popular, use_container_width=True)

st.markdown("### 📈 Tren Jumlah Lagu Dirilis per Bulan")

fig_line = px.line(
    filtered_df.groupby("release_month")["track"].count()
    .reindex([
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]).dropna().reset_index(name="jumlah_lagu"),
    x="release_month",
    y="jumlah_lagu",
    markers=True,
    line_shape="spline",
    color_discrete_sequence=[color_ijo[3]]
)

st.plotly_chart(fig_line, use_container_width=True)

st.markdown("### 🎶 Genre dengan Jumlah Lagu Terbanyak")

genre_lagu = filtered_df.groupby("genre")["track"].count().nlargest(10).reset_index(name="jumlah_lagu")

fig_genre = px.bar(
    genre_lagu,
    x="genre",
    y="jumlah_lagu",
    color="genre",
    color_discrete_sequence=color_ijo
)

st.plotly_chart(fig_genre, use_container_width=True)


# Distribusi Durasi
st.markdown("### ⏱️ Distribusi Lagu Berdasarkan Durasi")

# Definisi fungsi kategori durasi HARUS didefinisikan sebelum dipakai
def kategori_durasi(ms):
    menit = ms / 60000
    if menit <= 2:
        return "Pendek (≤2m)"
    elif menit <= 4:
        return "Sedang (2–4m)"
    else:
        return "Panjang (>4m)"


filtered_df['durasi_kategori'] = filtered_df['duration_ms'].apply(kategori_durasi)

durasi_pie = filtered_df['durasi_kategori'].value_counts().reset_index()
durasi_pie.columns = ['durasi_kategori', 'jumlah_lagu']

# Pie chart
fig_pie = px.pie(
    durasi_pie,
    names='durasi_kategori',
    values='jumlah_lagu',
    color_discrete_sequence=color_ijo
)

st.plotly_chart(fig_pie, use_container_width=True)

#Top 10 Artis dengan Lagu Terbanyak
st.markdown("### 🌟 Top 10 Artis dengan Lagu Terbanyak")

top_artis = (
    filtered_df.groupby("artist")["track"]
    .count()
    .nlargest(10)
    .reset_index(name="jumlah_lagu")
    .sort_values(by="jumlah_lagu", ascending=True)
)

fig_top_stream = px.bar(
    top_artis,
    x="jumlah_lagu",
    y="artist",
    orientation="h",
    color="artist",
    color_discrete_sequence=color_ijo,
)

fig_top_stream.update_layout(
    yaxis=dict(title="Artis", autorange="reversed"),
    xaxis=dict(title="Jumlah Lagu")
)

st.plotly_chart(fig_top_stream, use_container_width=True)


# Tabel Data Lagu
st.markdown("### 📋 Tabel Data Lagu")

tabel_lengkap = (
    filtered_df[[ 
        "track", "album", "artist", "genre", "popularity", "explicit",
        "release_date", "duration_min", "track_score"
    ]]
    .sort_values(by="popularity", ascending=False)
)

st.dataframe(tabel_lengkap.reset_index(drop=True))

# Footer
st.markdown("---")
st.caption("By Dinda Maulidiyah ")
