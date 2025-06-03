import os
import re
import glob
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import textwrap
from datetime import datetime
from fpdf import FPDF
from PyPDF2 import PdfMerger
from vnstock import Vnstock

# Import các module từ project của bạn
from financial_statement import financial_ratios_final
from data_processor import (
    industry_classification,
    get_company_overview_tcbs,
    get_company_profile_tcbs,
    get_executives_vci,
    get_subsidiaries_tcbs,
)
from ai_analyst import ask_gemini
from fundamental_analyst import calculate_stock_price, get_eps_bvps_2024, valuation_index

# ------------------- ĐỊNH NGHĨA ĐƯỜNG DẪN ------------------- #
FILEPATH = r"\Data\Data_store"

# ------------------- HÀM XỬ LÝ FILE EXCEL ------------------- #
def load_latest_file(stock_code, table_type, filepath):
    """
    Trả về file có tên chứa stock_code và table_type với định dạng:
      {stock_code}_{table_type}_{date}.xlsx
    Nếu có nhiều file, chọn file có ngày gần hiện tại nhất.
    """
    pattern = os.path.join(filepath, f"{stock_code}_{table_type}_*.xlsx")
    files = glob.glob(pattern)
    if not files:
        return None

    def extract_date(f):
        parts = os.path.basename(f).split("_")
        if len(parts) < 3:
            return None
        date_str = parts[-1].replace(".xlsx", "")
        try:
            return datetime.strptime(date_str, "%d%m%Y")
        except Exception:
            return None

    files_dates = [(f, extract_date(f)) for f in files if extract_date(f) is not None]
    if not files_dates:
        return None
    return max(files_dates, key=lambda x: x[1])[0]

def load_bs_table(stock_code, filepath):
    file = load_latest_file(stock_code, "bs", filepath)
    if not file:
        return pd.DataFrame()
    df = pd.read_excel(file, index_col=0)
    return df.drop("Mã cổ phiếu", errors='ignore')

def load_is_table(stock_code, filepath):
    file = load_latest_file(stock_code, "is", filepath)
    if not file:
        return pd.DataFrame()
    df = pd.read_excel(file, index_col=0)
    return df.drop("Mã cổ phiếu", errors='ignore')

def load_cf_table(stock_code, filepath):
    file = load_latest_file(stock_code, "cf", filepath)
    if not file:
        return pd.DataFrame()
    df = pd.read_excel(file, index_col=0)
    return df.drop("Mã cổ phiếu", errors='ignore')

def load_financial_ratios_table(stock_code, filepath):
    file = load_latest_file(stock_code, "financialratios", filepath)
    if not file:
        return pd.DataFrame()
    return pd.read_excel(file, index_col=0)

def df_to_table_data(df, years):
    table_data = {}
    for idx, row in df.iterrows():
        table_data[idx] = [str(row.get(str(year), "")) for year in years]
    return table_data

def convert_financial_ratios_table(df):
    """
    Chuyển đổi DataFrame của file "Chỉ số tài chính" sang định dạng:
                2020      2021      2022      2023      2024
    (Vay NH+DH)/VCSH    ...       ...       ...       ...       ...
    EPS (VND)           ...       ...       ...       ...       ...
    """
    df = df.drop("Phân loại", errors='ignore')
    df_new = df.transpose()
    desired_years = ["2020", "2021", "2022", "2023", "2024"]
    df_new.columns = [str(col) for col in df_new.columns]
    return df_new.reindex(columns=desired_years)

# ------------------- HÀM HIỂN THỊ PHƯƠNG PHÁP ĐỊNH GIÁ & TIN TỨC VĨ MÔ ------------------- #
def display_valuation_methodology(pdf):
    pdf.set_fill_color(0, 0, 128)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(0, 10, "Phương pháp định giá cổ phiếu dựa trên P/E và P/B", 0, 1, "C", fill=True)
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(0, 10, "Giới thiệu phương pháp:", 0, 1, "C")
    pdf.set_font("DejaVu", "", 8)
    explanation = (
        "Phương pháp P/E: Giá cổ phiếu = EPS * P/E (của ngành).\n"
        "Phương pháp P/B: Giá cổ phiếu = BVPS * P/B (của ngành).\n"
        "Giá định giá được tính bằng trung bình của 2 phương pháp, sau đó chia cho 1000."
    )
    pdf.multi_cell(0, 5, explanation)
    pdf.ln(3)

