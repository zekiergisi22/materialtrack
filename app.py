import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. SAYFA VE GÖRÜNÜM AYARLARI ---
st.set_page_config(page_title="MOL-OCU Tedarik Yönetimi", page_icon="🏗️", layout="wide")

st.title("🏗️ MOL-OCU Malzeme Tedarik ve Veri Yönetim Sistemi")

# --- 2. GOOGLE SHEETS BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Mevcut veriyi çek
    df = conn.read(ttl=0)
    df = df.dropna(how="all")
    df.columns = df.columns.str.strip()

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
    st.stop()

# --- 3. YAN MENÜ (NAVİGASYON) ---
menu = st.sidebar.selectbox(
    "Ana Menü - İşlem Seçiniz", 
    ["📊 Dashboard (İzleme)", "📝 Yeni Malzeme Ekle", "✏️ Verileri Düzenle / Sil"]
)

st.sidebar.divider()
st.sidebar.info("💡 **Bilgi:** Bu sistemdeki tüm veriler Google Sheets dosyanızla anlık olarak senkronizedir.")

# =======================================================
# MODÜL 1: DASHBOARD (İZLEME) - YENİLENMİŞ VERSİYON
# =======================================================
if menu == "📊 Dashboard (İzleme)":
    
    # --- KATEGORİ (ANA GRUP) SEÇİMİ ---
    ana_gruplar = ["🌟 Genel Görünüm (Overall)"] # Varsayılan ilk seçenek
    if 'Ana_Grup' in df.columns:
        # Veritabanındaki benzersiz grupları alıp listeye ekle
        ana_gruplar.extend(df['Ana_Grup'].dropna().unique().tolist())
    
    # Kullanıcı seçimi
    secilen_grup = st.selectbox("📂 İncelemek İstediğiniz Kategoriyi Seçiniz:", ana_gruplar)
    
    # --- VERİYİ SEÇİME GÖRE FİLTRELEME ---
    if secilen_grup == "🌟 Genel Görünüm (Overall)":
        gosterilecek_df = df.copy()
        st.subheader("Tüm Projenin Anlık Durumu")
    else:
        gosterilecek_df = df[df['Ana_Grup'] == secilen_grup].copy()
        st.subheader(f"Durum Özeti: {secilen_grup}")

    # --- DİNAMİK METRİKLER (Sadece filtrelenmiş veriye göre hesaplanır) ---
    pr_bekleyen = gosterilecek_df[(gosterilecek_df['Quotation_Status'].str.contains('Approved', case=False, na=False)) & (gosterilecek_df['PR_No'].str.strip() == '')]
    po_bekleyen = gosterilecek_df[(gosterilecek_df['PR_No'].str.strip() != '') & (gosterilecek_df['PO_No'].str.strip() == '')]
    sahaya_ulasan = gosterilecek_df[gosterilecek_df['Receiving_Pct'] >= 100] if 'Receiving_Pct' in gosterilecek_df.columns else pd.DataFrame()
    
    # Üst Metrik Kartları
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Kalem", len(gosterilecek_df))
    
    # Eğer eksik yoksa yeşil (normal), eksik varsa kırmızı (inverse) yansıtma mantığı
    pr_renk = "normal" if len(pr_bekleyen) == 0 else "inverse"
    po_renk = "normal" if len(po_bekleyen) == 0 else "inverse"
    
    c2.metric("PR Bekleyen", len(pr_bekleyen), delta="Sorun Yok" if len(pr_bekleyen)==0 else "Aksiyon Bekliyor", delta_color=pr_renk)
    c3.metric("PO Bekleyen", len(po_bekleyen), delta="Sorun Yok" if len(po_bekleyen)==0 else "Siparişe Dönüşmeli", delta_color=po_renk)
    c4.metric("Sahaya Ulaşan", len(sahaya_ulasan), delta="Teslim Alındı")
    
    st.divider()
    
    # --- DETAYLI ARAMA VE TABLO GÖSTERİMİ ---
    if secilen_grup == "🌟 Genel Görünüm (Overall)":
        st.markdown("**🔍 Tüm Veritabanında Arama Yapın**")
    else:
        st.markdown(f"**🔍 '{secilen_grup}' Kategorisinde Arama Yapın**")
        
    arama = st.text_input("Malzeme, Tedarikçi veya Sipariş Numarası arayın (Örn: Leser, Flange, PR-1001):")
    
    if arama:
        # Arama kelimesi varsa sadece onları göster
        mask = gosterilecek_df.apply(lambda row: row.astype(str).str.contains(arama, case=False, na=False).any(), axis=1)
        st.dataframe(gosterilecek_df[mask], use_container_width=True, hide_index=True)
    else:
        # Arama yoksa filtrelenmiş kategorinin tamamını göster
        st.dataframe(gosterilecek_df, use_container_width=True, hide_index=True)


# =======================================================
# MODÜL 2: YENİ VERİ GİRİŞİ
# =======================================================
elif menu == "📝 Yeni Malzeme Ekle":
    st.subheader("Sisteme Yeni Malzeme Kalemi Ekle")
    
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
    * 🗑️ **Silmek için:** Silmek istediğiniz satırın en solundaki gri kutucuğu seçip 'Delete' tuşuna veya çöp kutusu ikonuna basın.
    * 💾 İşleminiz bitince alttaki mavi renkli **Kaydet** butonuna basmayı unutmayın!
    """)
    
    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        num_rows="dynamic", 
        height=600
    )
    
    if st.button("💾 Değişiklikleri Google Sheets'e Kaydet", type="primary", use_container_width=True):
        with st.spinner("Değişiklikler Google Sheets'e aktarılıyor..."):
            conn.update(data=edited_df)
            st.success("✅ Tüm değişiklikleriniz başarıyla kaydedildi! Dashboard otomatik olarak güncellendi.")
