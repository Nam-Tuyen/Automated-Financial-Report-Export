# 📊 Hệ Thống Xuất Báo Cáo Phân Tích Cổ Phiếu Tự Động

Hệ thống tự động tạo báo cáo phân tích tài chính chuyên nghiệp cho các mã cổ phiếu Việt Nam với giao diện web hiện đại và tích hợp AI.

## ✨ Tính năng chính

- 📈 **Phân tích tài chính tự động**: Xử lý và phân tích báo cáo tài chính từ file Excel
- 🤖 **Tích hợp AI (Gemini)**: Tự động phân tích xu hướng, rủi ro và khuyến nghị đầu tư
- 📊 **Chỉ báo kỹ thuật**: SMA, Bollinger Bands, RSI, MACD
- 📉 **Biểu đồ phân tích**: Tự động vẽ và xuất các biểu đồ kỹ thuật
- 📑 **Báo cáo PDF chuyên nghiệp**: Tạo báo cáo PDF đầy đủ với định dạng chuyên nghiệp
- 🎨 **Giao diện hiện đại**: Web UI với Streamlit, dark theme, autocomplete
- 💾 **Cache thông minh**: Giảm API calls và tăng tốc độ xử lý

## 📁 Cấu trúc thư mục

```
Back_end/
├── main.py                    # Ứng dụng Streamlit chính
├── report_generator.py        # Generator báo cáo PDF
├── data_processor.py          # Xử lý dữ liệu tài chính
├── financial_statement.py     # Xử lý báo cáo tài chính
├── indicator.py               # Tính toán chỉ báo kỹ thuật
├── fundamental_analyst.py     # Phân tích định giá cơ bản
├── chart.py                   # Vẽ biểu đồ
├── ai_analyst.py              # Core AI engine (Gemini)
├── ai_sections.py             # Single-call AI orchestrator
├── ai_cache.py                # Hệ thống cache thông minh
├── paths.py                   # Quản lý đường dẫn
├── helpers_fonts.py            # Helper functions cho fonts
│
├── docs/                      # Tài liệu dự án
│   ├── QUICK_START.md         # Hướng dẫn nhanh
│   ├── AI_V3_SINGLE_CALL_GUIDE.md
│   ├── REPORT_V2_GUIDE.md
│   └── ...
│
├── tests/                     # Test files
│   ├── test_report_v2.py
│   └── test_font_setup.py
│
├── utils/                     # Utility scripts
│   ├── download_fonts.py
│   └── install_fonts_auto.py
│
├── assets/                    # Tài nguyên
│   └── fonts/                 # Fonts DejaVu
│
└── requirements.txt           # Dependencies
```

## 🚀 Cài đặt

### 1. Yêu cầu hệ thống

- Python 3.8 trở lên
- Windows/Linux/macOS
- Git (optional)

### 2. Cài đặt dependencies

```bash
cd Back_end
pip install -r requirements.txt
```

### 3. Cấu hình API Key

Tạo file `.env` trong thư mục gốc của project:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Hoặc set biến môi trường:

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

**Linux/macOS:**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 4. Kiểm tra fonts

Fonts DejaVu được bundle sẵn trong `assets/fonts/`. Nếu gặp vấn đề, chạy:

```bash
python utils/install_fonts_auto.py
```

Hoặc test font setup:

```bash
python tests/test_font_setup.py
```

### 5. Chuẩn bị dữ liệu

Đảm bảo cấu trúc thư mục `Data/` như sau:

```
Data/
├── Data cleaned/              # File Excel đã làm sạch
│   └── Phan_loai_nganh(cleaned).xlsx
├── Data raw/                  # File dữ liệu thô
│   ├── FT2325.csv
│   └── market_index.xlsx
├── Data_store/                # File Excel đầu vào (tự động tạo)
│   └── {STOCK_CODE}_{TYPE}_{DATE}.xlsx
└── Report_export/             # Báo cáo PDF xuất ra (tự động tạo)
    └── Report_{STOCK_CODE}_{TIMESTAMP}.pdf
```

## 💻 Sử dụng

### Chạy ứng dụng

Từ thư mục gốc của project:

```bash
streamlit run Back_end/main.py
```

Ứng dụng sẽ mở tự động tại `http://localhost:8501`

### Quy trình tạo báo cáo

1. **Nhập mã cổ phiếu**
   - Gõ mã cổ phiếu (ví dụ: HPG, DGW, VNM, GEX)
   - Sử dụng autocomplete để tìm mã
   - Click vào gợi ý hoặc nhấn Enter

2. **Nhấn "Tạo Báo Cáo"**
   - Hệ thống sẽ thực hiện 6 bước tự động:
     - ✅ Bước 1: Xử lý dữ liệu từ file Excel
     - ✅ Bước 2: Xử lý báo cáo tài chính
     - ✅ Bước 3: Tính toán chỉ báo kỹ thuật
     - ✅ Bước 4: Vẽ và xuất biểu đồ
     - ✅ Bước 5: Phân tích định giá
     - ✅ Bước 6: Tạo báo cáo tổng hợp

3. **Tải báo cáo PDF**
   - Sau khi hoàn tất, báo cáo sẽ tự động hiển thị nút tải xuống
   - File PDF được lưu tại: `Data/Report_export/Report_{STOCK_CODE}_{TIMESTAMP}.pdf`

## 📋 Các module chính

### 1. `main.py` - Streamlit Application
- Giao diện web với Streamlit
- Xử lý input từ người dùng
- Quản lý workflow 6 bước
- Hiển thị progress và kết quả