def display_macro_news(pdf, stock_code):
    macro_query = (
        f"Hiện tại đang có những tin tức vĩ mô gì ảnh hưởng đến {stock_code}? "
        "Trả lời bằng 5 gạch đầu dòng theo format 'Chủ đề: Nội dung', với chủ đề in đậm và giới hạn 600 chữ."
    )
    macro_news_text = ask_gemini(macro_query)
    pdf.set_fill_color(0, 0, 128)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(0, 10, "Phân tích tin tức vĩ mô ảnh hưởng đến cổ phiếu", 0, 1, "C", fill=True)
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", "", 8)
    pdf.multi_cell(0, 5, macro_news_text)
    pdf.ln(3)

# ------------------- LỚP PDF ------------------- #
class PDF(FPDF):
    def __init__(self, industry_info=None):
        super().__init__()
        self.industry_info = industry_info

    def add_section_header(self, title, align="L"):
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(0, 0, 128)
        self.cell(190, 10, title, border=0, ln=1, align=align, fill=True)
        self.ln(3)

    def header(self):
        # Phần thêm tiêu đề của trang header (nếu cần)
        font_path = r"C:\Users\Nguyen Thi Son\Downloads\Automation financial report exporting\Back_end"
        self.add_font("DejaVu", "", os.path.join(font_path, "DejaVuSans.ttf"), uni=True)
        self.add_font("DejaVu", "B", os.path.join(font_path, "DejaVuSans-Bold.ttf"), uni=True)
        self.add_font("DejaVu", "I", os.path.join(font_path, "DejaVuSans-Oblique.ttf"), uni=True)
        self.add_font("DejaVu", "BI", os.path.join(font_path, "DejaVuSans-BoldOblique.ttf"), uni=True)
        if self.industry_info is not None and not self.industry_info.empty:
            stock_code = self.industry_info.iloc[0].get("Mã", "")
            ten_cong_ty = self.industry_info.iloc[0].get("Tên công ty", "")
            san = self.industry_info.iloc[0].get("Sàn", "")
            nganh_icb_cap2 = self.industry_info.iloc[0].get("Ngành ICB - cấp 2", "")
        else:
            stock_code = "UNKNOWN"
            ten_cong_ty = "UNKNOWN"
            san = ""
            nganh_icb_cap2 = ""
        today = datetime.today()
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, f"{stock_code.upper()} ({san})", 0, 1, 'L')
        self.set_font("DejaVu", "", 8)
        self.cell(0, 6, f"{ten_cong_ty} - {nganh_icb_cap2}", 0, 1, 'L')
        self.cell(0, 5, f"Ngày xuất báo cáo: {today.strftime('%d/%m/%y')}", 0, 1, 'L')
        report_time = datetime.now().strftime("%H:%M")
        self.cell(0, 5, f"Thời gian xuất báo cáo: {report_time}", 0, 1, 'L')
        self.set_fill_color(0, 0, 128)
        self.set_draw_color(0, 0, 128)
        self.set_line_width(0.5)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(3)

    def footer(self):
        self.set_y(-10)
        self.set_fill_color(0, 0, 128)
        self.rect(0, self.get_y(), self.w, 10, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVu", "", 8)
        self.set_y(-7)
        self.cell(0, 5, f'Trang {self.page_no()} / {{nb}}', 0, 1, 'C')

    def basic_information(self, overview_df, profile_df):
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(0, 0, 128)
        self.cell(190, 10, "Thông tin cơ bản", border=0, ln=1, align="L", fill=True)
        self.ln(3)
        overview = overview_df.iloc[0] if not overview_df.empty else {}
        profile = profile_df.iloc[0] if not profile_df.empty else {}
        info_list = [
            ("Trang chủ công ty", overview.get("website", "")),
            ("Ngày thành lập", profile.get("history_dev", "")),
            ("Chìa khoá phát triển", profile.get("key_developments", "")),
            ("Rủi ro kinh doanh", profile.get("business_risk", "")),
            ("Chiến lược kinh doanh", profile.get("business_strategies", "")),
            ("Số lượng cổ đông", overview.get("no_shareholders", "")),
            ("Số lượng nhân viên", overview.get("no_employees", ""))
        ]
        for header_text, value in info_list:
            self.set_x(10)
            self.set_font("DejaVu", "B", 10)
            self.set_text_color(0, 0, 0)
            self.cell(0, 6, header_text, border=0, ln=1, align="L")
            self.set_x(10)
            self.set_font("DejaVu", "", 8)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 5, str(value), border=0, align="L")
            self.ln(4)

    def create_executives_table(self, executives_df):
        self.add_section_header("Ban lãnh đạo", align="L")
        col_width = 190 / 4
        headers = ["Tên cán bộ", "Tên chức vụ rút gọn", "Tỷ lệ sở hữu", "Số lượng"]
        
        # Vẽ tiêu đề bảng (không dùng border)
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(0, 0, 0)
        table_top = self.get_y()
        x0 = self.get_x()
        for header in headers:
            self.cell(col_width, 7, header, border=0, align="L")
        self.ln(7)
        
        self.set_font("DejaVu", "", 8)
        self.set_text_color(0, 0, 0)
        
        # Duyệt từng dòng dữ liệu
        for idx, row in executives_df.iterrows():
            x0 = self.get_x()
            y0 = self.get_y()
            texts = [
                str(row["officer_name"]),
                str(row["position_short_name"]),
                str(row["officer_own_percent"]),
                str(row["quantity"])
            ]
            
            # Pass 1: Tính chiều cao cần thiết của từng ô (không vẽ border)
            cell_heights = []
            for text in texts:
                x_temp = self.get_x()
                y_temp = self.get_y()
                self.multi_cell(col_width, 5, text, border=0, align="L")
                cell_heights.append(self.get_y() - y_temp)
                self.set_xy(x_temp + col_width, y_temp)
            row_height = max(cell_heights)
            
            # Pass 2: Vẽ nội dung cho mỗi ô với cùng chiều cao (không vẽ border)
            self.set_xy(x0, y0)
            for text in texts:
                x_cell = self.get_x()
                y_cell = self.get_y()
                self.multi_cell(col_width, 5, text, border=0, align="L")
                drawn = self.get_y() - y_cell
                if drawn < row_height:
                    self.set_xy(x_cell, self.get_y())
                    self.cell(col_width, row_height - drawn, "", border=0)
                self.set_xy(x_cell + col_width, y_cell)
            # Di chuyển con trỏ xuống dòng tiếp theo
            self.set_xy(x0, y0 + row_height)
            self.ln(3)
        table_bottom = self.get_y()


    def create_company_info_table2(self, subsidiaries_df):
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(0, 0, 128)
        self.cell(190, 10, "Danh sách công ty con, liên kết", border=0, ln=1, align="L", fill=True)
        self.ln(5)
        
        if subsidiaries_df.empty:
            self.set_font("DejaVu", "", 8)
            self.set_text_color(0, 0, 0)
            self.cell(190, 6, "Không có thông tin công ty con.", border=0, ln=1, align="L")
            return

        col_width = 190 / 2
        headers = ["Tên công ty con", "Tỷ lệ sở hữu"]
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(0, 0, 0)
        table_top = self.get_y()
        x0 = self.get_x()
        # Vẽ tiêu đề bảng (không dùng border)
        for header in headers:
            self.cell(col_width, 6, header, border=0, align="L")
        self.ln(6)
        
        self.set_font("DejaVu", "", 8)
        self.set_text_color(0, 0, 0)
        
        # Duyệt từng dòng dữ liệu
        for idx, row in subsidiaries_df.iterrows():
            x0 = self.get_x()
            y0 = self.get_y()
            text1 = str(row["sub_company_name"])
            text2 = str(row["sub_own_percent"])
            texts = [text1, text2]
            
            # Pass 1: Tính chiều cao cần thiết cho từng ô (không dùng border)
            cell_heights = []
            for text in texts:
                x_temp = self.get_x()
                y_temp = self.get_y()
                self.multi_cell(col_width, 5, text, border=0, align="L")
                cell_heights.append(self.get_y() - y_temp)
                self.set_xy(x_temp + col_width, y_temp)
            row_height = max(cell_heights)
            
            # Pass 2: Vẽ nội dung cho mỗi ô với cùng chiều cao (không dùng border)
            self.set_xy(x0, y0)
            for text in texts:
                x_cell = self.get_x()
                y_cell = self.get_y()
                self.multi_cell(col_width, 5, text, border=0, align="L")
                drawn = self.get_y() - y_cell
                if drawn < row_height:
                    self.set_xy(x_cell, self.get_y())
                    self.cell(col_width, row_height - drawn, "", border=0)
                self.set_xy(x_cell + col_width, y_cell)
            # Di chuyển con trỏ xuống dòng tiếp theo
            self.set_xy(x0, y0 + row_height)
            self.ln(3)
        table_bottom = self.get_y()



    def create_table(self, title, data, years):
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(255, 255, 255)
        page_width = 210 - 20
        col_width = page_width * 0.35
        year_width = (page_width * 0.65) / len(years)
        self.set_x(10)
        self.set_fill_color(0, 0, 128)
        self.cell(col_width, 6, title, 0, 0, "L", fill=True)
        for year in years:
            self.cell(year_width, 6, year, 0, 0, "R", fill=True)
        self.ln()
        self.set_x(10)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(0, 0, 0)
        row_count = 0
        for key, values in data.items():
            if row_count % 2 == 0:
                self.set_fill_color(230, 240, 250)
            else:
                self.set_fill_color(255, 255, 255)
            self.cell(col_width, 6, key, 0, 0, "L", fill=True)
            for value in values:
                self.cell(year_width, 6, value, 0, 0, "R", fill=True)
            self.ln()
            row_count += 1
        self.ln(5)

