import glob
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

file_paths = sorted(glob.glob("**/PRSA_Data_*_20130301-20170228.csv", recursive=True))

station_dfs = []
for path in file_paths:
  temp_df = pd.read_csv(path, delimiter=",")
  if "station" not in temp_df.columns:
    temp_df["station"] = os.path.basename(path).split("_")[2]
  station_dfs.append(temp_df)

if not station_dfs:
  raise FileNotFoundError(
      "File PRSA_Data_*_20130301-20170228.csv tidak ditemukan. Cek"
      " folder aktif atau path file."
  )

air_quality_df = pd.concat(station_dfs, axis=0, ignore_index=True)
air_quality_df.head()

# 1. Cek informasi kolom, jumlah non-null, dan tipe data
air_quality_df.info()

# 2. Cek jumlah missing value per kolom
print("\nMissing values per kolom:")
print(air_quality_df.isna().sum())

# 3. Cek jumlah data duplikat
print("\nJumlah duplikasi:", air_quality_df.duplicated().sum())

# 4. Cek ringkasan statistik kolom numerik (cek nilai min/max/outlier)
air_quality_df.describe()

# Buat salinan agar data mentah tetap aman bila ingin dibandingkan
clean_aq_df = air_quality_df.copy()

# 1. Menghapus data duplikat (jika ada)
clean_aq_df.drop_duplicates(inplace=True)
print("Jumlah duplikasi setelah dibersihkan:", clean_aq_df.duplicated().sum())

# 2. Membuat kolom datetime dari year, month, day, hour
clean_aq_df["datetime"] = pd.to_datetime(
    clean_aq_df[["year", "month", "day", "hour"]]
)

# 3. Menangani nilai tidak wajar (misalnya nilai polutan negatif jika muncul)
for col in ["PM2.5", "PM10"]:
  if col in clean_aq_df.columns:
    clean_aq_df.loc[clean_aq_df[col] < 0, col] = np.nan

# 4. Menangani missing value pada kolom utama (PM2.5 dan PM10)
# Opsi A (umum untuk analisis rata-rata per stasiun/bulan/jam): hapus baris yang kosong pada PM2.5 / PM10
clean_aq_df = clean_aq_df.dropna(subset=["PM2.5", "PM10"])

# Opsi B (alternatif interpolasi per stasiun jika ingin menjaga kontinuitas waktu):
# clean_aq_df["PM2.5"] = clean_aq_df.groupby("station")["PM2.5"].transform(lambda s: s.interpolate(method="linear").bfill().ffill())
# clean_aq_df["PM10"] = clean_aq_df.groupby("station")["PM10"].transform(lambda s: s.interpolate(method="linear").bfill().ffill())

print("\nMissing values PM2.5 & PM10 setelah cleaning:")
print(clean_aq_df[["PM2.5", "PM10"]].isna().sum())
clean_aq_df.info()

# Agregasi rata-rata dan statistik PM2.5 per stasiun
station_pm25 = (
    clean_aq_df.groupby(by="station", observed=False)["PM2.5"]
    .agg(mean_pm25="mean", median_pm25="median", count="count")
    .sort_values(by="mean_pm25", ascending=False)
    .reset_index()
)

highest_station = station_pm25.iloc[0]
lowest_station = station_pm25.iloc[-1]

# Selisih persentase tertinggi terhadap terendah
pct_diff_station = (
    (highest_station["mean_pm25"] - lowest_station["mean_pm25"])
    / lowest_station["mean_pm25"]
) * 100

print(station_pm25)
print(
    f"\nTertinggi: {highest_station['station']} ({highest_station['mean_pm25']:.2f} µg/m³)"
)
print(
    f"Terendah: {lowest_station['station']} ({lowest_station['mean_pm25']:.2f} µg/m³)"
)
print(
    f"Selisih persentase (tertinggi vs terendah): {pct_diff_station:.2f}%"
)

# Visualisasi Pertanyaan 1
plt.figure(figsize=(10, 6))
sns.barplot(
    data=station_pm25,
    x="mean_pm25",
    y="station",
    palette="Reds_r",
)
plt.title(
    "Rata-Rata Konsentrasi PM2.5 per Stasiun (Maret 2013 – Februari 2017)",
    fontsize=13,
)
plt.xlabel("Rata-Rata PM2.5 (µg/m³)")
plt.ylabel("Stasiun Pemantauan")
plt.grid(axis="x", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()

# 1. Rata-rata bulanan (1 - 12)
monthly_pollutants = (
    clean_aq_df.groupby(by="month", observed=False)[["PM2.5", "PM10"]]
    .mean()
    .reset_index()
)

# 2. Rata-rata per jam (0 - 23)
hourly_pollutants = (
    clean_aq_df.groupby(by="hour", observed=False)[["PM2.5", "PM10"]]
    .mean()
    .reset_index()
)

# Hitung puncak & terendah per jam untuk PM2.5 dan PM10
for col in ["PM2.5", "PM10"]:
  peak_row = hourly_pollutants.loc[hourly_pollutants[col].idxmax()]
  low_row = hourly_pollutants.loc[hourly_pollutants[col].idxmin()]
  pct_increase_hour = ((peak_row[col] - low_row[col]) / low_row[col]) * 100
  print(
      f"{col} -> Jam puncak: {int(peak_row['hour']):02d}:00"
      f" ({peak_row[col]:.2f}), Jam terendah: {int(low_row['hour']):02d}:00"
      f" ({low_row[col]:.2f}), Kenaikan: {pct_increase_hour:.2f}%"
  )

peak_month_pm25 = monthly_pollutants.loc[
    monthly_pollutants["PM2.5"].idxmax()
]
peak_month_pm10 = monthly_pollutants.loc[
    monthly_pollutants["PM10"].idxmax()
]
print(
    f"Bulan puncak PM2.5: {int(peak_month_pm25['month'])}"
    f" ({peak_month_pm25['PM2.5']:.2f}) | PM10: {int(peak_month_pm10['month'])}"
    f" ({peak_month_pm10['PM10']:.2f})"
)

# Visualisasi Pertanyaan 2: Bulanan & Jam
fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(11, 9))

# Grafik atas: Tren bulanan
axes[0].plot(
    monthly_pollutants["month"],
    monthly_pollutants["PM2.5"],
    marker="o",
    label="PM2.5",
)
axes[0].plot(
    monthly_pollutants["month"],
    monthly_pollutants["PM10"],
    marker="s",
    label="PM10",
)
axes[0].set_title(
    "Rata-Rata Konsentrasi PM2.5 dan PM10 per Bulan (2013–2017)"
)
axes[0].set_xlabel("Bulan")
axes[0].set_ylabel("Konsentrasi (µg/m³)")
axes[0].set_xticks(range(1, 13))
axes[0].legend()
axes[0].grid(True, linestyle="--", alpha=0.5)

# Grafik bawah: Tren per jam
axes[1].plot(
    hourly_pollutants["hour"],
    hourly_pollutants["PM2.5"],
    marker="o",
    label="PM2.5",
)
axes[1].plot(
    hourly_pollutants["hour"],
    hourly_pollutants["PM10"],
    marker="s",
    label="PM10",
)
axes[1].set_title(
    "Rata-Rata Konsentrasi PM2.5 dan PM10 per Jam (2013–2017)"
)
axes[1].set_xlabel("Jam (0–23)")
axes[1].set_ylabel("Konsentrasi (µg/m³)")
axes[1].set_xticks(range(0, 24))
axes[1].legend()
axes[1].grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
plt.show()

clean_aq_df.to_csv("clean_air_quality.csv", index=False)

