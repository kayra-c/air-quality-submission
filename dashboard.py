from pathlib import Path
import zipfile
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(
    page_title="Dashboard Kualitas Udara (2013-2017)",
    page_icon="🌫️",
    layout="wide"
)

sns.set_theme(style="whitegrid")

# Sesuai nama file ZIP di repository GitHub: main_data.zip
DATA_PATH = Path(__file__).parent / "main_data.zip"


def _read_csv_with_fallback(file_obj):
    for enc in ("utf-8", "utf-8-sig", "latin1", "cp1252"):
        try:
            file_obj.seek(0)
            return pd.read_csv(file_obj, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Gagal membaca file CSV di dalam main_data.zip dengan encoding yang didukung.")


@st.cache_data
def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"File data tidak ditemukan: {DATA_PATH}")

    with zipfile.ZipFile(DATA_PATH, "r") as zf:
        csv_files = [
            name for name in zf.namelist()
            if name.lower().endswith(".csv") and not name.startswith("__MACOSX")
        ]
        if not csv_files:
            raise FileNotFoundError("Tidak ditemukan file .csv di dalam main_data.zip.")

        with zf.open(csv_files[0], "r") as f:
            df = _read_csv_with_fallback(f)

    df["datetime"] = pd.to_datetime(df["datetime"])

    if "year" not in df.columns:
        df["year"] = df["datetime"].dt.year
    if "month" not in df.columns:
        df["month"] = df["datetime"].dt.month
    if "hour" not in df.columns:
        df["hour"] = df["datetime"].dt.hour

    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Gagal memuat dataset: {e}")
    st.stop()

st.title("🌫️ Dashboard Analisis Kualitas Udara (2013–2017)")
st.markdown(
    "Dashboard interaktif untuk mengeksplorasi pola polusi udara (**PM2.5** dan **PM10**) "
    "berdasarkan stasiun pemantauan, tahun, bulan, dan jam."
)

# Sidebar filter
st.sidebar.header("Filter Data")

stations = sorted(df["station"].dropna().unique().tolist())
selected_stations = st.sidebar.multiselect(
    "Pilih Stasiun",
    options=stations,
    default=stations
)

min_date = df["datetime"].min().date()
max_date = df["datetime"].max().date()
date_range = st.sidebar.date_input(
    "Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range if not isinstance(date_range, tuple) else date_range[0]

pollutant_options = [col for col in ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"] if col in df.columns]
if not pollutant_options:
    st.error("Kolom polutan yang didukung (PM2.5, PM10, SO2, NO2, CO, O3) tidak ditemukan pada dataset.")
    st.stop()

pollutant = st.sidebar.selectbox(
    "Pilih Polutan Utama",
    options=pollutant_options,
    index=0
)

if not selected_stations:
    st.warning("Silakan pilih minimal satu stasiun di sidebar.")
    st.stop()

mask = (
    df["station"].isin(selected_stations)
    & (df["datetime"].dt.date >= start_date)
    & (df["datetime"].dt.date <= end_date)
)
filtered_df = df.loc[mask].copy()

if filtered_df.empty:
    st.warning("Tidak ada data yang sesuai dengan filter yang dipilih.")
    st.stop()

# Metrik ringkasan
col1, col2, col3, col4 = st.columns(4)
col1.metric("Jumlah Baris Data", f"{len(filtered_df):,}")
col2.metric(f"Rata-rata {pollutant}", f"{filtered_df[pollutant].mean():.2f}")
col3.metric(f"Median {pollutant}", f"{filtered_df[pollutant].median():.2f}")
col4.metric(f"Maksimum {pollutant}", f"{filtered_df[pollutant].max():.2f}")

st.divider()

# Visualisasi
tab1, tab2, tab3 = st.tabs([
    "📍 Perbandingan Stasiun",
    "📅 Pola Bulanan",
    "🕒 Pola Per Jam"
])

with tab1:
    st.subheader(f"Rata-rata {pollutant} per Stasiun")
    station_avg = (
        filtered_df.groupby("station", as_index=False)[pollutant]
        .mean()
        .sort_values(pollutant, ascending=False)
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=station_avg, x=pollutant, y="station", ax=ax, palette="viridis")
    ax.set_title(f"Rata-rata {pollutant} Berdasarkan Stasiun")
    ax.set_xlabel(pollutant)
    ax.set_ylabel("Stasiun")
    st.pyplot(fig)
    plt.close(fig)

with tab2:
    st.subheader(f"Tren Bulanan {pollutant}")
    monthly_avg = filtered_df.groupby("month", as_index=False)[pollutant].mean()
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=monthly_avg, x="month", y=pollutant, marker="o", ax=ax)
    ax.set_xticks(range(1, 13))
    ax.set_title(f"Rata-rata {pollutant} per Bulan")
    ax.set_xlabel("Bulan")
    ax.set_ylabel(pollutant)
    st.pyplot(fig)
    plt.close(fig)

with tab3:
    st.subheader(f"Pola Harian (Per Jam) {pollutant}")
    hourly_avg = filtered_df.groupby("hour", as_index=False)[pollutant].mean()
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=hourly_avg, x="hour", y=pollutant, marker="o", ax=ax)
    ax.set_xticks(range(0, 24))
    ax.set_title(f"Rata-rata {pollutant} per Jam")
    ax.set_xlabel("Jam (0–23)")
    ax.set_ylabel(pollutant)
    st.pyplot(fig)
    plt.close(fig)