# ------------------- HÀM XỬ LÝ ẢNH ------------------- #
def extract_date_from_filename(file):
    """
    Trích xuất ngày (dạng ddmmyyyy) từ tên file.
    Giả sử tên file có dạng: {stock_code}_{pattern_suffix}_{date}.png
    """
    base = os.path.basename(file)
    parts = base.split("_")
    if len(parts) < 3:
        return None
    date_str = parts[-1].replace(".png", "")
    try:
        return datetime.strptime(date_str, "%d%m%Y")
    except Exception:
        return None

def get_latest_file(stock_code, pattern_suffix, filepath):
    """
    Tìm file có tên: {stock_code}_{pattern_suffix}_{date}.png trong filepath,
    chọn file có ngày gần với ngày hiện tại nhất nếu có nhiều file trùng mã.
    """
    pattern = os.path.join(filepath, f"{stock_code}_{pattern_suffix}_*.png")
    files = glob.glob(pattern)
    if not files:
        return None

    today = datetime.today()
    best_file = None
    best_diff = None
    for f in files:
        file_date = extract_date_from_filename(f)
        if file_date is None:
            continue
        diff = abs((today - file_date).days)
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_file = f
    return best_file

def generate_image_groups(pdf, stock_code, filepath):
    """
    Với mã cổ phiếu và đối tượng PDF cùng đường dẫn chứa file, hàm tìm kiếm, in tiêu đề 
    "Phân tích kỹ thuật" và phân nhóm các file PNG:
      - Nhóm 1 (ảnh 1): Top 5 cổ đông
      - Nhóm 2 (ảnh 2 đến ảnh 7): Các chỉ số phân tích kỹ thuật (6 file)
      - Nhóm 3 (ảnh 8 đến ảnh 15): Các chỉ số đánh giá doanh nghiệp (7 hoặc 8 file)
    """
    # In tiêu đề "Phân tích kỹ thuật" lên PDF
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(0, 0, 128)
    pdf.cell(190, 10, "Phân tích kỹ thuật", border=0, ln=1, align="C", fill=True)
    pdf.ln(5)
    
    # Nhóm 1: Top 5 cổ đông
    group1_pattern = "plot_top_shareholders"
    group1_file = get_latest_file(stock_code, group1_pattern, filepath)
    group1 = [group1_file] if group1_file else []

    # Nhóm 2: Các chỉ số phân tích kỹ thuật (6 file)
    group2_patterns = [
        "draw_normalized_linegraph",
        "draw_volume_comparison",
        "plot_indicator_charts_1",
        "plot_indicator_charts_2",
        "plot_indicator_charts_3",
        "plot_indicator_charts_4",
    ]
    group2 = []
    for pattern in group2_patterns:
        f = get_latest_file(stock_code, pattern, filepath)
        if f:
            group2.append(f)

    # Nhóm 3: Các chỉ số đánh giá doanh nghiệp (7 hoặc 8 file)
    group3_patterns = [
        "draw_chart_1",
        "draw_chart_2",
        "draw_chart_3",
        "draw_chart_4",
        "draw_chart_5",
        "draw_chart_6",
        "draw_chart_7",
    ]
    group3 = []
    for pattern in group3_patterns:
        f = get_latest_file(stock_code, pattern, filepath)
        if f:
            group3.append(f)

    return group1, group2, group3

