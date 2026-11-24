# Air Quality Analysis & Streamlit Dashboard ✨

Proyek analisis data kualitas udara dari 12 stasiun pemantauan (periode Maret 2013 – Februari 2017) yang dilengkapi *notebook* analisis di Google Colab serta *dashboard* interaktif berbasis Streamlit untuk memantau konsentrasi `PM2.5` dan `PM10` lintas stasiun, bulan, dan jam.

## Pertanyaan Bisnis Utama
1. **Perbandingan `PM2.5` per Stasiun:** Stasiun mana yang mencatat rata-rata konsentrasi `PM2.5` tertinggi hingga terendah, serta berapa selisih persentasenya untuk menentukan prioritas intervensi pengendalian polusi udara?
2. **Pola Bulanan & Per Jam (`PM2.5` & `PM10`):** Pada bulan dan jam berapa lonjakan rata-rata konsentrasi `PM2.5` dan `PM10` tertinggi terjadi, serta berapa persentase kenaikan jam puncak dibanding jam terendah sebagai acuan penjadwalan imbauan kesehatan dan aktivitas luar ruang?

## Struktur Proyek
* `notebook.ipynb` — Berisi tahapan *Data Wrangling* (*Gathering*, *Assessing*, *Cleaning*), *Exploratory Data Analysis (EDA)*, *Visualization & Explanatory Analysis*, serta *Conclusion & Recommendation*.
* `clean_air_quality.csv` — Dataset hasil pembersihan (411.813 baris observasi dengan kolom `datetime`, `station`, `month`, `hour`, `PM2.5`, `PM10`, serta variabel pendukung).
* `dashboard.py` — Aplikasi *dashboard* Streamlit interaktif dengan filter stasiun dan rentang tanggal, metrik ringkas, *barplot* rata-rata `PM2.5` per stasiun, serta grafik tren `PM2.5` dan `PM10` per bulan dan per jam.
* `requirements.txt` — Daftar *package* Python yang dibutuhkan untuk menjalankan *dashboard*.

## Setup Environment - Anaconda
```bash
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt

mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt

streamlit run dashboard.py
