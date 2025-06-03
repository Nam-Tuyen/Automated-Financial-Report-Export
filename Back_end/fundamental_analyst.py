# fundamental_analyst.py

import os
import re
import pandas as pd
from data_processor import get_financial_ratios_vci, industry_classification
from financial_statement import financial_ratios_final

def get_eps_bvps_2024(stock_code):
    """
    Lấy ra EPS (VND) và BVPS (VND) năm 2024 từ file Excel được lưu trong đường dẫn FILEPATH.
    File có định dạng: {stock_code}_financialratios_{ngày tháng năm xuất ra}.xlsx.
    Nếu có nhiều file, chọn file có ngày gần hiện tại nhất.
    Sau đó, lấy giá trị từ ô nằm ở dòng "2024" và cột "EPS (VND)" (lưu vào eps_float)
    và cột "BVPS (VND)" (lưu vào bvps_float).
    Nếu không tìm thấy dữ liệu, trả về (None, None).
    """
    import os
    import glob
    from datetime import datetime
    import pandas as pd

    FILEPATH = r"\Data\Data_store"
    pattern = os.path.join(FILEPATH, f"{stock_code}_financialratios_*.xlsx")
    files = glob.glob(pattern)
    
    if not files:
        print(f"Không tìm thấy file tỷ số tài chính cho mã {stock_code} trong {FILEPATH}.")
        return None, None

    # Hàm phụ: trích xuất ngày từ tên file với định dạng ddmmyyyy
    def extract_date(filename):
        basename = os.path.basename(filename)
        parts = basename.split("_")
        if len(parts) < 3:
            return None
        date_str = parts[-1].replace(".xlsx", "")
        try:
            return datetime.strptime(date_str, "%d%m%Y")
        except Exception:
            return None

    # Lấy file có ngày xuất gần hiện tại nhất
    files_with_dates = [(f, extract_date(f)) for f in files if extract_date(f) is not None]
    if not files_with_dates:
        print("Không trích xuất được ngày từ tên file tỷ số tài chính.")
        return None, None

    # Chọn file có ngày lớn nhất (gần hiện tại nhất)
    best_file, best_date = max(files_with_dates, key=lambda x: x[1])
    print(f"Đang sử dụng file tỷ số tài chính: {best_file}")

    # Đọc file Excel với index là 0
    df = pd.read_excel(best_file, index_col=0)
    
    # Kiểm tra xem có dòng "2024" và các cột "EPS (VND)" và "BVPS (VND)" không
    if "2024" not in df.index:
        print("Không tìm thấy dòng năm 2024 trong file tỷ số tài chính.")
        return None, None
    if "EPS (VND)" not in df.columns or "BVPS (VND)" not in df.columns:
        print("Không tìm thấy cột 'EPS (VND)' hoặc 'BVPS (VND)' trong file tỷ số tài chính.")
        return None, None

    # Lấy giá trị từ ô, loại bỏ dấu phẩy và chuyển đổi sang float
    eps_str = df.loc["2024", "EPS (VND)"]
    bvps_str = df.loc["2024", "BVPS (VND)"]
    try:
        eps_float = float(eps_str.replace(',', ''))
        bvps_float = float(bvps_str.replace(',', ''))
    except Exception as e:
        print("Lỗi chuyển đổi EPS/BVPS sang float:", e)
        return None, None

    return eps_float, bvps_float


import os
import pandas as pd
import unicodedata

