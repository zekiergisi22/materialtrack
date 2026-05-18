import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. SAYFA VE GÖRÜNÜM AYARLARI ---
st.set_page_config(page_title="MOL-OCU Tedarik Yönetimi", page_icon="🏗️", layout="wide")

st.title("🏗️ MOL-OCU Malzeme Tedarik ve Veri Yönetim Sistemi")

# --- 2. GOOGLE SHEETS BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Mevcut veriyi çek (ttl=0 yaparak her sayfada taze veri alıyoruz)
    df = conn.read(ttl=0)
    df = df.dropna(how="all")
    df.columns = df.columns.str.strip() # Sütun isimlerini temizle

    # Boşluk hatalarını engellemek için veri tiplerini standartlaştıralım
    if 'PR_No' in df.columns:
        df['PR_No'] = df['PR_No'].fillna('').astype(str)
    if 'PO_No' in df.columns:
        df['PO_No'] = df['PO_No'].fillna('').astype(str)
    if 'Quotation_Status' in df.columns:
        df['Quotation_Status'] = df['Quotation_Status'].fillna('').astype(str)
    if 'Receiving_Pct' in df.columns:
        df['Receiving_Pct'] = df['Receiving_Pct'].astype(str).str.replace('%', '').str.strip()
        df['Receiving_Pct'] = pd.to_numeric(df['Receiving_Pct'], errors='coerce').fillna(0)

except Exception as e:
    st.error("⚠️ Google Sheets bağlantısında hata oluştu. Lütfen Secrets ayarlarını kontrol edin.")
    st.stop() # Hata varsa aşağıyı çalıştırma

# --- 3. YAN MENÜ (NAVİGASYON) ---
menu = st.sidebar.selectbox(
    "Ana Menü - İşlem Seçiniz", 
    ["📊 Dashboard (İzleme)", "📝 Yeni Malzeme Ekle", "✏️ Verileri Düzenle / Sil"]
)

st.sidebar.divider()
st.sidebar.info("💡 **Bilgi:** Bu sistemdeki tüm veriler 'OCU Material Track' isimli Google Sheets dosyanızla anlık olarak senkronizedir.")

# =======================================================
# MODÜL 1: DASHBOARD (İZLEME)
# =======================================================
if menu == "📊 Dashboard (İzleme)":
    st.subheader("Anlık Tedarik Durumu")
    
    # Hızlı Filtreleme Mantığı
    pr_bekleyen = df[(df['Quotation_Status'].str.contains('Approved', case=False, na=False)) & (df['PR_No'].str.strip() == '')]
    po_bekleyen = df[(df['PR_No'].str.strip() != '') & (df['PO_No'].str.strip() == '')]
    sahaya_ulasan = df[df['Receiving_Pct'] >= 100] if 'Receiving_Pct' in df.columns else pd.DataFrame()
    
    # Üst Metrikler
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Kalem", len(df))
    c2.metric("PR Bekleyen", len(pr_bekleyen), delta="Aksiyon Bekliyor", delta_color="inverse")
    c3.metric("PO Bekleyen", len(po_bekleyen), delta="Siparişe Dönüşmeli", delta_color="inverse")
    c4.metric("Sahaya Ulaşan", len(sahaya_ulasan), delta="Teslim Alındı")
    
    st.divider()
    
    # Detaylı Arama Ekranı
    st.markdown("**🔍 Veritabanında Arama Yapın**")
    arama = st.text_input("Malzeme, Tedarikçi veya Ana Grup arayın (Örn: Leser, Flange, PR-1001):")
    
    if arama:
        mask = df.apply(lambda row: row.astype(str).str.contains(arama, case=False, na=False).any(), axis=1)
        st.dataframe(df[mask], use_container_width=True, hide_index=True)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

