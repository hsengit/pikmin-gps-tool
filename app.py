import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import piexif
import io

def decimal_to_dms(decimal_degree):
    """將十進制度數轉換為 EXIF 格式所需的度、分、秒 (有理數 tuple)"""
    val = abs(decimal_degree)
    degrees = int(val)
    minutes = int((val - degrees) * 60)
    seconds = int(round(((val - degrees) * 60 - minutes) * 60 * 1000))
    return ((degrees, 1), (minutes, 1), (seconds, 1000))

def process_image(image_bytes, lat, lon):
    # 1. 處理 EXIF 定位資訊 (保留其它所有 EXIF)
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

    # 2. 讀取相片並進行等比例縮放 (長邊固定為 1024 像素)
    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size
    
    if width >= height:
        new_width = 1024
        new_height = int(round(height * (1024 / width)))
    else:
        new_height = 1024
        new_width = int(round(width * (1024 / height)))
        
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 3. 儲存並寫入更新後的 EXIF 資訊
    output_io = io.BytesIO()
    img_resized.save(output_io, format="jpeg", exif=exif_bytes)
    return output_io.getvalue()

# --- 網頁介面設計 ---
st.title("📍 皮克敏定位盆修改相片GPS")

# 加入版本號與製作者資訊
st.markdown("**版本號**：v1.0 (2026-06-23) &nbsp;|&nbsp; **製作者**：HSEN")

st.write("上傳 JPG 相片，快速修改 GPS 座標與屬性標籤，自動縮放長邊至 1024px。")

# 初始化分頁屬性狀態
if "photo_attr_input" not in st.session_state:
    st.session_state.photo_attr_input = ""

uploaded_file = st.file_uploader("請選擇相片", type=["jpg", "jpeg"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="相片預覽", use_container_width=True)
    st.markdown("---")

    # --- 欄位 1：GPS 座標輸入與剪貼簿按鈕 ---
    gps_coords = st.text_input("GPS座標 (緯度,經度)", value="22.9976,120.2023", help="格式請用逗號隔開，例如：22.9976,120.2023")
    
    # 透過前端 JavaScript 讀取瀏覽器剪貼簿，並精準填入 Streamlit 的輸入框中
    components.html("""
    <button id="paste-btn" style="
        padding: 6px 12px; 
        background-color: #f0f2f6; 
        color: #31333f; 
        border: 1px solid rgba(49, 51, 63, 0.2); 
        border-radius: 4px; 
        cursor: pointer;
        font-size: 14px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    ">📋 點擊直接貼上剪貼簿資料</button>
    <script>
    document.getElementById('paste-btn').addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            const inputs = window.parent.document.querySelectorAll('input');
            let found = false;
            for (let input of inputs) {
                if (input.getAttribute('aria-label') === 'GPS座標 (緯度,經度)') {
                    input.value = text.trim();
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    found = true;
                    break;
                }
            }
            if (!found) alert('未找到座標輸入欄位，請手動貼上。');
        } catch (err) {
            alert('無法讀取剪貼簿，請確保已授權瀏覽器讀取剪貼簿權限。\\n錯誤: ' + err);
        }
    });
    </script>
    """, height=40)

    st.markdown(" ")

    # --- 欄位 2：定位相片屬性與快捷按鈕 ---
    photo_attr = st.text_input("定位相片屬性", value=st.session_state.photo_attr_input, key="attr_field")
    
    # 皮克敏飾器類別快捷按鈕
    categories = [
        "餐廳", "咖啡廳", "甜點店", "電影院", "藥局", 
        "動物園", "森林", "水邊", "郵局", "美術館", 
        "機場", "車站", "海灘", "迷你小品", "理髮廳"
    ]
    
    st.write("👉 點擊下方按鈕快速填入類別：")
    cols = st.columns(5)
    for i, cat in enumerate(categories):
        with cols[i % 5]:
            if st.button(cat, key=f"btn_{cat}", use_container_width=True):
                st.session_state.photo_attr_input = cat
                st.rerun() # 立即重整網頁以連動更新上方輸入框

    st.markdown("---")

    # --- 欄位 3：執行處理與下載 ---
    if st.button("🚀 開始處理相片", type="primary"):
        # 驗證 GPS 格式
        try:
            lat_str, lon_str = gps_coords.split(",")
            lat = float(lat_str.strip())
            lon = float(lon_str.strip())
            valid_gps = True
        except ValueError:
            st.error("❌ GPS 座標格式錯誤！請確保是以逗號隔開的十進位數字 (例如: 22.9976,120.2023)")
            valid_gps = False

        if valid_gps:
            if not photo_attr:
                st.warning("⚠️ 您尚未輸入「定位相片屬性」，下載的檔名開頭將會留白。")
            
            with st.spinner("正在修改 EXIF 資訊並等比例縮放圖片..."):
                try:
                    image_bytes = uploaded_file.getvalue()
                    # 執行影像處理與 EXIF 寫入
                    processed_bytes = process_image(image_bytes, lat, lon)
                    st.success("✅ 相片處理完成！其它 EXIF 資訊已完整保留，長邊已縮小為 1024 像素。")

                    # 格式化自訂下載名稱： 定位相片屬性_GPS座標.jpg
                    clean_gps_str = gps_coords.replace(" ", "")
                    download_filename = f"{photo_attr}_{clean_gps_str}.jpg"

                    # 下載按鈕
                    st.download_button(
                        label="📥 下載修改後的相片",
                        data=processed_bytes,
                        file_name=download_filename,
                        mime="image/jpeg"
                    )
                except Exception as e:
                    st.error(f"處理相片時發生未知錯誤: {e}")