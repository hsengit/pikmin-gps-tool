import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import piexif
import io

# --- 頁面基本設定 (需放在腳本最上方) ---
st.set_page_config(page_title="皮克敏定位盆工具", page_icon="📍", layout="centered")

# --- CSS 介面美化注入 ---
st.markdown("""
<style>
/* 隱藏 Streamlit 預設的右上角選單與底部 Footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 全域背景漸層 (清新自然風) */
.stApp {
    background: linear-gradient(135deg, #f1f8e9 0%, #e8f5e9 100%);
}

/* 按鈕全域美化 (包含上傳按鈕與執行按鈕) */
.stButton > button, .stDownloadButton > button {
    background-color: #4CAF50 !important; /* 皮克敏綠 */
    color: white !important;
    border-radius: 20px !important;
    border: none !important;
    padding: 10px 24px !important;
    font-weight: bold !important;
    transition: all 0.3s ease 0s !important;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background-color: #45a049 !important;
    box-shadow: 0px 6px 15px rgba(0,0,0,0.2) !important;
    transform: translateY(-2px) !important;
}

/* 快捷類別小按鈕稍微調整，區分主次 */
div[data-testid="column"] .stButton > button {
    background-color: #81C784 !important;
    padding: 5px 10px !important;
    font-size: 14px !important;
    border-radius: 12px !important;
}
div[data-testid="column"] .stButton > button:hover {
    background-color: #66BB6A !important;
}

/* 文字輸入框美化 */
.stTextInput > div > div > input {
    border-radius: 10px !important;
    border: 2px solid #A5D6A7 !important;
    padding: 8px 12px !important;
}

/* 上傳區塊背景淡化並加上虛線圓角 */
.stFileUploader > div > div {
    background-color: rgba(255, 255, 255, 0.6) !important;
    border-radius: 15px !important;
    border: 2px dashed #81C784 !important;
}

/* 文字與標題顏色統一為深綠自然色 */
h1, h2, h3, p, span, label {
    color: #2E7D32 !important;
}
</style>
""", unsafe_allow_html=True)


def decimal_to_dms(decimal_degree):
    """將十進制度數轉換為 EXIF 格式所需的度、分、秒"""
    val = abs(decimal_degree)
    degrees = int(val)
    minutes = int((val - degrees) * 60)
    seconds = int(round(((val - degrees) * 60 - minutes) * 60 * 1000))
    return ((degrees, 1), (minutes, 1), (seconds, 1000))

def process_image(image_bytes, lat, lon):
    # 1. 處理 EXIF 定位資訊
    try:
        exif_dict = piexif.load(image_bytes)
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}

    lat_ref = "N" if lat >= 0 else "S"
    lon_ref = "E" if lon >= 0 else "W"

    exif_dict["GPS"][piexif.GPSIFD.GPSVersionID] = (2, 0, 0, 0)
    exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = lat_ref
    exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = decimal_to_dms(lat)
    exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = lon_ref
    exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = decimal_to_dms(lon)

    exif_bytes = piexif.dump(exif_dict)

    # 2. 讀取相片並縮放長邊至 1024 像素
    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size
    
    if width >= height:
        new_width = 1024
        new_height = int(round(height * (1024 / width)))
    else:
        new_height = 1024
        new_width = int(round(width * (1024 / height)))
        
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 3. 輸出
    output_io = io.BytesIO()
    img_resized.save(output_io, format="jpeg", exif=exif_bytes)
    return output_io.getvalue()

# --- 網頁介面設計 ---
st.title("📍 皮克敏定位盆修改相片GPS")
st.markdown("**版本號**：v1.1 (美化版) &nbsp;|&nbsp; **製作者**：HSEN")
st.write("上傳 JPG 相片，快速修改 GPS 座標與屬性標籤，自動縮放長邊至 1024px。")

if "photo_attr_input" not in st.session_state:
    st.session_state.photo_attr_input = ""

uploaded_file = st.file_uploader("📂 請選擇相片", type=["jpg", "jpeg"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="相片預覽", use_container_width=True)
    st.markdown("---")

    gps_coords = st.text_input("🌍 GPS座標 (緯度,經度)", value="22.9976,120.2023", help="格式請用逗號隔開")
    
    components.html("""
    <button id="paste-btn" style="
        padding: 8px 16px; 
        background-color: #ffffff; 
        color: #2E7D32; 
        border: 2px solid #81C784; 
        border-radius: 20px; 
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    ">📋 點擊直接貼上剪貼簿座標</button>
    <script>
    document.getElementById('paste-btn').addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            const inputs = window.parent.document.querySelectorAll('input');
            for (let input of inputs) {
                if (input.getAttribute('aria-label') === '🌍 GPS座標 (緯度,經度)') {
                    input.value = text.trim();
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    break;
                }
            }
        } catch (err) {
            alert('無法讀取剪貼簿，請允許權限。\\n錯誤: ' + err);
        }
    });
    </script>
    """, height=45)

    photo_attr = st.text_input("🏷️ 定位相片屬性", value=st.session_state.photo_attr_input, key="attr_field")
    
    categories = [
        "餐廳", "咖啡廳", "甜點店", "電影院", "藥局", 
        "動物園", "森林", "水邊", "郵局", "美術館", 
        "機場", "車站", "海灘", "迷你小品", "理髮廳"
    ]
    
    st.write("👉 **快速填入飾器類別：**")
    cols = st.columns(5)
    for i, cat in enumerate(categories):
        with cols[i % 5]:
            if st.button(cat, key=f"btn_{cat}", use_container_width=True):
                st.session_state.photo_attr_input = cat
                st.rerun()

    st.markdown("---")

    if st.button("🚀 開始處理相片", type="primary", use_container_width=True):
        try:
            lat_str, lon_str = gps_coords.split(",")
            lat = float(lat_str.strip())
            lon = float(lon_str.strip())
            valid_gps = True
        except ValueError:
            st.error("❌ GPS 座標格式錯誤！請確保是以逗號隔開的十進位數字")
            valid_gps = False

        if valid_gps:
            if not photo_attr:
                st.warning("⚠️ 尚未輸入「定位相片屬性」，檔名開頭將留白。")
            
            with st.spinner("正在施展魔法處理中... 🌱"):
                try:
                    processed_bytes = process_image(uploaded_file.getvalue(), lat, lon)
                    st.success("✅ 處理完成！長邊已縮為 1024px，EXIF 保留完畢。")

                    clean_gps_str = gps_coords.replace(" ", "")
                    download_filename = f"{photo_attr}_{clean_gps_str}.jpg"

                    st.download_button(
                        label="📥 下載專屬定位相片",
                        data=processed_bytes,
                        file_name=download_filename,
                        mime="image/jpeg",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"處理失敗: {e}")