def valuation_index(stock_code):
    """
    Lấy chỉ số định giá của ngành của cổ phiếu dựa vào thông tin phân loại ngành và chỉ số ngành.
    
    Các bước:
      1. Gọi hàm industry_classification(stock_code) để lấy thông tin phân loại ngành của cổ phiếu.
      2. Lấy giá trị của cột "Ngành ICB - cấp 2" làm tên ngành.
      3. Đọc file Excel chứa chỉ số ngành từ đường dẫn:
         "\\Data\\Data raw\\Chỉ_số_ngành.xlsx"
      4. Đối chiếu với cột "Ngành" trong file Excel để tìm dòng phù hợp.
      5. Lấy ra giá trị "P/E" và "P/B" của ngành đó và trả về.
      
    Nếu không tìm thấy thông tin, trả về (None, None).
    """

    # Hàm nội bộ: Loại bỏ dấu khỏi chuỗi để chuẩn hóa so sánh
    def remove_accents(text):
        try:
            text = unicodedata.normalize('NFD', text)
            text = ''.join([char for char in text if unicodedata.category(char) != 'Mn'])
            return text
        except Exception as e:
            return text

    # Bước 1: Lấy thông tin phân loại ngành của cổ phiếu
    df_class = industry_classification(stock_code)
    if df_class.empty or "Ngành ICB - cấp 2" not in df_class.columns:
        print(f"Không tìm thấy thông tin phân loại ngành cho cổ phiếu {stock_code}.")
        return None, None

    # Lấy tên ngành và chuẩn hóa (loại dấu và chuyển về chữ thường)
    industry = df_class["Ngành ICB - cấp 2"].iloc[0].strip()
    industry_normalized = remove_accents(industry).lower()
    
    # Bước 2: Đọc file Excel chứa chỉ số ngành
    file_path = os.path.join(
        "\\Data\\Data raw",
        "Chỉ_số_ngành.xlsx"
    )
    if not os.path.exists(file_path):
        print(f"File chỉ số ngành không tồn tại: {file_path}")
        return None, None

    try:
        df_index = pd.read_excel(file_path)
        # Loại bỏ khoảng trắng thừa ở tên cột và chuẩn hóa cột "Ngành"
        df_index.columns = df_index.columns.str.strip()
        df_index["Ngành"] = df_index["Ngành"].astype(str).str.strip()
        # Thêm cột chuẩn hoá tên ngành trong file (loại bỏ dấu, chuyển về chữ thường)
        df_index["Ngành_normalized"] = df_index["Ngành"].apply(lambda x: remove_accents(x).lower())
    except Exception as e:
        print(f"Lỗi khi đọc file chỉ số ngành: {e}")
        return None, None

    def find_col(df, target):
        target = target.strip().upper()
        for col in df.columns:
            if col.strip().upper() == target:
                return col
        return None

    # Xác định cột chứa số liệu P/E và P/B
    pe_col = find_col(df_index, "P/E ngành")
    pb_col = find_col(df_index, "P/B ngành")
    
    if pe_col is None or pb_col is None:
        print("Không tìm thấy cột định giá P/E hoặc P/B trong file chỉ số ngành.")
        return None, None

    # Bước 3: Đối chiếu ngành bằng cách so sánh chuỗi đã chuẩn hóa
    df_filtered = df_index[df_index["Ngành_normalized"] == industry_normalized]
    if df_filtered.empty:
        print(f"Không tìm thấy dữ liệu chỉ số ngành cho ngành: {industry}")
        return None, None

    try:
        pe_industry = df_filtered[pe_col].iloc[0]
        pb_industry = df_filtered[pb_col].iloc[0]
        # Chuyển đổi kiểu dữ liệu nếu là chuỗi có dấu phẩy
        if isinstance(pe_industry, str):
            pe_industry = float(pe_industry.replace(",", "."))
        if isinstance(pb_industry, str):
            pb_industry = float(pb_industry.replace(",", "."))
    except Exception as e:
        print(f"Lỗi chuyển đổi giá trị định giá: {e}")
        return None, None

    return pe_industry, pb_industry


def calculate_stock_price(eps, bvps, industry_pe, industry_pb):
    """
    Tính giá cổ phiếu dựa trên 2 phương pháp:
      - Phương pháp P/E: Giá = EPS * P/E (của ngành)
      - Phương pháp P/B: Giá = BVPS * P/B (của ngành)
      
    Sau đó, lấy trung bình của 2 kết quả trên làm giá cổ phiếu định giá,
    chia kết quả cho 1000.
    
    Parameters:
      eps (float or str): Lợi nhuận trên mỗi cổ phiếu (EPS) của công ty.
      bvps (float or str): Giá trị sổ sách trên mỗi cổ phiếu (BVPS) của công ty.
      industry_pe (float): Tỷ số P/E trung bình của ngành.
      industry_pb (float): Tỷ số P/B trung bình của ngành.
    
    Returns:
      float: Giá cổ phiếu định giá theo trung bình của 2 phương pháp, sau khi chia cho 1000.
    """
    try:
        eps = float(eps)
        bvps = float(bvps)
    except Exception as e:
        print("Lỗi chuyển EPS/BVPS sang float:", e)
        return None

    price_pe = eps * industry_pe
    price_pb = bvps * industry_pb
    stock_price = (price_pe + price_pb) / 2
    stock_price_converted = stock_price / 1000  # Chia cho 1000
    return stock_price_converted

