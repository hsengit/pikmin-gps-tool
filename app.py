import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import piexif
import io

# --- 頁面基本設定 (需放在腳本最上方) ---
st.set_page_config(page_title="皮克敏定位盆工具", page_icon="📍", layout="centered")

# --- CSS 介面美化與手機端優化注入 ---
st.markdown("""
<style>
/* 隱藏 Streamlit 預設選單與 Footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 全域背景漸層 */
.stApp {
    background: linear-gradient(135deg, #f1f8e9 0%, #e8f5e9 100%);
}

/* 解決手機深色模式輸入框變黑的問題：強制白底黑字 */
input[type="text"] {
    background-color: #ffffff !important;
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    border: 2px solid #81C784 !important;
    border-radius: 10px !important;
}

/* 上傳區塊極簡化：隱藏拖曳文字，只保留按鈕感 */
[data-testid="stFileUploadDropzone"] {
    background-color: #ffffff !important;
    border: 2px dashed #81C784 !important;
    border-radius: 15px !important;
}
[data-testid="stFileUploadDropzone"] > div > div > small,
[data-testid="stFileUploadDropzone"] > div > div > span {
    display: none !important;
}

/* 次要按鈕 (未點選的飾品類別)：淺綠底、深綠字，提高對比度 */
button[kind="secondary"] {
    background-color: #E8F5E9 !important;
    color: #1B5E20 !important;
    border: 1px solid #81C784 !important;
    border-radius: 12px !important;
    font-weight: bold !important;
    padding: 2px 5px !important;
    transition: all 0.2s !important;
}
button[kind="secondary"]:hover {
    background-color: #C8E6C9 !important;
}

/* 主要按鈕 (已點選的飾品類別、執行與下載按鈕)：深綠底、白字 */
button[kind="primary"] {
    background-color: #2E7D32 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: bold !important;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.2) !important;
    transition: all 0.2s !important;
}
button[kind="primary"]:hover {
    background-color: #1B5E20 !important;
    transform: translateY(-2px) !important;
}

/* --- 核心魔法：讓按鈕群組在手機端完美橫向換行 --- */
@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        flex-direction: row !important;
    }
    div[data-testid="column"] {
        width: auto !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
        padding-right: 0.2rem !important; 
        padding-left: 0.2rem !important;
    }
}

/* 文字與標題統一為深綠色 */
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

    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size
    
    if width >= height:
        new_width = 1024
        new_height = int(round(height * (1024 / width)))
    else:
        new_height = 1024
        new_width = int(round(width * (1024 / height)))
        
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    output_io = io.BytesIO()
    img_resized.save(output_io, format="jpeg", exif=exif_bytes)
    return output_io.getvalue()

# --- 網頁介面設計 ---
st.title("📍 皮克敏定位盆修改相片GPS")
st.markdown("**版本號**：v1.3 (全類別自適應版) &nbsp;|&nbsp; **製作者**：HSEN")
st.write("上傳 JPG 相片，快速修改 GPS 座標與屬性標籤，自動縮放長邊至 1024px。")

if "photo_attr_input" not in st.session_state:
    st.session_state.photo_attr_input = ""

uploaded_file = st.file_uploader("📂 點擊按鈕上傳相片", type=["jpg", "jpeg"])

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
    
    # --- 飾品類別全收錄與動態排版 ---
    categories_dict = {
        "🍔 餐飲類": ["餐廳", "咖啡廳", "甜點店", "漢堡店", "披薩店", "壽司店", "拉麵店"],
        "🛍️ 商店與購物類": ["便利商店", "超市", "麵包店", "理髮廳", "服飾店", "美妝店", "藥局", "電器行", "五金行"],
        "🏛️ 休閒與公共設施": ["電影院", "遊樂園", "動物園", "美術館", "圖書館", "書店", "郵局", "體育場", "飯店", "神社", "寺廟"],
        "🚉 交通類": ["車站", "公車站", "機場"],
        "🌳 自然景觀類": ["公園", "森林", "水邊", "海灘", "山", "橋樑"]
    }
    
    st.write("👉 **快速填入飾品類別：**")
    
    for group_name, cats in categories_dict.items():
        st.markdown(f"<div style='margin-top: 10px; margin-bottom: 5px; font-weight: bold; font-size: 14px; color: #1B5E20;'>{group_name}</div>", unsafe_allow_html=True)
        
        # 為了避免單行過擠，將類別依每 4~5 個切分成一行
        chunk_size = 5
        for i in range(0, len(cats), chunk_size):
            chunk = cats[i:i+chunk_size]
            
            # 【關鍵排版】依據每個字串的長度作為欄位寬度的比例，例如 [4, 2, 3] -> 依字數完美分配寬度
            cols = st.columns([len(c) for c in chunk])
            for j, cat in enumerate(chunk):
                with cols[j]:
                    btn_type = "primary" if st.session_state.photo_attr_input == cat else "secondary"
                    if st.button(cat, key=f"btn_{cat}", type=btn_type, use_container_width=True):
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
                        type="primary",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"處理失敗: {e}")