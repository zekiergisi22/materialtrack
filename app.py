import streamlit as st
import pandas as pd
from datetime import date
import uuid

# Sayfa Ayarları
st.set_page_config(page_title="Malzeme Tedarik Sistemi", layout="wide")

# Geçici Veritabanı (Session State) Başlatma
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        "Talep_ID", "Malzeme_Adı", "Miktar", "Birim", "Talep_Tarihi", 
        "Durum", "Seçilen_Tedarikçi", "Birim_Fiyat", "Sahaya_Ulaşım_Tarihi"
    ])

st.title("🏗️ Endüstriyel Malzeme Tedarik ve Takip Sistemi")

# Yan Menü (Sidebar) Navigasyonu
menu = st.sidebar.selectbox(
    "Modül Seçiniz",
    ["1. Yeni Malzeme Talebi", "2. Teklif Değerlendirme & Sipariş", "3. Saha Kabul & Kontrol", "4. Genel Rapor"]
)

# --- 1. MODÜL: YENİ MALZEME TALEBİ ---
if menu == "1. Yeni Malzeme Talebi":
    st.header("Yeni Malzeme Talebi Oluştur")
    with st.form("yeni_talep_formu"):
        malzeme = st.text_input("Malzeme Adı / Özellikleri (Örn: Çelik Boru 8 inç)")
        col1, col2 = st.columns(2)
        miktar = col1.number_input("Miktar", min_value=1, step=1)
        birim = col2.selectbox("Birim", ["Adet", "Ton", "Metre", "Paket"])
        talep_tarihi = st.date_input("Talep Tarihi", date.today())
        
        submit = st.form_submit_button("Talebi Kaydet")
        
        if submit and malzeme:
            yeni_kayit = {
                "Talep_ID": str(uuid.uuid4())[:8],
                "Malzeme_Adı": malzeme,
                "Miktar": miktar,
                "Birim": birim,
                "Talep_Tarihi": talep_tarihi,
                "Durum": "Talep Açıldı", # Statü: Talep Açıldı -> Sipariş Verildi -> Sahaya Ulaştı
                "Seçilen_Tedarikçi": "-",
                "Birim_Fiyat": 0.0,
                "Sahaya_Ulaşım_Tarihi": "-"
            }
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([yeni_kayit])], ignore_index=True)
            st.success(f"{malzeme} talebi başarıyla oluşturuldu!")

# --- 2. MODÜL: TEKLİF VE SİPARİŞ ---
elif menu == "2. Teklif Değerlendirme & Sipariş":
    st.header("Teklif Değerlendirme ve Sipariş Oluşturma")
    bekleyen_talepler = st.session_state.data[st.session_state.data["Durum"] == "Talep Açıldı"]
    
    if bekleyen_talepler.empty:
        st.info("Bekleyen talep bulunmamaktadır.")
    else:
        secilen_talep = st.selectbox("İşlem Yapılacak Talep", bekleyen_talepler["Talep_ID"] + " - " + bekleyen_talepler["Malzeme_Adı"])
        talep_id = secilen_talep.split(" - ")[0]
        
        with st.form("siparis_formu"):
            tedarikci = st.text_input("Anlaşılan Tedarikçi Firma")
            fiyat = st.number_input("Birim Fiyat (USD/TRY)", min_value=0.0, format="%.2f")
            
            siparis_ver = st.form_submit_button("Siparişi Onayla")
            
            if siparis_ver and tedarikci:
                idx = st.session_state.data.index[st.session_state.data["Talep_ID"] == talep_id].tolist()[0]
                st.session_state.data.at[idx, "Durum"] = "Sipariş Verildi (Yolda)"
                st.session_state.data.at[idx, "Seçilen_Tedarikçi"] = tedarikci
                st.session_state.data.at[idx, "Birim_Fiyat"] = fiyat
                st.success("Sipariş başarıyla oluşturuldu ve tedarikçi sisteme işlendi!")

# --- 3. MODÜL: SAHA KABUL ---
elif menu == "3. Saha Kabul & Kontrol":
    st.header("Saha Kabul ve Kalite Kontrol")
    yoldaki_siparisler = st.session_state.data[st.session_state.data["Durum"] == "Sipariş Verildi (Yolda)"]
    
    if yoldaki_siparisler.empty:
        st.info("Sahaya gelmesi beklenen sipariş bulunmamaktadır.")
    else:
        secilen_teslimat = st.selectbox("Teslim Alınan Malzeme", yoldaki_siparisler["Talep_ID"] + " - " + yoldaki_siparisler["Malzeme_Adı"])
        teslim_id = secilen_teslimat.split(" - ")[0]
        
        with st.form("kabul_formu"):
            kabul_tarihi = st.date_input("Sahaya Ulaşım Tarihi", date.today())
            kalite_onay = st.checkbox("Gözle Kontrol / Kalite Onayı Başarılı")
            
            teslim_al = st.form_submit_button("Sahaya Kabul Et")
            
            if teslim_al:
                if kalite_onay:
                    idx = st.session_state.data.index[st.session_state.data["Talep_ID"] == teslim_id].tolist()[0]
                    st.session_state.data.at[idx, "Durum"] = "Sahaya Ulaştı (Kabul Edildi)"
                    st.session_state.data.at[idx, "Sahaya_Ulaşım_Tarihi"] = kabul_tarihi
                    st.success("Malzeme başarıyla sahaya kabul edildi ve stoklara işlendi!")
                else:
                    st.error("Kalite onayı verilmeden saha kabulü yapılamaz!")

# --- 4. MODÜL: GENEL RAPOR ---
elif menu == "4. Genel Rapor":
    st.header("Tüm Malzeme Tedarik Durumu")
    # Pandas DataFrame'i etkileşimli bir tablo olarak gösterme
    st.dataframe(st.session_state.data, use_container_width=True)
    
    # Basit metrikler
    toplam_talep = len(st.session_state.data)
    yoldaki = len(st.session_state.data[st.session_state.data["Durum"] == "Sipariş Verildi (Yolda)"])
    sahada = len(st.session_state.data[st.session_state.data["Durum"] == "Sahaya Ulaştı (Kabul Edildi)"])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Talep Edilen Kalem", toplam_talep)
    col2.metric("Yoldaki Malzeme Kalemi", yoldaki)
    col3.metric("Sahaya Ulaşan Kalem", sahada)