import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. SAYFA VE GÖRÜNÜM AYARLARI ---
st.set_page_config(page_title="MOL-OCU Tedarik Yönetimi", page_icon="🏗️", layout="wide")

st.title("📊 MOL-OCU Projesi Malzeme Tedarik Dashboard")
st.markdown("Veriler doğrudan **OCU Material Track** isimli Google Sheets dosyanızdan canlı olarak çekilmektedir.")

# --- 2. GOOGLE SHEETS VERİTABANI BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Veriyi çek (ttl="1m" -> Verileri her 1 dakikada bir günceller)
    st.info("🔄 Google Sheets üzerinden güncel veriler senkronize ediliyor...")
    df = conn.read(ttl="1m")
    
    # Tüm satır veya sütunları tamamen boş olanları temizle
    df = df.dropna(how="all")
    
    # ÇOK ÖNEMLİ: Excel'deki görünmez boşluk hatalarını çözmek için tüm sütun isimlerini temizliyoruz
    df.columns = df.columns.str.strip()
    
    # Başlıklarınızdaki olası isim farklılıklarını garantiye almak için kontrol:
    # Eğer "Malzeme _Kalemi" gibi boşluklu yazılmışsa onu düzeltiriz.
    if 'Malzeme _Kalemi' in df.columns:
        df.rename(columns={'Malzeme _Kalemi': 'Malzeme_Kalemi'}, inplace=True)
    
    # --- 3. VERİ TEMİZLEME VE HAZIRLIK ---
    # Hata almamak için boş (NaN) değerleri string boşluğa ('') çeviriyoruz
    if 'PR_No' in df.columns:
        df['PR_No'] = df['PR_No'].fillna('').astype(str)
    else:
        st.error("⚠️ 'PR_No' sütunu bulunamadı. Lütfen Excel başlıklarını kontrol edin.")
        
    if 'PO_No' in df.columns:
        df['PO_No'] = df['PO_No'].fillna('').astype(str)
        
    if 'Quotation_Status' in df.columns:
        df['Quotation_Status'] = df['Quotation_Status'].fillna('').astype(str)
    
    # Yüzde değerlerini matematiksel işleme sokabilmek için sayıya çeviriyoruz
    if 'Receiving_Pct' in df.columns:
        df['Receiving_Pct'] = df['Receiving_Pct'].astype(str).str.replace('%', '').str.strip()
        df['Receiving_Pct'] = pd.to_numeric(df['Receiving_Pct'], errors='coerce').fillna(0)
    else:
        st.error("⚠️ 'Receiving_Pct' sütunu bulunamadı. Lütfen Excel başlıklarını kontrol edin.")

    # --- 4. MANTIKSAL FİLTRELEMELER ---
    
    # 1. PR Bekleyen: Teklifi onaylanmış (Approved) ama PR numarası boş olanlar
    pr_bekleyen = df[(df['Quotation_Status'].str.contains('Approved', case=False, na=False)) & (df['PR_No'].str.strip() == '')]
    
    # 2. PO Bekleyen: PR numarası girilmiş ama PO numarası boş olanlar
    po_bekleyen = df[(df['PR_No'].str.strip() != '') & (df['PO_No'].str.strip() == '')]
    
    # 3. Sahaya Ulaşan: Kabul yüzdesi (Receiving_Pct) 100 veya üzeri olanlar
    # Eğer Receiving_Pct sütunu bulunamazsa kodun çökmemesi için boş bir tablo (DataFrame) oluşturuyoruz
    if 'Receiving_Pct' in df.columns:
        sahaya_ulasan = df[df['Receiving_Pct'] >= 100]
    else:
        sahaya_ulasan = pd.DataFrame(columns=df.columns)

    # --- 5. ÜST METRİKLER (KPI KARTLARI) ---
    st.subheader("Anlık Durum Özetleri")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Toplam Takip Edilen Kalem", len(df))
    col2.metric("PR Açılması Bekleyen", len(pr_bekleyen), delta="Aksiyon Gerekli", delta_color="inverse")
    col3.metric("PO Siparişi Bekleyen", len(po_bekleyen), delta="Sipariş Bekliyor", delta_color="inverse")
    col4.metric("Sahaya Ulaşan Malzemeler", len(sahaya_ulasan), delta="Teslim Alındı")

    st.divider()

    # --- 6. SEKMELER (TABS) İLE DETAYLI RAPORLAMA ---
    st.subheader("📌 Kategori Bazlı İşlem Detayları")
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 PR Bekleyenler", 
        "⏳ PO Bekleyenler", 
        "✅ Sahaya Ulaşanlar", 
        "🔍 Tüm Veritabanı ve Arama"
    ])

    with tab1:
        st.error("**Tedarikçisi Onaylanmış ancak Satınalma Talebi (PR) henüz açılmamış malzemeler:**")
        st.dataframe(pr_bekleyen, use_container_width=True, hide_index=True)

    with tab2:
        st.warning("**PR Numarası alınmış ancak henüz Sipariş (PO) aşamasına geçilmemiş kalemler:**")
        st.dataframe(po_bekleyen, use_container_width=True, hide_index=True)

    with tab3:
        st.success("**Sahaya gelmiş ve %100 teslim alınmış malzemeler:**")
        st.dataframe(sahaya_ulasan, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("**🔍 Veritabanında Detaylı Arama Yapın**")
        
        arama = st.text_input("Aramak İstediğiniz Malzeme, Tedarikçi veya Ana Grubu Yazın (Örn: Flange, Leser, Steel):")
        
        if arama:
            mask = df.apply(lambda row: row.astype(str).str.contains(arama, case=False, na=False).any(), axis=1)
            filtrelenmis_df = df[mask]
            st.dataframe(filtrelenmis_df, use_container_width=True, hide_index=True)
            st.caption(f"Arama sonucunda {len(filtrelenmis_df)} kayıt bulundu.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("⚠️ Google Sheets'ten veri çekilirken bir hata oluştu.")
    st.info("Lütfen linkin herkese açık olduğundan ve Secrets ayarlarının doğru yapıldığından emin olun.")
    st.write("Teknik Hata Detayı:", e)