### 2. `report_generator.py` - PDF Generator
- Tạo báo cáo PDF chuyên nghiệp
- Tích hợp AI phân tích
- Format và layout chuyên nghiệp
- Hỗ trợ tiếng Việt đầy đủ

### 3. `data_processor.py` - Data Processing
- Xử lý file Excel tài chính
- Lấy thông tin công ty từ TCBS/VCI
- Phân loại ngành
- Xử lý cân đối kế toán, kết quả kinh doanh, dòng tiền

### 4. `financial_statement.py` - Financial Analysis
- Tính toán các chỉ số tài chính
- Xuất báo cáo tài chính ra Excel
- Phân tích tỷ số tài chính

### 5. `indicator.py` - Technical Indicators
- SMA (Simple Moving Average)
- Bollinger Bands
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)

### 6. `fundamental_analyst.py` - Valuation
- Tính EPS, BVPS
- Định giá dựa trên P/E, P/B ngành
- Tính giá cổ phiếu mục tiêu

### 7. `chart.py` - Chart Generation
- Vẽ biểu đồ giá
- Biểu đồ chỉ báo kỹ thuật
- Export hình ảnh

### 8. `ai_analyst.py` - AI Engine
- Tích hợp Google Gemini API
- Xử lý prompt và response
- Error handling và retry logic

### 9. `ai_sections.py` - AI Orchestrator
- Single-call architecture (V3)
- Gom tất cả AI sections vào 1 JSON call
- Tiết kiệm 80% API quota
- Cache thông minh

### 10. `ai_cache.py` - Smart Caching
- RAM + Disk dual-layer cache
- Context-based hashing
- Cache invalidation thông minh

## 🔧 Cấu hình

### Cấu hình đường dẫn (`paths.py`)

Tất cả đường dẫn được quản lý tập trung:

```python
DATA_DIR = PROJECT_ROOT / "Data"
DATA_CLEANED_DIR = DATA_DIR / "Data cleaned"
DATA_RAW_DIR = DATA_DIR / "Data raw"
DATA_STORE_DIR = DATA_DIR / "Data_store"
REPORT_EXPORT_DIR = DATA_DIR / "Report_export"
FONTS_DIR = BACKEND_DIR / "assets" / "fonts"
```

### Cấu hình AI

Các tham số AI có thể điều chỉnh trong `ai_sections.py`:
- Model version
- Temperature
- Max tokens
- Retry attempts
- Cache TTL

## 🐛 Xử lý lỗi thường gặp

### 1. Lỗi: "DejaVu fonts not found"

**Giải pháp:**
```bash
python utils/install_fonts_auto.py
```

### 2. Lỗi: "GEMINI_API_KEY not found"

**Giải pháp:**
- Tạo file `.env` với `GEMINI_API_KEY=your_key`
- Hoặc set biến môi trường

### 3. Lỗi: "Module not found"

**Giải pháp:**
```bash
pip install -r requirements.txt
```

### 4. Lỗi: "File Excel not found"

**Giải pháp:**
- Đảm bảo file Excel được đặt đúng trong `Data/Data_store/`
- Format tên file: `{STOCK_CODE}_{bs|is|cf}_{DDMMYYYY}.xlsx`

### 5. Lỗi encoding trong console

**Giải pháp:**
- Code đã tự động fix encoding cho Windows
- Nếu vẫn lỗi, restart terminal

### 6. Lỗi API quota (429)

**Giải pháp:**
- Hệ thống tự động retry với exponential backoff
- Kiểm tra quota API key
- Cache sẽ giúp giảm số lượng calls

## 📚 Tài liệu tham khảo

Xem thêm trong thư mục `docs/`:
- `QUICK_START.md` - Hướng dẫn nhanh
- `AI_V3_SINGLE_CALL_GUIDE.md` - Hướng dẫn AI V3
- `REPORT_V2_GUIDE.md` - Hướng dẫn cấu trúc báo cáo
- `FONT_SETUP.md` - Chi tiết về font setup

## 🔄 Quy trình phát triển

### Testing

```bash
# Test font setup
python tests/test_font_setup.py

# Test report generation
python tests/test_report_v2.py
```

### Development

1. Chỉnh sửa code trong các module tương ứng
2. Test với một số mã cổ phiếu
3. Kiểm tra output PDF
4. Commit changes

## 📝 Changelog

### Version 3.0 (Current)
- ✨ Single-call AI architecture
- 🚀 Cache system thông minh
- 📊 Compact report layout
- ⚡ Tăng tốc độ xử lý 5x
- 💰 Tiết kiệm 80% API quota

### Version 2.0
- 🤖 Tích hợp AI Analyst
- 📑 Cấu trúc báo cáo mới
- 🎨 UI/UX cải thiện

### Version 1.0
- 📊 Báo cáo tài chính cơ bản
- 📈 Technical indicators
- 📉 Charts

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra phần "Xử lý lỗi thường gặp"
2. Xem logs trong console
3. Kiểm tra file trong `docs/` để biết thêm chi tiết

## 📄 License

Dự án này sử dụng fonts DejaVu (license trong `assets/fonts/DejaVu Fonts License.txt`).

## 🙏 Credits

- **Streamlit** - Web framework
- **FPDF** - PDF generation
- **Google Gemini** - AI analysis
- **vnstock** - Vietnam stock data
- **DejaVu Fonts** - Font support for Vietnamese

---

**Last Updated:** 2025-01-30  
**Status:** ✅ Production Ready