# ------------------- HÀM XUẤT DỮ LIỆU TEXT ------------------- #
def export_text_data(pdf, stock_code, overview_df, profile_df, executives_df, subsidiaries_df, bs_data, is_data, cf_data, fr_data, years):
    pdf.basic_information(overview_df, profile_df)
    pdf.create_executives_table(executives_df)
    pdf.create_company_info_table2(subsidiaries_df)
    pdf.create_table("Cân đối kế toán", bs_data, years)
    pdf.create_table("Kết quả kinh doanh", is_data, years)
    pdf.create_table("Lưu chuyển tiền tệ", cf_data, years)
    pdf.create_table("Chỉ số tài chính", fr_data, years)

# ------------------- HÀM TẠO BÁO CÁO ------------------- #
def generate_stock_report(stock_code):
    industry_info = industry_classification(stock_code)
    overview_df = get_company_overview_tcbs(stock_code)
    profile_df = get_company_profile_tcbs(stock_code)
    subsidiaries_df = get_subsidiaries_tcbs(stock_code)

    bs_df = load_bs_table(stock_code, FILEPATH)
    is_df = load_is_table(stock_code, FILEPATH)
    cf_df = load_cf_table(stock_code, FILEPATH)
    fr_df = load_financial_ratios_table(stock_code, FILEPATH)
    fr_df_converted = convert_financial_ratios_table(fr_df)

    years = ["2020", "2021", "2022", "2023", "2024"]
    bs_data = df_to_table_data(bs_df, years)
    is_data = df_to_table_data(is_df, years)
    cf_data = df_to_table_data(cf_df, years)
    fr_data = df_to_table_data(fr_df_converted, years)

    executives_df = get_executives_vci(stock_code, filter_by='working')

    # Tạo đối tượng PDF
    pdf = PDF(industry_info=industry_info)
    pdf.alias_nb_pages()
    pdf.add_page()

    introduction_query = f"Hãy giới thiệu về mã cổ phiếu {stock_code.upper()}, giới hạn 100 từ."
    introduction_text = ask_gemini(introduction_query)
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Giới thiệu", 0, 1, "L")
    pdf.ln(2)
    pdf.set_font("DejaVu", "", 8)
    pdf.multi_cell(0, 5, introduction_text)
    pdf.ln(5)

    export_text_data(pdf, stock_code, overview_df, profile_df, executives_df,
                     subsidiaries_df, bs_data, is_data, cf_data, fr_data, years)
    display_valuation_methodology(pdf)
    
    # Lấy giá trị EPS và BVPS (giả sử từ DataFrame đã xử lý, ví dụ fr_df_converted)
    eps_value, bvps_value = get_eps_bvps_2024(stock_code)
    if eps_value is None or bvps_value is None:
        print("Lỗi lấy giá trị EPS/BVPS từ file tỷ số tài chính.")
        eps_value, bvps_value = 0, 0

    # Lấy chỉ số định giá ngành bằng hàm valuation_index
    industry_pe, industry_pb = valuation_index(stock_code)
    if industry_pe is None or industry_pb is None:
        print("Không lấy được chỉ số ngành")
        

    # Bước 3: Tính giá cổ phiếu định giá sử dụng hàm calculate_stock_price
    valuation_price = calculate_stock_price(eps_value, bvps_value, industry_pe, industry_pb)
    print(f"Giá cổ phiếu định giá (trung bình P/E và P/B): {valuation_price:.3f} VND")
    
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(0, 10, "Mức giá sau khi sử dụng kết hợp P/E và P/B", 0, 1, "L")
    pdf.set_font("DejaVu", "", 8)
    pdf.cell(0, 10, f"Giá cổ phiếu định giá: {valuation_price:.3f} (VND)", 0, 1, "L")
    pdf.ln(5)
    
    display_macro_news(pdf, stock_code)
    
    # ----------------- CHÈN ẢNH VÀO PHẦN DƯỚI CÙNG BÁO CÁO ----------------- #
    group1, group2, group3 = generate_image_groups(pdf, stock_code, FILEPATH)

    # Nhóm 1: Top 5 cổ đông
    if group1:
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(0, 10, "Nhóm 1: Top 5 cổ đông", 0, 1, "L")
        pdf.ln(3)
        for image_path in group1:
            pdf.image(image_path, x=10, w=pdf.w - 20)
            pdf.ln(3)

    # Nhóm 2: Các chỉ số phân tích kỹ thuật (6 file)
    if group2:
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(0, 10, "Nhóm 2: Các chỉ số phân tích kỹ thuật", 0, 1, "L")
        pdf.ln(3)
        for image_path in group2:
            pdf.image(image_path, x=10, w=pdf.w - 20)
            pdf.ln(3)

    # Nhóm 3: Các chỉ số đánh giá doanh nghiệp (7 hoặc 8 file)
    if group3:
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(0, 10, "Nhóm 3: Các chỉ số đánh giá doanh nghiệp", 0, 1, "L")
        pdf.ln(3)
        for image_path in group3:
            pdf.image(image_path, x=10, w=pdf.w - 20)
            pdf.ln(3)
    # ---------------------------------------------------------------------- #
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"Report_{stock_code.upper()}_{timestamp}.pdf"
    export_dir = r"\Data\Report_export"
    os.makedirs(export_dir, exist_ok=True)
    output_path = os.path.join(export_dir, filename)
    pdf.output(output_path, 'F')
    print(f"✅ Report saved to: {output_path}")

