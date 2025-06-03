# Automated-Financial-Report-Export
**1. Yêu cầu về các thư viện chính (đã liệt kê trong requirements.txt):**
requests
pandas
python-dotenv

**2. Cài đặt**
Clone repository
git clone https://github.com/username/Automated-Financial-Report-Export.git
cd Automated-Financial-Report-Export

**Tạo môi trường ảo (ví dụ venv)**
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows

**Cài đặt dependency**
pip install -r requirements.txt

**3. Cấu hình**
API Key Gemini
Đăng ký tài khoản tại https://www.gemini.com/ và tạo API Key.

**Tạo file .env ở thư mục gốc với nội dung:**
GEMINI_API_KEY=your_gemini_api_key_here

**Trong code, load bằng python-dotenv:**
from dotenv import load_dotenv
import os
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

**Cập nhật đường dẫn dữ liệu**
Trong các script, tìm dòng chú thích # Đường dẫn đến thư mục... và thay bằng đường dẫn tuyệt đối trên máy (ví dụ:
data_store_path = r"C:\Users\Nguyen Thi Son\Downloads\Automated Financial Report Export\Data\Data_store")
Tương tự với report_output_path trong export_report.py.

**4. Cấu trúc thư mục**
Automated Financial Report Export/
├── .env                      # Chứa GEMINI_API_KEY (không commit lên Git)
├── .gitignore                # Loại trừ .env và file không cần thiết khác
├── README.md                 # Hướng dẫn này
├── requirements.txt          # Thư viện Python cần cài
├── fetch_data.py             # Lấy dữ liệu thô từ Gemini API
├── process_data.py           # Xử lý, tổng hợp dữ liệu thành DataFrame
├── export_report.py          # Xuất báo cáo (Excel/CSV/PDF) vào output/reports/
├── utils/
│   ├── helpers.py            # Các hàm chung (load_env, convert_date,…)
│   └── constants.py          # Hằng số (URL Gemini API, tên bảng,…)
├── Data/
│   └── Data_store/           # Lưu trữ dữ liệu thô (CSV/JSON,…)
└── output/
    └── reports/              # Lưu báo cáo đầu ra


**5. Chức năng chính**
fetch_data.py

Kết nối tới Gemini API bằng GEMINI_API_KEY.

Tải dữ liệu tài chính (giá cổ phiếu, báo cáo tổng hợp,…) vào Data/Data_store/.

process_data.py

Đọc dữ liệu thô từ Data/Data_store/.

Làm sạch, tính toán các chỉ số cần thiết.

Trả về DataFrame cho bước xuất báo cáo.

export_report.py

Nhận DataFrame từ process_data.py.

Xuất báo cáo (Excel, CSV hoặc PDF) vào output/reports/.

utils/helpers.py

Chứa hàm chung: load .env, format ngày tháng, validate API Key,…

utils/constants.py

Định nghĩa các hằng số cố định (URL cơ bản Gemini API, tên bảng,…).


**6. Hướng dẫn sử dụng**

**Cấu hình**
Mở .env, thêm GEMINI_API_KEY.
Chỉnh lại tất cả biến đường dẫn (ví dụ data_store_path, report_output_path) thành đường dẫn tuyệt đối trên máy.

**Chạy lần lượt các script**
python fetch_data.py
python process_data.py
python export_report.py

**Kết quả**
Kiểm tra folder output/reports/ để lấy báo cáo đã xuất (PDF).

**7. Lưu ý**
.env: Không commit file này lên Git.

Đường dẫn: Mỗi máy có cấu trúc khác nhau, cần cập nhật đúng.

Debug: Nếu gặp lỗi “file not found”, kiểm tra lại biến *_path trong từng script.





