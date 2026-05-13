import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date

# --- 1. SAYFA VE GÖRÜNÜM AYARLARI ---
st.set_page_config(page_title="MOL-OCU Tedarik Yönetimi", page_icon="🏗️", layout="wide")

st.title("🏗️ MOL-OCU Malzeme Tedarik ve Veri Giriş Sistemi")

# --- 2. GOOGLE SHEETS BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Mevcut veriyi çek (ttl=0 yaparak her işlemde taze veri alıyoruz)
df = conn.read(ttl=0)
df = df.dropna(how="all")
df.columns = df.columns.str.strip() # Sütun isimlerini temizle

# --- 3. YAN MENÜ (NAVİGASYON) ---
menu = st.sidebar.selectbox("İşlem Seçiniz", ["📊 Dashboard", "📝 Yeni Veri Girişi"])

# --- 4. MODÜL: DASHBOARD (İZLEME) ---
if menu == "📊 Dashboard":
    # (Önceki yazdığımız Dashboard kodlarını buraya alıyoruz)
    st.subheader("Anlık Tedarik Durumu")
    
    # Hızlı Filtreleme Mantığı
    pr_bekleyen = df[(df['Quotation_Status'].str.contains('Approved', case=False, na=False)) & (df['PR_No'].fillna('').str.strip() == '')]
    po_bekleyen = df[(df['PR_No'].fillna('').str.strip() != '') & (df['PO_No'].fillna('').str.strip() == '')]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Kalem", len(df))
    c2.metric("PR Bekleyen", len(pr_bekleyen))
    c3.metric("PO Bekleyen", len(po_bekleyen))
    
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- 5. MODÜL: YENİ VERİ GİRİŞİ ---
elif menu == "📝 Yeni Veri Girişi":
    st.subheader("Yeni Malzeme Kaydı Oluştur")
    
    # Mevcut Ana Grupları listeden al (veya yeni yazılmasına izin ver)
    ana_gruplar = df['Ana_Grup'].dropna().unique().tolist()
    
    with st.form("yeni_kayit_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            secilen_grup = st.selectbox("Ana Grubu Seçin", options=["--- Yeni Grup Ekle ---"] + ana_gruplar)
            if secilen_grup == "--- Yeni Grup Ekle ---":
                yeni_grup_adi = st.text_input("Yeni Ana Grup Adını Yazın (Örn: 50.OCU-Pipeline)")
                ana_grup = yeni_grup_adi
            else:
                ana_grup = secilen_grup
            
            malzeme = st.text_input("Malzeme Kalemi / Cinsi")
            durum = st.selectbox("Teklif Durumu", ["Quotation Approved", "Quotation Received", "Material List Sent for Quotation", "Under Preperation"])
            
        with col2:
            pr_no = st.text_input("PR Numarası (Varsa)")
            po_no = st.text_input("PO Numarası (Varsa)")
            receiving_pct = st.number_input("Saha Kabul Yüzdesi (%)", min_value=0, max_value=100, value=0)
            
        notlar = st.text_area("Malzeme Notları / Detaylar")
        
        submit_button = st.form_submit_button("Veritabanına Kaydet")
        
        if submit_button:
            if ana_grup and malzeme:
                # Yeni veriyi bir sözlük (dictionary) olarak hazırla
                # Google Sheets'teki sütun başlıklarınızla BİREBİR aynı olmalı
                yeni_veri = {
                    "Ana_Grup": ana_grup,
                    "Malzeme_Kalemi": malzeme,
                    "Quotation_Status": durum,
                    "PR_No": pr_no,
                    "PO_No": po_no,
                    "Receiving_Pct": receiving_pct,
                    "Description / Remarks": notlar
                }
                
                # Mevcut DataFrame'e ekle
                yeni_df = pd.concat([df, pd.DataFrame([yeni_veri])], ignore_index=True)
                
                # Google Sheets'i GÜNCELLE
                conn.update(data=yeni_df)
                
                st.success(f"✅ {malzeme} başarıyla Google Sheets'e kaydedildi!")
                st.balloons()
            else:
                st.warning("Lütfen 'Ana Grup' ve 'Malzeme Kalemi' alanlarını doldurun.")
