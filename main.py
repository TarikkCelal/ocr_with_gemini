from PIL import Image
from PIL import ImageOps
import pytesseract
import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')  # Model adını kontrol edin
    except Exception as e:
        st.error(f"Gemini modelini başlatırken bir hata oluştu: {e}")
        model = None
else:
    st.error("GEMINI_API_KEY ortam değişkeni bulunamadı. Lütfen .env dosyasını kontrol edin.")
    model = None

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.title("OCR ve Gemini ile Metin Temizleme")

uploaded_file = st.file_uploader("Bir görüntü dosyası yükleyin", type=["png", "jpg", "jpeg"])

def img2txt(image):
    try:
        metin = pytesseract.image_to_string(image, lang='tur')
        return metin
    except Exception as e:
        st.error(f"OCR sırasında bir hata oluştu: {e}")
        st.warning("Lütfen Tesseract'ın doğru şekilde kurulduğundan ve dil paketlerinin (tur) yüklendiğinden emin olun.")
        return None

if uploaded_file is not None:
    pil_image = Image.open(uploaded_file)
    st.image(pil_image, caption="Yüklenen Görüntü.", use_container_width=True)

    gri_tonlama_uygula = st.checkbox("Gri Tonlama Uygula")
    esikleme_uygula = st.checkbox("Eşikleme Uygula")

    processed_image = pil_image

    if gri_tonlama_uygula:
        processed_image = ImageOps.grayscale(processed_image)
        st.image(processed_image, caption="Gri Tonlamalı Görüntü.", use_container_width=True)

    if esikleme_uygula:
        esik_degeri = st.slider("Eşik Değeri", 0, 255, 128)
        processed_image = processed_image.point(lambda p: p > esik_degeri and 255)
        st.image(processed_image, caption=f"Eşiklenmiş Görüntü (Eşik: {esik_degeri}).", use_container_width=True)

    if st.button("OCR ve Temizle"):
        ocr_cikti = img2txt(processed_image)
        if ocr_cikti and model:  # Modelin başlatılıp başlatılmadığını kontrol et
            st.subheader("OCR Çıktısı:")
            st.text_area("Ham Metin", ocr_cikti, height=200)

            prompt = f"""
            Aşağıdaki metin bir görüntüden Optik Karakter Tanıma (OCR) ile çıkarılmıştır.
            Metindeki olası hataları düzeltin. Kelimelerin orijinal (Osmanlıca/Eski Türkçe) biçimini koruyun, günümüz Türkçesine çevirmeyin.
            Sadece OCR kaynaklı bariz hataları giderin (örneğin, sayı olarak algılanan harfleri düzeltin, anlamsız veya tekrar eden kelimeleri çıkarın).
            "assı" kelimesini "ısı" olarak veya "ağdı" kelimesini "ağacı" olarak değiştirmeyin; bu kelimelerin orijinal hallerini koruyun.
            Noktalama işaretleri eklemeyin.

            {ocr_cikti}
            """

            try:
                response = model.generate_content(prompt)
                temizlenmis_metin = response.text
                st.subheader("Temizlenmiş Metin (Gemini):")
                st.text_area("Düzeltilmiş Metin", temizlenmis_metin, height=200)
                st.session_state["temizlenmis_metin"] = temizlenmis_metin
            except Exception as e:
                st.error(f"Gemini API çağrısında bir hata oluştu: {e}")
        elif not model:
            st.warning("Gemini modeli başlatılamadığı için metin temizleme yapılamıyor.")
        else:
            st.warning("OCR sonuç alınamadı veya bir hata oluştu.")

else:
    st.info("Lütfen OCR ve temizleme için bir görüntü dosyası yükleyin.")