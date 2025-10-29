# Automated-Financial-Report-Export

## Tính năng
- Xuất báo cáo phân tích tài chính tự động (PDF) theo mã cổ phiếu.
- Giao diện Streamlit hiện đại, luồng chạy mượt, có lịch sử tải báo cáo gần đây.
- Tự động hóa đường dẫn bằng Pathlib, chạy được trên mọi máy không phụ thuộc đường dẫn tuyệt đối.
- Tách biệt cấu hình API Gemini qua `.env`/`.env.local`, không lộ khóa trên GitHub.

## Cài đặt nhanh
1) Tạo môi trường ảo và cài thư viện
```bash
pip install -r Back_end/requirements.txt
```

2) Cấu hình API Gemini an toàn (không commit)
- Cách 1: Tạo file `.env.local` ở thư mục gốc dự án:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```
- Cách 2: Đặt biến môi trường hệ thống `GEMINI_API_KEY` (Windows PowerShell):
```powershell
[System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY','your_gemini_api_key_here','User')
```

3) Chạy ứng dụng
```bash
streamlit run Back_end/main.py
```

## Cấu trúc chính
- `Back_end/paths.py`: Trung tâm hóa đường dẫn (Data, output, fonts...).
- `Back_end/main.py`: Giao diện Streamlit và luồng chạy 6 bước.
- `Back_end/report_generator.py`: Tạo PDF (font nhúng, hình ảnh, bảng số liệu, phân tích AI).
- `Back_end/data_processor.py`: Đọc Excel cleaned và xử lý dữ liệu.
- `Back_end/financial_statement.py`: Chuẩn hóa bảng và xuất Excel ra `Data/Data_store`.
- `Back_end/chart.py`, `Back_end/indicator.py`: Tính chỉ báo, vẽ và lưu biểu đồ.
- `Back_end/ai_analyst.py`: Gọi Gemini thông qua biến `GEMINI_API_KEY`.

## Nguyên tắc bảo mật khóa API
- Dự án đọc `GEMINI_API_KEY` từ `.env.local` (ưu tiên) hoặc `.env`, hoặc biến môi trường.
- `.gitignore` đã chặn `.env*` và các file sinh ra. Không commit khóa API.

## Cài đặt Font (Bắt buộc cho tiếng Việt)

**Vấn đề:** Báo cáo PDF cần font DejaVu để hiển thị tiếng Việt đúng.

**Giải pháp nhanh - Tự động download:**
```bash
cd Back_end
python install_fonts_auto.py
```

Hoặc (cần xác nhận):
```bash
cd Back_end
python download_fonts.py
```

**Hoặc download thủ công:**
1. Tải DejaVu fonts từ: https://dejavu-fonts.github.io/Download.html
2. Giải nén và copy các file `.ttf` vào: `Back_end/assets/fonts/`
3. Cần 4 file: `DejaVuSans.ttf`, `DejaVuSans-Bold.ttf`, `DejaVuSans-Oblique.ttf`, `DejaVuSans-BoldOblique.ttf`

**Lưu ý:** Nếu không có font, hệ thống sẽ tự động fallback về Helvetica (không hỗ trợ tiếng Việt tốt).

Chi tiết xem: `Back_end/FONT_SETUP.md`

## Gợi ý lỗi thường gặp
- **Font error / tiếng Việt hiển thị sai**: Cài đặt DejaVu fonts theo hướng dẫn ở trên.
- **File dữ liệu không tồn tại**: Kiểm tra thư mục `Data/` đúng vị trí và tên file.
- **Thiếu GEMINI_API_KEY**: Tạo `.env.local` hoặc đặt biến môi trường như hướng dẫn.
