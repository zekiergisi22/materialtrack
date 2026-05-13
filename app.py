import streamlit as st
import pandas as pd
import numpy as np

# Sayfa Ayarları
st.set_page_config(page_title="MOL-OCU Tedarik Dashboard", page_icon="🏗️", layout="wide")

# Veri Yükleme ve Temizleme Fonksiyonu
@st.cache_data
def load_and_clean_data():
    # Normalde buraya: df = pd.read_csv("MOL-OCU Material Procurement Follow-up .xlsx - Material.csv") gelecek
    # Excel'den gelen bu karmaşık yapıyı sizin için simüle eden ve düzleştiren bir DataFrame oluşturuyoruz.
    # Sistemin nasıl çalışacağını görmeniz için örnek veriler:
    
    data = {
        "Ana_Grup": ["16.Project Material Part 4", "16.Project Material Part 4", "44.MOL-TKN-638 - Precom", "46.OCU-MOL-TKN-634", "21.Teknokon Site Support"],
        "Malzeme_Tipi": ["Leser Valve", "Flange Blind", "Fittings&Tube", "Steel Profile", "Bolt&Nut&Gasket"],
        "Quotation_Status": ["Quotation Approved", "Quotation Approved", "Material List Sent for Quotation", "Quotation Approved", "Quotation Received"],
        "Supplier": ["Leser", "-", "-", "Local", "SOLTESZ"],
        "PR_No": ["PR-1001", np.nan, np.nan, "PR-1045", np.nan],
        "PO_No": ["PO-5001", np.nan, np.nan, np.nan, np.nan],
        "Receiving_Pct": [100, 0, 0, 0, 0],
        "Delivery_Date": ["2026-06-01", "-", "-", "2026-05-20", "2-3 Weeks"]
    }
    df = pd.DataFrame(data)
    return df

df = load_and_clean_data()

# --- MANTIK (LOGIC) HESAPLAMALARI ---
# 1. Quotation Onaylanmış ama PR (Purchase Request) Bekleyenler
pr_bekleyen = df[(df['Quotation_Status'] == 'Quotation Approved') & (df['PR_No'].isna())]

# 2. PR Yapılmış ama PO (Purchase Order) Bekleyenler
po_bekleyen = df[(df['PR_No'].notna()) & (df['PO_No'].isna())]

# 3. Sahaya Ulaşmış Malzemeler (%100 Kabul edilenler veya PO'su olup gelenler)
sahaya_ulasan = df[df['Receiving_Pct'] >= 100]

# --- DASHBOARD ARAYÜZÜ ---
st.title("📊 MOL-OCU Projesi Malzeme Tedarik ve Takip Dashboard'u")
st.markdown("Bu panel üzerinden tüm malzemelerin onay, sipariş ve sahaya varış durumlarını anlık olarak takip edebilirsiniz.")

# Üst Metrikler (KPIs)
st.subheader("Genel Durum Özetleri")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Toplam Takip Edilen Kalem", len(df))
col2.metric("Teklif Onaylı / PR Bekleyen", len(pr_bekleyen), delta="- Acil aksiyon", delta_color="inverse")
col3.metric("PR Kesilmiş / PO Bekleyen", len(po_bekleyen), delta="- Siparişe Dönüşmeli", delta_color="inverse")
col4.metric("Sahaya Ulaşan Malzemeler", len(sahaya_ulasan), delta="+ Teslim Alındı")

st.divider()

# --- DETAYLI TABLOLAR VE FİLTRELEME ---
st.subheader("📌 Kategori Bazlı Detay Görünümleri")

# Sekmeler (Tabs) ile ekranı temiz tutalım
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 PR Bekleyenler (Teklif Onaylı)", 
    "⏳ PO Bekleyenler (PR Kesilmiş)", 
    "✅ Sahaya Ulaşanlar", 
    "🔍 Genel Arama / Tüm Veriler"
])

with tab1:
    st.markdown("**Açıklama:** Teklifi onaylanmış (Quotation Approved) ancak henüz Satınalma Talebi (PR) açılmamış kalemler.")
    st.dataframe(pr_bekleyen, use_container_width=True, hide_index=True)

with tab2:
    st.markdown("**Açıklama:** PR numarası alınmış ancak henüz Satınalma Siparişine (PO) dönüştürülmemiş, tedarikçiye geçilmemiş siparişler.")
    st.dataframe(po_bekleyen, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("**Açıklama:** Sahaya gelmiş ve %100 teslim alınmış (Material Receiving % = 100) malzemeler.")
    st.dataframe(sahaya_ulasan, use_container_width=True, hide_index=True)

with tab4:
    st.markdown("**Genel Filtreleme ve Arama Ekranı**")
    
    # Detaya inmek için (Drill-down) filtreler
    f_col1, f_col2 = st.columns(2)
    secilen_grup = f_col1.multiselect("Ana Grup Seçiniz (Örn: 16.Project Material Part 4)", options=df['Ana_Grup'].unique())
    secilen_status = f_col2.multiselect("Teklif Durumuna Göre Filtrele", options=df['Quotation_Status'].unique())
    
    # Filtreyi uygula
    filtrelenmis_df = df.copy()
    if secilen_grup:
        filtrelenmis_df = filtrelenmis_df[filtrelenmis_df['Ana_Grup'].isin(secilen_grup)]
    if secilen_status:
        filtrelenmis_df = filtrelenmis_df[filtrelenmis_df['Quotation_Status'].isin(secilen_status)]
        
    st.dataframe(filtrelenmis_df, use_container_width=True, hide_index=True)