# =======================================================
# MODÜL 2: YENİ VERİ GİRİŞİ
# =======================================================
elif menu == "📝 Yeni Malzeme Ekle":
    st.subheader("Sisteme Yeni Malzeme Kalemi Ekle")
    
    # Mevcut Ana Grupları listeden al (Hata vermemesi için boş olanları temizle)
    ana_gruplar = []
    if 'Ana_Grup' in df.columns:
        ana_gruplar = df['Ana_Grup'].dropna().unique().tolist()
    
    with st.form("yeni_kayit_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            secilen_grup = st.selectbox("Ana Grubu Seçin", options=["--- Yeni Grup Ekle ---"] + ana_gruplar)
            if secilen_grup == "--- Yeni Grup Ekle ---":
                ana_grup = st.text_input("Yeni Ana Grup Adını Yazın")
            else:
                ana_grup = secilen_grup
            
            malzeme = st.text_input("Malzeme Kalemi / Cinsi")
            durum = st.selectbox("Teklif Durumu", ["Quotation Approved", "Quotation Received", "Material List Sent for Quotation", "Under Preperation"])
            tedarikci = st.text_input("Tedarikçi Firma (Supplier)")
            
        with col2:
            pr_no = st.text_input("PR Numarası (Varsa)")
            po_no = st.text_input("PO Numarası (Varsa)")
            receiving_pct = st.number_input("Saha Kabul Yüzdesi (%)", min_value=0, max_value=100, value=0)
            
        submit_button = st.form_submit_button("Veritabanına Kaydet")
        
        if submit_button:
            if ana_grup and malzeme:
                yeni_veri = {
                    "Ana_Grup": ana_grup,
                    "Malzeme_Kalemi": malzeme,
                    "Quotation_Status": durum,
                    "Supplier": tedarikci,
                    "PR_No": pr_no,
                    "PO_No": po_no,
                    "Receiving_Pct": receiving_pct
                }
                
                # Mevcut verinin altına yeni veriyi ekle ve Google Sheets'i güncelle
                yeni_df = pd.concat([df, pd.DataFrame([yeni_veri])], ignore_index=True)
                conn.update(data=yeni_df)
                
                st.success(f"✅ {malzeme} başarıyla sisteme eklendi!")
                st.balloons()
            else:
                st.warning("Lütfen 'Ana Grup' ve 'Malzeme Kalemi' alanlarını eksiksiz doldurun.")

# =======================================================
# MODÜL 3: VERİ DÜZENLEME & SİLME (PORTAL)
# =======================================================
elif menu == "✏️ Verileri Düzenle / Sil":
    st.subheader("Canlı Veritabanı Düzenleyicisi")
    
    st.info("""
    **Nasıl Kullanılır?**
    * ✏️ **Düzenlemek için:** Değiştirmek istediğiniz hücreye çift tıklayın ve yeni değeri yazın.
    * 🗑️ **Silmek için:** Silmek istediğiniz satırın en solundaki gri kutucuğu seçin klavyenizden 'Delete' tuşuna veya sağ üstte çıkan çöp kutusu ikonuna basın.
    * ➕ **Hızlı Eklemek için:** Tablonun en altındaki boş satıra tıklayarak hızlıca yeni veri yazabilirsiniz.
    * 💾 İşleminiz bitince alttaki mavi renkli **Kaydet** butonuna basmayı unutmayın!
    """)
    
    # Etkileşimli Excel / Veri Düzenleyici Arayüzü (num_rows="dynamic" silme ve eklemeye izin verir)
    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        num_rows="dynamic", 
        height=600
    )
    
    # Değişiklikleri Kaydet Butonu
    if st.button("💾 Değişiklikleri Google Sheets'e Kaydet", type="primary", use_container_width=True):
        with st.spinner("Değişiklikler Google Sheets'e aktarılıyor..."):
            # Temizlenmiş ve düzenlenmiş son veriyi Google Sheets'e yazar
            conn.update(data=edited_df)
            st.success("✅ Tüm değişiklikleriniz başarıyla kaydedildi! Dashboard otomatik olarak güncellendi.")
