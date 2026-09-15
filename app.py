import streamlit as st
import pandas as pd
import numpy as np
import os

# 1. Sayfa ve Tema Yapılandırması
st.set_page_config(
    page_title="Pro Odds AI - Bet365 Auto GitHub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Koyu Tema CSS
st.markdown("""
<style>
    .main { background-color: #0f172a; }
    .stApp { background-color: #0f172a; color: #f8fafc; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #10b981 !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ PRO ODDS AI — Otomatik Analiz Paneli")
st.caption("2010 - 2026 Bet365 Veri Kümesi Doğrudan GitHub Repository Üzerinden Okunmaktadır")
st.markdown("---")

@st.cache_data(ttl=3600)
def load_data():
    # 1. Öncelik: Repoda aynı dizindeki CSV dosyası
    if os.path.exists("football_data_2010_2026_b365.csv"):
        return pd.read_csv("football_data_2010_2026_b365.csv")
    # 2. Öncelik: Repoda aynı dizindeki Excel dosyası
    elif os.path.exists("football_data_2010_2026_b365.xlsx"):
        return pd.read_excel("football_data_2010_2026_b365.xlsx")
    else:
        return None

# Veriyi Otomatik Yükle
df = load_data()

if df is not None:
    st.sidebar.success("✅ Veri Kümesi Otomatik Yüklendi")
    st.sidebar.header("🎯 Bet365 Oran Filtresi")
    
    match_mode = st.sidebar.radio("Arama Modu", ["Aralık İle Filtrele (Toleranslı)", "Birebir Tam Oran Eşleştir"])
    tol = 0.05 if match_mode == "Aralık İle Filtrele (Toleranslı)" else 0.00

    # Lig Seçimi
    if 'Div' in df.columns:
        leagues = ['Tüm Ligler'] + sorted(df['Div'].dropna().unique().tolist())
        selected_league = st.sidebar.selectbox("Lig Seçin", leagues)
        if selected_league != 'Tüm Ligler':
            df = df[df['Div'] == selected_league]

    # Bet365 Oran Girişleri
    st.sidebar.subheader("📌 Bet365 Açılış Oranları")
    b365h = st.sidebar.number_input("Ev Sahibi (B365H)", value=1.75, step=0.01)
    b365d = st.sidebar.number_input("Beraberlik (B365D)", value=3.60, step=0.01)
    b365a = st.sidebar.number_input("Deplasman (B365A)", value=4.50, step=0.01)
    
    use_triple = st.sidebar.checkbox("MS Oranlarının Üçünü De Filtrele", value=True)

    filtered_df = df.copy()

    # Filtreleme Mantığı
    if 'B365H' in filtered_df.columns:
        if match_mode == "Birebir Tam Oran Eşleştir":
            if use_triple and 'B365D' in filtered_df.columns and 'B365A' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['B365H'] == b365h) & 
                    (filtered_df['B365D'] == b365d) & 
                    (filtered_df['B365A'] == b365a)
                ]
            else:
                filtered_df = filtered_df[filtered_df['B365H'] == b365h]
        else:
            if use_triple and 'B365D' in filtered_df.columns and 'B365A' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['B365H'].between(b365h - tol, b365h + tol)) & 
                    (filtered_df['B365D'].between(b365d - tol, b365d + tol)) & 
                    (filtered_df['B365A'].between(b365a - tol, b365a + tol))
                ]
            else:
                filtered_df = filtered_df[filtered_df['B365H'].between(b365h - tol, b365h + tol)]

    total_matches = len(filtered_df)
    st.subheader(f"📊 Bulunan Maç Sayısı: {total_matches}")

    if total_matches > 0:
        # 1. Maç Sonucu Dağılımları
        ms1_ratio = (filtered_df['FTR'] == 'H').mean() * 100 if 'FTR' in filtered_df.columns else 0
        ms0_ratio = (filtered_df['FTR'] == 'D').mean() * 100 if 'FTR' in filtered_df.columns else 0
        ms2_ratio = (filtered_df['FTR'] == 'A').mean() * 100 if 'FTR' in filtered_df.columns else 0

        # 2. Gol İstatistikleri
        has_goals = 'FTHG' in filtered_df.columns and 'FTAG' in filtered_df.columns
        if has_goals:
            filtered_df['TotalGoals'] = filtered_df['FTHG'] + filtered_df['FTAG']
            over15_ratio = (filtered_df['TotalGoals'] > 1.5).mean() * 100
            over25_ratio = (filtered_df['TotalGoals'] > 2.5).mean() * 100
            over35_ratio = (filtered_df['TotalGoals'] > 3.5).mean() * 100
            btts_ratio = ((filtered_df['FTHG'] > 0) & (filtered_df['FTAG'] > 0)).mean() * 100

        # AI Sinyalleri
        st.markdown("### 🤖 Yapay Zeka Sinyalleri")
        signals = []
        if total_matches >= 3:
            if ms1_ratio >= 60: signals.append(("MS 1 (Ev Sahibi)", ms1_ratio))
            if ms0_ratio >= 35: signals.append(("MS 0 (Beraberlik)", ms0_ratio))
            if ms2_ratio >= 60: signals.append(("MS 2 (Deplasman)", ms2_ratio))
            if has_goals:
                if over15_ratio >= 75: signals.append(("1.5 ÜST Gol ⚽", over15_ratio))
                if over25_ratio >= 60: signals.append(("2.5 ÜST Gol ⚽", over25_ratio))
                if (100 - over25_ratio) >= 60: signals.append(("2.5 ALT Gol 🛡️", 100 - over25_ratio))
                if btts_ratio >= 60: signals.append(("KG VAR 🤝", btts_ratio))

            if signals:
                cols = st.columns(min(len(signals), 4))
                for idx, (sig_name, sig_val) in enumerate(signals):
                    cols[idx % 4].success(f"🔥 **GÜÇLÜ SİNYAL**\n\n**{sig_name}**\n\nBaşarı: **%{sig_val:.1f}**")
            else:
                st.info("💡 Bu oran aralığında yüksek yüzdeli tek bir sonuç öne çıkmadı.")
        else:
            st.warning("⚠️ Daha güvenilir sinyal için toleransı biraz artırabilirsiniz.")

        # Metrik Kartları
        st.markdown("---")
        st.markdown("### 📈 Maç Sonucu (MS) Dağılımı")
        m1, m2, m3 = st.columns(3)
        m1.metric("MS 1 (Ev)", f"%{ms1_ratio:.1f}")
        m2.metric("MS 0 (Berabere)", f"%{ms0_ratio:.1f}")
        m3.metric("MS 2 (Deplasman)", f"%{ms2_ratio:.1f}")

        if has_goals:
            st.markdown("---")
            st.markdown("### ⚽ Gol İstatistikleri")
            g1, g2, g3, g4 = st.columns(4)
            g1.metric("1.5 Üst %", f"%{over15_ratio:.1f}")
            g2.metric("2.5 Üst %", f"%{over25_ratio:.1f}")
            g3.metric("3.5 Üst %", f"%{over35_ratio:.1f}")
            g4.metric("KG Var %", f"%{btts_ratio:.1f}")

        # Tablo Gösterimi
        st.markdown("---")
        st.markdown("### 📋 Eşleşen Geçmiş Maçlar")
        cols_to_show = [c for c in ['Season', 'Div', 'Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'B365H', 'B365D', 'B365A'] if c in filtered_df.columns]
        st.dataframe(filtered_df[cols_to_show], use_container_width=True)

    else:
        st.error("Aranan oran kombinasyonuna uygun geçmiş maç bulunamadı.")
else:
    st.warning("⚠️ Veri dosyası (`football_data_2010_2026_b365.csv` veya `.xlsx`) repository içinde bulunamadı.")
