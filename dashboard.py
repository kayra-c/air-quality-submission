import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(
    page_title="Dashboard Kualitas Udara (2013–2017)",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "main_data.csv")


@st.cache_data
def load_data():
    last_error = None
    df = None

    for enc in ("utf-8", "utf-8-sig", "latin1", "cp1252"):
        try:
            df = pd.read_csv(DATA_PATH, encoding=enc, on_bad_lines="skip")
            break
        except UnicodeDecodeError as e:
            last_error = e
            continue
        except pd.errors.ParserError:
            try:
                df = pd.read_csv(
                    DATA_PATH,
                    encoding=enc,
                    engine="python",
                    on_bad_lines="skip",
                )
                break
            except Exception as e:
                last_error = e
                continue

    if df is None:
        df = pd.read_csv(
            DATA_PATH,
            encoding="latin1",
            encoding_errors="replace",
            engine="python",
            on_bad_lines="skip",
        )
        if df.empty and last_error is not None:
            raise last_error

    # Rapikan nama kolom (hilangkan spasi berlebih)
    df.columns = df.columns.str.strip()

    # Cari kolom waktu yang tersedia atau susun dari year/month/day/hour
    candidate_cols = ["datetime", "date", "dteday", "timestamp", "time"]
    found_col = next((c for c in candidate_cols if c in df.columns), None)

    if found_col is not None:
        df["datetime"] = pd.to_datetime(df[found_col], errors="coerce")
    elif {"year", "month", "day"}.issubset(df.columns):
        time_parts = {
            "year": df["year"],
            "month": df["month"],
            "day": df["day"],
        }
        if "hour" in df.columns:
            time_parts["hour"] = df["hour"]
        df["datetime"] = pd.to_datetime(time_parts, errors="coerce")
    else:
        raise KeyError(
            f"Kolom waktu tidak ditemukan. Kolom yang tersedia: {list(df.columns)}"
        )

    df = df.dropna(subset=["datetime"])

    if "month" not in df.columns:
        df["month"] = df["datetime"].dt.month
    if "hour" not in df.columns:
        df["hour"] = df["datetime"].dt.hour

    for col in ("PM2.5", "PM10"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


df = load_data()

# Sidebar filter
st.sidebar.header("Filter Data")
stations = sorted(df["station"].dropna().astype(str).unique())
selected_stations = st.sidebar.multiselect(
    "Pilih Stasiun",
    options=stations,
    default=stations,
)

min_date = df["datetime"].min().date()
max_date = df["datetime"].max().date()
date_range = st.sidebar.date_input(
    "Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

filtered_df = df[df["station"].astype(str).isin(selected_stations)].copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_dt = pd.to_datetime(date_range[0])
    end_dt = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)
    filtered_df = filtered_df[
        (filtered_df["datetime"] >= start_dt) & (filtered_df["datetime"] < end_dt)
    ]

# Judul & KPI Ringkas
st.title("Dashboard Analisis Kualitas Udara")
st.caption(
    "Ringkasan konsentrasi PM2.5 dan PM10 lintas stasiun, bulan, serta jam"
)

if filtered_df.empty:
    st.warning(
        "Tidak ada data yang sesuai dengan filter stasiun atau rentang tanggal yang dipilih."
    )
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Total Observasi", f"{len(filtered_df):,}")
col2.metric("Rata-Rata PM2.5 (µg/m³)", f"{filtered_df['PM2.5'].mean():.2f}")
col3.metric("Rata-Rata PM10 (µg/m³)", f"{filtered_df['PM10'].mean():.2f}")

st.divider()

# Visualisasi Pertanyaan 1: Rata-rata PM2.5 per stasiun
st.subheader("1. Rata-Rata Konsentrasi PM2.5 per Stasiun")
station_pm25 = (
    filtered_df.groupby("station", observed=False)["PM2.5"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)

fig1, ax1 = plt.subplots(figsize=(10, 5))
sns.barplot(
    data=station_pm25,
    x="PM2.5",
    y="station",
    hue="station",
    palette="Reds_r",
    legend=False,
    ax=ax1,
)
ax1.set_xlabel("Rata-Rata PM2.5 (µg/m³)")
ax1.set_ylabel("Stasiun")
ax1.grid(axis="x", linestyle="--", alpha=0.5)
st.pyplot(fig1)
plt.close(fig1)

# Visualisasi Pertanyaan 2: Pola Bulanan & Per Jam (PM2.5 dan PM10)
st.subheader("2. Pola Bulanan & Per Jam PM2.5 dan PM10")
tab_month, tab_hour = st.tabs(["Per Bulan", "Per Jam"])

with tab_month:
    monthly_df = (
        filtered_df.groupby("month", observed=False)[["PM2.5", "PM10"]]
        .mean()
        .reset_index()
    )
    fig2, ax2 = plt.subplots(figsize=(10, 4.5))
    ax2.plot(
        monthly_df["month"], monthly_df["PM2.5"], marker="o", label="PM2.5"
    )
    ax2.plot(monthly_df["month"], monthly_df["PM10"], marker="s", label="PM10")
    ax2.set_xticks(range(1, 13))
    ax2.set_xlabel("Bulan")
    ax2.set_ylabel("Konsentrasi (µg/m³)")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig2)
    plt.close(fig2)

with tab_hour:
    hourly_df = (
        filtered_df.groupby("hour", observed=False)[["PM2.5", "PM10"]]
        .mean()
        .reset_index()
    )
    fig3, ax3 = plt.subplots(figsize=(10, 4.5))
    ax3.plot(hourly_df["hour"], hourly_df["PM2.5"], marker="o", label="PM2.5")
    ax3.plot(hourly_df["hour"], hourly_df["PM10"], marker="s", label="PM10")
    ax3.set_xticks(range(0, 24))
    ax3.set_xlabel("Jam (0–23)")
    ax3.set_ylabel("Konsentrasi (µg/m³)")
    ax3.legend()
    ax3.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig3)
    plt.close(fig3)
