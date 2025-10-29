import os
import sys
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

# Fix encoding for Windows console
if sys.platform == "win32":
    import codecs
    try:
        # Check if stdout needs encoding fix
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding not in ['utf-8', 'UTF-8', None]:
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        # Check if stderr needs encoding fix
        if hasattr(sys.stderr, 'encoding') and sys.stderr.encoding not in ['utf-8', 'UTF-8', None]:
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, TypeError):
        # If already wrapped or in special environment (like Streamlit), skip
        pass

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
from ai_sections import get_ai_sections, build_trend_data
from fundamental_analyst import calculate_stock_price, get_eps_bvps_2024, valuation_index
from pathlib import Path
from paths import DATA_STORE_DIR, REPORT_EXPORT_DIR, FONTS_DIR
from paths import (
    FONT_SANS_REG, FONT_SANS_BOLD, FONT_SANS_ITAL, FONT_SANS_BI,
    FONT_SANS_XL, FONT_COND_REG, FONT_COND_BOLD, FONT_COND_ITAL, FONT_COND_BI
)
from helpers_fonts import ensure_fonts_exist, system_fallback_font

# ------------------- ĐỊNH NGHĨA ĐƯỜNG DẪN ------------------- #
FILEPATH = str(DATA_STORE_DIR.resolve())

# ------------------- MÀU SẮC CHUYÊN NGHIỆP ------------------- #
COLOR_PRIMARY = (0, 51, 102)      # Navy blue
COLOR_SECONDARY = (0, 102, 153)   # Light blue
COLOR_ACCENT = (255, 153, 0)      # Orange
COLOR_SUCCESS = (34, 139, 34)     # Green
COLOR_WARNING = (255, 165, 0)     # Orange
COLOR_DANGER = (220, 20, 60)      # Red
COLOR_LIGHT_BG = (245, 247, 250)  # Light gray background
COLOR_TABLE_HEADER = (70, 130, 180)  # Steel blue

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
    df = pd.read_excel(file, index_col=0, engine='openpyxl')
    return df.drop("Mã cổ phiếu", errors='ignore')

def load_is_table(stock_code, filepath):
    file = load_latest_file(stock_code, "is", filepath)
    if not file:
        return pd.DataFrame()
    df = pd.read_excel(file, index_col=0, engine='openpyxl')
    return df.drop("Mã cổ phiếu", errors='ignore')

def load_cf_table(stock_code, filepath):
    file = load_latest_file(stock_code, "cf", filepath)
    if not file:
        return pd.DataFrame()
    df = pd.read_excel(file, index_col=0, engine='openpyxl')
    return df.drop("Mã cổ phiếu", errors='ignore')

def load_financial_ratios_table(stock_code, filepath):
    file = load_latest_file(stock_code, "financialratios", filepath)
    if not file:
        return pd.DataFrame()
    return pd.read_excel(file, index_col=0, engine='openpyxl')

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

# ------------------- HÀM LẤY KEY METRICS ------------------- #
def get_key_metrics(fr_df, bs_df, is_df):
    """Trích xuất các chỉ số quan trọng nhất từ financial ratios."""
    metrics = {}
    
    if not fr_df.empty:
        try:
            # Lấy năm 2024 (dòng cuối cùng hoặc index 2024)
            if "2024" in fr_df.index:
                row_2024 = fr_df.loc["2024"]
            elif len(fr_df) > 0:
                row_2024 = fr_df.iloc[-1]
            else:
                row_2024 = pd.Series()
            
            metrics["ROE"] = row_2024.get("ROE (%)", "N/A")
            metrics["ROA"] = row_2024.get("ROA (%)", "N/A")
            metrics["EPS"] = row_2024.get("EPS (VND)", "N/A")
            metrics["BVPS"] = row_2024.get("BVPS (VND)", "N/A")
            metrics["P/E"] = row_2024.get("P/E", "N/A")
            metrics["P/B"] = row_2024.get("P/B", "N/A")
            metrics["ROE"] = row_2024.get("ROE (%)", "N/A")
            metrics["Nợ/VCSH"] = row_2024.get("Nợ/VCSH", "N/A")
        except Exception as e:
            print(f"Error extracting key metrics: {e}")
    
    return metrics

# ------------------- HÀM PHÂN TÍCH TỪ GEMINI ------------------- #
def extract_month_year(founding_date_text):
    """
    Rút trích Month/Year từ chuỗi ngày thành lập.
    
    Args:
        founding_date_text: Chuỗi chứa thông tin ngày thành lập
    
    Returns:
        str: Format "Month/Year" hoặc "N/A" nếu không tìm thấy
    """
    if not founding_date_text or founding_date_text == "N/A":
        return "N/A"
    
    text = str(founding_date_text)
    
    # Danh sách tháng tiếng Anh
    months_en = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12'
    }
    
    # Danh sách tháng tiếng Việt
    months_vi = {
        'tháng 1': '01', 'tháng 2': '02', 'tháng 3': '03', 'tháng 4': '04',
        'tháng 5': '05', 'tháng 6': '06', 'tháng 7': '07', 'tháng 8': '08',
        'tháng 9': '09', 'tháng 10': '10', 'tháng 11': '11', 'tháng 12': '12'
    }
    
    # Pattern 1: "Month Year" (ví dụ: "March 2004")
    pattern1 = re.search(r'(\w+)\s+(\d{4})', text, re.IGNORECASE)
    if pattern1:
        month_str = pattern1.group(1).lower()
        year = pattern1.group(2)
        if month_str in months_en:
            month = months_en[month_str]
            return f"{month}/{year}"
    
    # Pattern 2: "MM/YYYY" hoặc "MM-YYYY"
    pattern2 = re.search(r'(\d{1,2})[/-](\d{4})', text)
    if pattern2:
        month = pattern2.group(1).zfill(2)
        year = pattern2.group(2)
        return f"{month}/{year}"
    
    # Pattern 3: "YYYY-MM-DD" hoặc "YYYY/MM/DD"
    pattern3 = re.search(r'(\d{4})[/-](\d{1,2})', text)
    if pattern3:
        year = pattern3.group(1)
        month = pattern3.group(2).zfill(2)
        return f"{month}/{year}"
    
    # Pattern 4: Chỉ có năm, lấy năm đầu tiên tìm thấy
    pattern4 = re.search(r'(\d{4})', text)
    if pattern4:
        year = pattern4.group(1)
        # Thử tìm tháng
        for month_vi, month_num in months_vi.items():
            if month_vi in text.lower():
                return f"{month_num}/{year}"
        # Nếu không có tháng, chỉ trả về năm
        return f"{year}"
    
    return "N/A"

def get_company_introduction(stock_code, company_name, founding_date, initial_capital, ask_gemini_fn):
    """
    Lấy giới thiệu về công ty bằng Gemini AI viết theo mẫu chuyên nghiệp (khoảng 150 chữ).
    
    Args:
        stock_code: Mã cổ phiếu
        company_name: Tên công ty
        founding_date: Ngày thành lập (raw text, có thể chứa đầy đủ thông tin)
        initial_capital: Vốn điều lệ khi thành lập
        ask_gemini_fn: Hàm gọi Gemini
    
    Returns:
        str: Giới thiệu về công ty (khoảng 150 chữ) viết theo mẫu chuyên nghiệp
    """
    fallback = f"{company_name} (mã chứng khoán {stock_code}) được thành lập vào {founding_date if founding_date else 'N/A'} với vốn điều lệ ban đầu {initial_capital}. Công ty đã phát triển qua nhiều giai đoạn và hiện có vị thế vững chắc trên thị trường chứng khoán Việt Nam."
    
    prompt = f"""Viết giới thiệu về công ty {company_name} (mã chứng khoán {stock_code}) theo MẪU THAM KHẢO dưới đây:

MẪU THAM KHẢO:
"Công ty Cổ phần Tập đoàn Gelex (mã chứng khoán GEX) khởi nguồn từ Tổng Công ty Thiết bị kỹ thuật điện được thành lập vào ngày 27 tháng 10 năm 1995 theo Quyết định của Bộ Công nghiệp nặng (nay là Bộ Công Thương). Trải qua hơn một thập kỷ hoạt động theo mô hình Tổng Công ty Nhà nước, Gelex chính thức chuyển đổi thành Tổng Công ty Cổ phần Thiết bị điện Việt Nam vào ngày 01 tháng 12 năm 2010, sau đợt IPO thành công tại HNX.

Kể từ khi Bộ Công Thương thoái toàn bộ vốn vào cuối năm 2015, công ty đã đẩy mạnh quá trình tái cấu trúc và phát triển mạnh mẽ. Đặc biệt, Gelex đã thực hiện nhiều đợt tăng vốn điều lệ ấn tượng, củng cố vị thế trên thị trường. Công ty chính thức niêm yết trên Sở Giao dịch Chứng khoán TP. Hồ Chí Minh (HOSE) từ đầu năm 2018. Bước ngoặt quan trọng là việc đổi tên thành Công ty Cổ phần Tập đoàn Gelex vào ngày 24 tháng 6 năm 2021, đánh dấu sự mở rộng sang mô hình Tập đoàn đa ngành. Đến tháng 9 năm 2024, vốn điều lệ của Tập đoàn đã đạt mức 8.594,29 tỷ đồng, khẳng định vị thế là một trong những tập đoàn kinh tế hàng đầu Việt Nam."

YÊU CẦU VIẾT:
1. BẮT ĐẦU: "{company_name} (mã chứng khoán {stock_code}) khởi nguồn từ... được thành lập vào ngày [dd] tháng [mm] năm [yyyy]..." (nếu có đầy đủ thông tin, nếu không thì chỉ dùng thông tin có sẵn)
2. MÔ TẢ LỊCH SỬ: Các giai đoạn phát triển, chuyển đổi, IPO, niêm yết, đổi tên (nếu có thông tin)
3. KẾT THÚC: Vốn điều lệ hiện tại (nếu có) và vị thế trên thị trường

THÔNG TIN CÓ SẴN:
- Ngày thành lập (thông tin gốc): {founding_date if founding_date else 'N/A'}
- Vốn điều lệ khi thành lập: {initial_capital if initial_capital else 'N/A'}

LƯU Ý:
- Độ dài KHOẢNG 150 chữ (không quá 160 chữ)
- Format ngày tháng: "ngày [dd] tháng [mm] năm [yyyy]" (ví dụ: ngày 27 tháng 10 năm 1995)
- Nếu không có ngày đầy đủ, dùng format: "tháng [mm] năm [yyyy]" hoặc chỉ "năm [yyyy]"
- Viết tiếng Việt, chuyên nghiệp, có cấu trúc thời gian rõ ràng
- Nếu không có đủ thông tin lịch sử, tập trung vào thông tin cơ bản và vị thế hiện tại
- Tự tìm kiếm thông tin công khai về lịch sử phát triển, IPO, niêm yết nếu có"""
    
    intro_text = ask_gemini_fn(prompt, fallback_content=fallback)
    
    # Đảm bảo không quá dài (trim nếu cần)
    if len(intro_text) > 160:
        # Tìm câu cuối phù hợp để cắt
        sentences = intro_text.split('.')
        trimmed = ""
        for i, sent in enumerate(sentences):
            if len(trimmed + sent + '.') <= 157:
                trimmed += sent + '.'
            else:
                break
        if trimmed:
            intro_text = trimmed.strip()
        else:
            intro_text = intro_text[:157] + "..."
    
    return intro_text

def get_company_mission(stock_code, company_name, website, ask_gemini_fn):
    """
    Lấy sứ mệnh và triết lý kinh doanh bằng Gemini AI (3-4 dòng).
    
    Args:
        stock_code: Mã cổ phiếu
        company_name: Tên công ty
        website: Website công ty
        ask_gemini_fn: Hàm gọi Gemini
    
    Returns:
        str: Sứ mệnh và triết lý kinh doanh (3-4 dòng)
    """
    fallback = f"{company_name} cam kết mang lại giá trị bền vững cho khách hàng, cổ đông và cộng đồng thông qua chất lượng dịch vụ và sản phẩm vượt trội. Công ty theo đuổi triết lý phát triển bền vững, đổi mới sáng tạo và tối đa hóa hiệu quả kinh doanh."
    
    prompt = f"""Viết về sứ mệnh và triết lý kinh doanh của {company_name} (mã cổ phiếu: {stock_code}), khoảng 3-4 dòng:
1. Sứ mệnh của công ty
2. Triết lý kinh doanh
3. Giá trị cốt lõi hoặc cam kết

Website: {website} (tham khảo nếu cần)

Viết tiếng Việt, ngắn gọn, chuyên nghiệp, dựa trên thông tin công khai."""
    
    return ask_gemini_fn(prompt, fallback_content=fallback)

def get_executive_summary(stock_code, industry_info, key_metrics):
    """Lấy investment snapshot ngắn gọn (thay thế Executive Summary)."""
    industry_name = ""
    company_name = ""
    if not industry_info.empty:
        industry_name = industry_info.iloc[0].get("Ngành ICB - cấp 2", "")
        company_name = industry_info.iloc[0].get("Tên công ty", stock_code)
    
    # Tạo fallback từ dữ liệu thực
    roe = key_metrics.get("ROE", "N/A")
    eps = key_metrics.get("EPS", "N/A")
    pb = key_metrics.get("P/B", "N/A")
    
    fallback = f"{company_name} hoạt động trong lĩnh vực {industry_name}. "
    if roe != "N/A":
        fallback += f"ROE đạt {roe}, "
    if eps != "N/A":
        fallback += f"EPS {eps} VND. "
    fallback += "Công ty có vị thế vững chắc trong ngành với hệ thống phân phối rộng và thương hiệu uy tín."
    
    metrics_str = ", ".join([f"{k}: {v}" for k, v in list(key_metrics.items())[:5] if v != "N/A"])
    
    prompt = f"""Viết tóm tắt đầu tư cho {stock_code} trong {industry_name}, tối đa 5 dòng:
1. Vị thế công ty trong ngành
2. Điểm mạnh tài chính nổi bật (dựa trên: {metrics_str})
3. Triển vọng ngắn hạn

Viết tiếng Việt, ngắn gọn, đi thẳng vào vấn đề."""
    
    return ask_gemini(prompt, fallback_content=fallback)

def get_industry_analysis(stock_code, industry_info):
    """Lấy phân tích ngành ngắn gọn (bỏ - không dùng trong bản mới)."""
    # Bản mới không có phần này - loại bỏ theo checklist
    return None

def get_swot_analysis(stock_code, industry_info, overview_df, key_metrics):
    """Lấy phân tích SWOT ngắn gọn (bỏ - không dùng trong bản mới)."""
    # Bản mới không có SWOT dài - loại bỏ theo checklist
    return None

# DEPRECATED - Không dùng nữa, đã thay bằng get_ai_sections()
# def get_risk_assessment(...): ...

# DEPRECATED - Không dùng nữa, đã thay bằng get_ai_sections()
# def get_investment_recommendation(...): ...

# DEPRECATED - Không dùng nữa, đã thay bằng get_ai_sections()
# def get_financial_trend_analysis(...): ...

# ------------------- LỚP PDF CẢI TIẾN ------------------- #
class PDF(FPDF):
    _fonts_registered = False
    _has_dejavu = False  # Track if DejaVu fonts are available
    
    def __init__(self, industry_info=None):
        super().__init__()
        self.industry_info = industry_info
        # COMPACT LAYOUT: Giảm margins từ 15mm xuống 10mm
        self.set_margins(left=10, top=10, right=10)
        self.set_auto_page_break(auto=True, margin=10)
        
        # Register fonts once per class (not per instance)
        if not PDF._fonts_registered:
            self._register_fonts()
            PDF._fonts_registered = True

    def _register_fonts(self):
        """Register all DejaVu fonts for FPDF (cross-platform compatible)."""
        # Define font paths mapping
        font_paths = {
            "": FONT_SANS_REG,
            "B": FONT_SANS_BOLD,
            "I": FONT_SANS_ITAL,
            "BI": FONT_SANS_BI,
        }
        
        # Validate and resolve font paths
        resolved = ensure_fonts_exist(font_paths)
        registered = 0
        registered_styles = []
        
        # Register each valid font with uni=True for Unicode support
        for style, abs_path in resolved.items():
            try:
                # CRITICAL: uni=True is required for Vietnamese characters
                # Verify file exists before registering
                if not os.path.exists(abs_path):
                    print(f"[ERROR] Font file does not exist: {abs_path}")
                    continue
                
                # Register font - style can be empty string for regular, "B" for bold, etc.
                self.add_font("DejaVu", style, abs_path, uni=True)
                registered += 1
                registered_styles.append(style if style else "Regular")
                print(f"[FONT] Registered DejaVu{style if style else 'Regular'} from {os.path.basename(abs_path)}")
            except Exception as e:
                print(f"[ERROR] Cannot register DejaVu{style} ({abs_path}): {e}")
                import traceback
                traceback.print_exc()
        
        # Handle fallback
        if registered == 0:
            # CRITICAL: Cannot use Helvetica for Vietnamese
            PDF._has_dejavu = False
            print("\n" + "="*70)
            print("❌ CRITICAL ERROR: No Unicode fonts available!")
            print("="*70)
            print("Vietnamese text CANNOT be rendered without DejaVu fonts.")
            print("\nPlease install fonts using one of these methods:")
            print("\n1. AUTO-INSTALL:")
            print("   cd Back_end")
            print("   python utils/install_fonts_auto.py")
            print("\n2. MANUAL INSTALL:")
            print("   Download: https://dejavu-fonts.github.io/Download.html")
            print("   Extract and copy .ttf files to: Back_end/assets/fonts/")
            print("="*70 + "\n")
            raise RuntimeError(
                "Cannot generate PDF with Vietnamese text without Unicode fonts. "
                "Please install DejaVu fonts first."
            )
        else:
            PDF._has_dejavu = True
            # Verify all required styles are registered
            required_styles = ["", "B"]  # At minimum need Regular and Bold
            missing_styles = [s for s in required_styles if s not in resolved.keys() or (s if s else "") not in [rs if rs != "Regular" else "" for rs in registered_styles]]
            
            if missing_styles:
                style_names = {"": "Regular", "B": "Bold", "I": "Italic", "BI": "Bold Italic"}
                missing_names = [style_names.get(s, s) for s in missing_styles]
                print(f"[WARN] Missing font styles: {', '.join(missing_names)}")
            
            print(f"[FONT] Successfully registered {registered}/{len(font_paths)} DejaVu fonts: {', '.join(registered_styles)}")
    
    def set_font(self, family, style="", size=0):
        """
        Override set_font with proper Unicode support check.
        
        CRITICAL: Vietnamese text requires DejaVu fonts with uni=True.
        Do NOT fallback to Helvetica as it cannot render Vietnamese.
        """
        try:
            # CRITICAL: If requesting DejaVu but not available, STOP immediately
            if family == "DejaVu" and not PDF._has_dejavu:
                raise RuntimeError(
                    "DejaVu fonts not available but required for Vietnamese text. "
                    "Please install fonts: python Back_end/utils/install_fonts_auto.py"
                )
            
            # Verify font is registered before setting
            if family == "DejaVu":
                # FPDF requires the font to be registered with add_font before use
                # Try to set font, catch "Undefined font" errors
                try:
                    super().set_font(family, style, size)
                except Exception as font_error:
                    error_str = str(font_error)
                    if "Undefined font" in error_str or "dejavu" in error_str.lower():
                        # Font not registered properly - this should not happen if registration worked
                        print(f"[WARN] Font DejaVu{style if style else 'Regular'} not registered, checking...")
                        # Verify the font file exists
                        font_paths = {
                            "": FONT_SANS_REG,
                            "B": FONT_SANS_BOLD,
                            "I": FONT_SANS_ITAL,
                            "BI": FONT_SANS_BI,
                        }
                        if style in font_paths and os.path.exists(font_paths[style]):
                            # File exists, try re-registering just this font
                            try:
                                self.add_font("DejaVu", style, str(font_paths[style]), uni=True)
                                print(f"[FONT] Re-registered DejaVu{style if style else 'Regular'}")
                                super().set_font(family, style, size)
                            except Exception as reg_error:
                                print(f"[ERROR] Failed to re-register font: {reg_error}")
                                raise font_error
                        else:
                            print(f"[ERROR] Font file for style '{style}' not found: {font_paths.get(style)}")
                            raise font_error
                    else:
                        raise
            else:
                # For non-DejaVu fonts, use parent method
                super().set_font(family, style, size)
                
        except Exception as e:
            # Do NOT fallback to Helvetica - it cannot render Vietnamese
            error_msg = f"Font setting failed for {family}{style if style else 'Regular'}: {e}"
            if "DejaVu" in family:
                error_msg += (
                    "\n\nVietnamese text requires Unicode fonts. "
                    "Install DejaVu fonts: python Back_end/utils/install_fonts_auto.py"
                )
            print(f"[ERROR] {error_msg}")
            raise

    def add_cover_page(self, stock_code, company_name, industry_name, report_date):
        """Tạo trang bìa chuyên nghiệp."""
        self.add_page()
        
        # Background color
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(0, 0, self.w, self.h, 'F')
        
        # Title
        self.set_y(60)
        self.set_font("DejaVu", "B", 32)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, "BÁO CÁO PHÂN TÍCH ĐẦU TƯ", 0, 1, 'C')
        
        # Stock code
        self.set_y(85)
        self.set_font("DejaVu", "B", 48)
        self.set_text_color(*COLOR_ACCENT)
        self.cell(0, 20, stock_code.upper(), 0, 1, 'C')
        
        # Company name
        self.set_y(110)
        self.set_font("DejaVu", "", 16)
        self.set_text_color(255, 255, 255)
        self.multi_cell(0, 8, company_name, 0, 'C')
        
        # Industry
        self.set_y(130)
        self.set_font("DejaVu", "I", 12)
        self.cell(0, 8, f"Ngành: {industry_name}", 0, 1, 'C')
        
        # Date
        self.set_y(220)
        self.set_font("DejaVu", "", 12)
        self.cell(0, 8, f"Ngày xuất báo cáo: {report_date}", 0, 1, 'C')
        
        # Footer note
        self.set_y(270)
        self.set_font("DejaVu", "", 10)
        self.set_text_color(200, 200, 200)
        self.cell(0, 6, "Báo cáo này được tạo tự động bằng công nghệ AI", 0, 1, 'C')

    def add_section_header(self, title, align="L", color=COLOR_PRIMARY):
        """Thêm tiêu đề section với styling đẹp (COMPACT)."""
        self.ln(2)  # Giảm từ 5 xuống 2
        self.set_font("DejaVu", "B", 11)  # Giảm từ 12 xuống 11
        self.set_text_color(255, 255, 255)
        self.set_fill_color(*color)
        self.cell(190, 7, title, border=0, ln=1, align=align, fill=True)  # Giảm height từ 8 xuống 7
        self.ln(2)  # Giảm từ 3 xuống 2
        self.set_text_color(0, 0, 0)

    def add_subsection_header(self, title, size=9):
        """Thêm tiêu đề subsection (COMPACT)."""
        self.ln(2)  # Giảm từ 3 xuống 2
        self.set_font("DejaVu", "B", size)  # Default giảm từ 10 xuống 9
        self.set_text_color(*COLOR_SECONDARY)
        self.cell(0, 6, title, 0, 1, "L")  # Giảm height từ 7 xuống 6
        self.set_text_color(0, 0, 0)
        self.ln(1)  # Giảm từ 2 xuống 1

    def add_highlight_box(self, title, content, bg_color=COLOR_LIGHT_BG):
        """Thêm box highlight thông tin quan trọng."""
        x = self.get_x()
        y = self.get_y()
        
        # Background
        self.set_fill_color(*bg_color)
        self.rect(x, y, 190, 20, 'F')
        
        # Border
        self.set_draw_color(*COLOR_SECONDARY)
        self.set_line_width(0.5)
        self.rect(x, y, 190, 20, 'D')
        
        # Title
        self.set_xy(x + 5, y + 3)
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(*COLOR_SECONDARY)
        self.cell(0, 5, title, 0, 1, "L")
        
        # Content
        self.set_xy(x + 5, y + 10)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(0, 0, 0)
        self.multi_cell(180, 4, str(content), 0, "L")
        
        self.set_y(y + 23)

    def add_key_metrics_table(self, metrics):
        """Hiển thị các chỉ số quan trọng dạng bảng đẹp."""
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(*COLOR_TABLE_HEADER)
        
        # Header
        col_width = 95
        self.cell(col_width, 6, "Chỉ số", 1, 0, "L", fill=True)
        self.cell(col_width, 6, "Giá trị", 1, 1, "L", fill=True)
        
        # Data rows
        self.set_font("DejaVu", "", 8)
        self.set_text_color(0, 0, 0)
        row_count = 0
        for key, value in metrics.items():
            if value != "N/A":
                bg_color = COLOR_LIGHT_BG if row_count % 2 == 0 else (255, 255, 255)
                self.set_fill_color(*bg_color)
                
                self.set_font("DejaVu", "B", 8)
                self.cell(col_width, 6, key, 1, 0, "L", fill=True)
                
                self.set_font("DejaVu", "", 8)
                self.cell(col_width, 6, str(value), 1, 1, "L", fill=True)
                
                row_count += 1
        
        self.ln(3)

    def header(self):
        """Header cho các trang (COMPACT)."""
        if self.page_no() == 1:
            return  # Skip header on cover page
        
        if self.industry_info is not None and not self.industry_info.empty:
            stock_code = self.industry_info.iloc[0].get("Mã", "")
            ten_cong_ty = self.industry_info.iloc[0].get("Tên công ty", "")
            san = self.industry_info.iloc[0].get("Sàn", "")
        else:
            stock_code = "UNKNOWN"
            ten_cong_ty = "UNKNOWN"
            san = ""
        
        # Header background - compact hơn (giảm từ 25mm xuống 18mm)
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(0, 0, self.w, 18, 'F')
        
        # Stock code
        self.set_y(5)
        self.set_font("DejaVu", "B", 9)  # Giảm từ 10 xuống 9
        self.set_text_color(255, 255, 255)
        self.cell(0, 4, f"{stock_code.upper()} ({san})", 0, 1, 'L')
        
        # Company name
        self.set_y(11)
        self.set_font("DejaVu", "", 7)  # Giảm từ 8 xuống 7
        self.cell(0, 4, ten_cong_ty[:80], 0, 1, 'L')
        
        # Line separator
        self.set_draw_color(*COLOR_SECONDARY)
        self.set_line_width(0.3)
        self.line(10, 18, 200, 18)
        self.set_y(20)  # Giảm từ 28 xuống 20

    def footer(self):
        """Footer cho các trang (COMPACT)."""
        if self.page_no() == 1:
            return  # Skip footer on cover page
        
        self.set_y(-10)  # Giảm từ -12 xuống -10
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(0, self.get_y(), self.w, 10, 'F')  # Giảm từ 12 xuống 10
        
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVu", "", 7)  # Giảm từ 8 xuống 7
        self.set_y(-7)  # Giảm từ -8 xuống -7
        self.cell(0, 4, f'Trang {self.page_no()} / {{nb}}', 0, 1, 'C')

    def basic_information(self, overview_df, profile_df, company_intro=None, company_mission=None, 
                          website=None, founding_date=None, num_shareholders=None, num_employees=None):
        """
        Hiển thị thông tin cơ bản với styling đẹp (COMPACT).
        
        Args:
            overview_df: DataFrame thông tin tổng quan
            profile_df: DataFrame thông tin hồ sơ
            company_intro: Văn bản giới thiệu công ty (từ AI)
            company_mission: Văn bản sứ mệnh (từ AI)
            website: Website công ty
            founding_date: Ngày thành lập
            num_shareholders: Số lượng cổ đông
            num_employees: Số lượng nhân viên
        """
        self.add_section_header("1. THÔNG TIN CƠ BẢN VỀ CÔNG TY")
        
        overview = overview_df.iloc[0] if not overview_df.empty else {}
        profile = profile_df.iloc[0] if not profile_df.empty else {}
        
        # Lấy thông tin từ parameters hoặc DataFrame
        website_value = website or overview.get("website", "N/A")
        founding_date_value = founding_date or profile.get("history_dev", "N/A")
        shareholders_value = num_shareholders or overview.get("no_shareholders", "N/A")
        employees_value = num_employees or overview.get("no_employees", "N/A")
        
        # 1.1 Giới thiệu về công ty
        if company_intro:
            self.add_subsection_header("1.1 Giới thiệu về công ty")
            self.set_font("DejaVu", "", 7)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 4, company_intro, align='J')
            self.ln(3)
        
        # 1.2 Sứ mệnh và triết lý kinh doanh
        if company_mission:
            self.add_subsection_header("1.2 Sứ mệnh và triết lý kinh doanh")
            self.set_font("DejaVu", "", 7)
            self.set_text_color(0, 0, 0)
            self.multi_cell(0, 4, company_mission, align='J')
            self.ln(3)
        
        # Thông tin chi tiết
        # Rút trích Month/Year từ founding_date để hiển thị
        founding_date_display = extract_month_year(founding_date_value) if founding_date_value != "N/A" else "N/A"
        
        info_items = [
            ("Website", website_value),
            ("Ngày thành lập", founding_date_display),
            ("Số lượng cổ đông", str(shareholders_value) if shareholders_value != "N/A" else "N/A"),
            ("Số lượng nhân viên", str(employees_value) if employees_value != "N/A" else "N/A"),
        ]
        
        self.ln(2)
        for label, value in info_items:
            if value and value != "N/A":
                self.set_font("DejaVu", "B", 8)
                self.set_text_color(*COLOR_SECONDARY)
                self.cell(60, 5, f"{label}:", 0, 0, "L")
                self.set_font("DejaVu", "", 7)
                self.set_text_color(0, 0, 0)
                self.cell(0, 5, str(value)[:120], 0, 1, "L")

    def create_executives_table(self, executives_df):
        """Tạo bảng ban lãnh đạo với styling đẹp (COMPACT - CHỈ TOP 5)."""
        self.add_section_header("2. BAN LÃNH ĐẠO")
        
        if executives_df.empty:
            self.set_font("DejaVu", "", 7)
            self.cell(0, 5, "Không có thông tin ban lãnh đạo.", 0, 1, "L")
            return
        
        # CHỈ LẤY TOP 5 để tiết kiệm không gian
        executives_df = executives_df.head(5)
        
        col_width = 190 / 4
        headers = ["Tên cán bộ", "Chức vụ", "Tỷ lệ sở hữu", "Số lượng"]
        
        # Header
        self.set_font("DejaVu", "B", 7)  # Giảm từ 9 xuống 7
        self.set_text_color(255, 255, 255)
        self.set_fill_color(*COLOR_TABLE_HEADER)
        
        for header in headers:
            self.cell(col_width, 5, header, 1, 0, "C", fill=True)  # height từ 7->5, align C
        self.ln(5)
        
        # Data rows
        self.set_font("DejaVu", "", 6)  # Giảm từ 8 xuống 6
        self.set_text_color(0, 0, 0)
        row_count = 0
        
        for idx, row in executives_df.iterrows():
            bg_color = COLOR_LIGHT_BG if row_count % 2 == 0 else (255, 255, 255)
            self.set_fill_color(*bg_color)
            
            texts = [
                str(row.get("officer_name", ""))[:25],  # Truncate
                str(row.get("position_short_name", ""))[:20],
                str(row.get("officer_own_percent", "")),
                str(row.get("quantity", ""))
            ]
            
            # Simple row - no complex height calc
            for text in texts:
                self.cell(col_width, 5, text, 1, 0, "L", fill=True)
            self.ln(5)
            row_count += 1

    def create_subsidiaries_table(self, subsidiaries_df):
        """Tạo bảng công ty con với styling đẹp (COMPACT - TOP 5)."""
        self.add_section_header("3. CÔNG TY CON VÀ LIÊN KẾT")
        
        if subsidiaries_df.empty:
            self.set_font("DejaVu", "", 7)
            self.cell(0, 5, "Không có thông tin công ty con.", 0, 1, "L")
            return

        # CHỈ LẤY TOP 5
        subsidiaries_df = subsidiaries_df.head(5)

        col_width = 95
        headers = ["Tên công ty con", "Tỷ lệ sở hữu"]
        
        # Header
        self.set_font("DejaVu", "B", 7)  # Giảm từ 9 xuống 7
        self.set_text_color(255, 255, 255)
        self.set_fill_color(*COLOR_TABLE_HEADER)
        
        for header in headers:
            self.cell(col_width, 5, header, 1, 0, "C", fill=True)  # height từ 7->5
        self.ln(5)
        
        # Data rows
        self.set_font("DejaVu", "", 6)  # Giảm từ 8 xuống 6
        self.set_text_color(0, 0, 0)
        row_count = 0
        
        for idx, row in subsidiaries_df.iterrows():
            bg_color = COLOR_LIGHT_BG if row_count % 2 == 0 else (255, 255, 255)
            self.set_fill_color(*bg_color)
            
            text1 = str(row.get("sub_company_name", ""))[:40]  # Truncate
            text2 = str(row.get("sub_own_percent", ""))
            
            # Simple row
            self.cell(col_width, 5, text1, 1, 0, "L", fill=True)
            self.cell(col_width, 5, text2, 1, 1, "C", fill=True)
            row_count += 1

    def create_financial_table(self, title, data, years):
        """Tạo bảng tài chính với styling đẹp (COMPACT - CHỈ TOP 10 ROWS)."""
        # CHỈ LẤY TOP 10 rows quan trọng nhất
        data_items = list(data.items())[:10]
        
        page_width = 190
        col_width = page_width * 0.4  # Tăng từ 0.35 -> 0.4 cho label
        year_width = (page_width * 0.6) / len(years)
        
        # Header
        self.set_font("DejaVu", "B", 7)  # Giảm từ 9 xuống 7
        self.set_text_color(255, 255, 255)
        self.set_fill_color(*COLOR_TABLE_HEADER)
        
        self.set_x(10)
        self.cell(col_width, 5, title, 1, 0, "L", fill=True)  # height từ 7->5
        for year in years:
            self.cell(year_width, 5, year, 1, 0, "C", fill=True)
        self.ln(5)
        
        # Data rows
        self.set_font("DejaVu", "", 6)  # Giảm từ 8 xuống 6
        self.set_text_color(0, 0, 0)
        row_count = 0
        
        for key, values in data_items:
            bg_color = COLOR_LIGHT_BG if row_count % 2 == 0 else (255, 255, 255)
            self.set_fill_color(*bg_color)
            
            self.set_x(10)
            self.cell(col_width, 4, str(key)[:30], 1, 0, "L", fill=True)  # height từ 6->4
            for value in values:
                self.cell(year_width, 4, str(value)[:10], 1, 0, "R", fill=True)
            self.ln(4)
            row_count += 1
        
        self.ln(1)  # Giảm từ 3 xuống 1

# ------------------- HÀM XỬ LÝ ẢNH ------------------- #
def extract_date_from_filename(file):
    """Trích xuất ngày từ tên file."""
    base = os.path.basename(file)
    parts = base.split("_")
    if len(parts) < 3:
        return None
    date_str = parts[-1].replace(".png", "")
    try:
        return datetime.strptime(date_str, "%d%m%Y")
    except Exception:
        return None

def get_latest_image_file(stock_code, pattern_suffix, filepath):
    """Tìm file PNG mới nhất cho biểu đồ."""
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
    """Tạo nhóm ảnh cho phân tích kỹ thuật."""
    group1_pattern = "plot_top_shareholders"
    group1_file = get_latest_image_file(stock_code, group1_pattern, filepath)
    group1 = [group1_file] if group1_file else []

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
        f = get_latest_image_file(stock_code, pattern, filepath)
        if f:
            group2.append(f)

    group3_patterns = [
        "draw_chart_1", "draw_chart_2", "draw_chart_3", "draw_chart_4",
        "draw_chart_5", "draw_chart_6", "draw_chart_7", "draw_chart_8",
    ]
    group3 = []
    for pattern in group3_patterns:
        f = get_latest_image_file(stock_code, pattern, filepath)
        if f:
            group3.append(f)

    return group1, group2, group3

# ------------------- HÀM TẠO BÁO CÁO MỚI ------------------- #
def generate_stock_report(stock_code):
    """Hàm chính tạo báo cáo với cấu trúc chuyên nghiệp."""
    
    print(f"📊 Bắt đầu tạo báo cáo cho {stock_code}...")
    
    # Preflight: Check font availability (warn only, don't crash)
    print("   Đang kiểm tra font...")
    font_check = {
        "": FONT_SANS_REG,
        "B": FONT_SANS_BOLD,
        "I": FONT_SANS_ITAL,
        "BI": FONT_SANS_BI,
    }
    _ = ensure_fonts_exist(font_check)
    
    # 1. Thu thập dữ liệu
    print("   Đang thu thập dữ liệu...")
    industry_info = industry_classification(stock_code)
    overview_df = get_company_overview_tcbs(stock_code)
    profile_df = get_company_profile_tcbs(stock_code)
    subsidiaries_df = get_subsidiaries_tcbs(stock_code)
    executives_df = get_executives_vci(stock_code, filter_by='working')

    # Load financial data
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

    # Get key metrics
    key_metrics = get_key_metrics(fr_df_converted, bs_df, is_df)
    
    # Get company info
    company_name = ""
    industry_name = ""
    if not industry_info.empty:
        company_name = industry_info.iloc[0].get("Tên công ty", stock_code)
        industry_name = industry_info.iloc[0].get("Ngành ICB - cấp 2", "")
    
    # Build trend data cho AI
    trend_data = build_trend_data(fr_df_converted)
    
    # ========== GỌI AI 1 LẦN DUY NHẤT CHO TẤT CẢ SECTIONS ==========
    print("   Đang gọi AI cho tất cả phân tích...")
    ai_sections = get_ai_sections(
        stock_code=stock_code,
        company_name=company_name,
        industry_name=industry_name,
        key_metrics=key_metrics,
        trend_data=trend_data,
        ask_gemini_fn=ask_gemini
    )
    # ai_sections chứa: executive, industry, trend, risk, recommendation
    # ================================================================
    
    # 2. Tạo PDF
    pdf = PDF(industry_info=industry_info)
    pdf.alias_nb_pages()
    
    report_date = datetime.now().strftime("%d/%m/%Y")
    
    # 3. Cover Page
    print("   Đang tạo trang bìa...")
    pdf.add_cover_page(stock_code, company_name, industry_name, report_date)
    
    # BỎ Investment Snapshot & Key Metrics (theo yêu cầu user)
    
    # 5. Company Information (GỘP Industry Analysis vào đây để tiết kiệm page)
    print("   Đang tạo phần thông tin công ty...")
    
    # Lấy thông tin công ty để gọi AI
    overview = overview_df.iloc[0] if not overview_df.empty else {}
    profile = profile_df.iloc[0] if not profile_df.empty else {}
    
    # Lấy thông tin từ DataFrame, có thể được truyền vào từ ngoài hoặc lấy từ data
    website = overview.get("website", "")
    founding_date_raw = profile.get("history_dev", "")
    num_shareholders = overview.get("no_shareholders", "")
    num_employees = overview.get("no_employees", "")
    
    # Tìm thông tin vốn điều lệ ban đầu từ founding_date
    initial_capital = "N/A"
    if founding_date_raw:
        # Extract vốn điều lệ từ chuỗi founding_date nếu có
        if "VND" in str(founding_date_raw).upper():
            vnd_match = re.search(r'VND[\d.]+(?:\s*tỷ|\s*triệu)?', str(founding_date_raw), re.IGNORECASE)
            if vnd_match:
                initial_capital = vnd_match.group(0)
            else:
                # Nếu có VND trong text nhưng không match pattern, lấy phần chứa VND
                parts = str(founding_date_raw).split()
                for i, part in enumerate(parts):
                    if "VND" in part.upper():
                        # Lấy part này và các part liên quan
                        initial_capital = " ".join(parts[max(0, i-1):i+2])
                        break
        elif "vốn" in str(founding_date_raw).lower() or "capital" in str(founding_date_raw).lower():
            # Tìm phần chứa thông tin vốn
            initial_capital = str(founding_date_raw)
    
    # Gọi AI để lấy giới thiệu và sứ mệnh
    # Truyền nguyên founding_date_raw để AI có thể extract thông tin đầy đủ
    print("   Đang lấy thông tin giới thiệu công ty từ AI...")
    company_intro = get_company_introduction(
        stock_code=stock_code,
        company_name=company_name,
        founding_date=founding_date_raw if founding_date_raw else "",  # Truyền raw để AI tự format
        initial_capital=initial_capital if initial_capital != "N/A" else "",
        ask_gemini_fn=ask_gemini
    )
    
    print("   Đang lấy thông tin sứ mệnh từ AI...")
    company_mission = get_company_mission(
        stock_code=stock_code,
        company_name=company_name,
        website=website,
        ask_gemini_fn=ask_gemini
    )
    
    pdf.add_page()
    # Hiển thị Month/Year trong phần thông tin
    # (đã được extract ở trên trong month_year_for_intro)
    
    pdf.basic_information(
        overview_df=overview_df, 
        profile_df=profile_df,
        company_intro=company_intro,
        company_mission=company_mission,
        website=website,
        founding_date=founding_date_raw,  # Truyền raw để extract trong basic_information
        num_shareholders=num_shareholders,
        num_employees=num_employees
    )
    pdf.create_executives_table(executives_df)
    pdf.create_subsidiaries_table(subsidiaries_df)
    
    # 6. Industry Analysis (GỘP vào trang Company Info)
    print("   Đang thêm phân tích ngành...")
    pdf.add_section_header("4. PHÂN TÍCH NGÀNH")
    
    # Dùng ai_sections["industry"] - đã có sẵn (COMPACT)
    if ai_sections.get("industry"):
        pdf.set_font("DejaVu", "", 7)  # Giảm từ 9 xuống 7
        pdf.multi_cell(0, 4, ai_sections["industry"], align='J')  # Justify
    
    # 7. Financial Statements (COMPACT - 4 TABLES)
    print("   Đang thêm báo cáo tài chính...")
    # BỎ add_page() - gộp vào trang hiện tại
    pdf.add_section_header("5. BÁO CÁO TÀI CHÍNH")
    
    # BỔ SUNG LẠI TẤT CẢ 4 TABLES
    pdf.add_subsection_header("5.1. Cân đối kế toán")
    pdf.create_financial_table("Cân đối kế toán", bs_data, years)
    
    pdf.add_subsection_header("5.2. Kết quả kinh doanh")
    pdf.create_financial_table("Kết quả kinh doanh", is_data, years)
    
    pdf.add_subsection_header("5.3. Lưu chuyển tiền tệ")
    pdf.create_financial_table("Lưu chuyển tiền tệ", cf_data, years)
    
    pdf.add_subsection_header("5.4. Chỉ số tài chính")
    pdf.create_financial_table("Chỉ số tài chính", fr_data, years)
    
    # 8. Financial Trend Analysis
    print("   Đang thêm phân tích xu hướng tài chính...")
    # BỎ add_page() - gộp vào trang hiện tại để tiết kiệm
    pdf.add_section_header("6. PHÂN TÍCH XU HƯỚNG TÀI CHÍNH")
    
    # Dùng ai_sections["trend"] - đã có sẵn (COMPACT)
    if ai_sections.get("trend"):
        pdf.set_font("DejaVu", "", 7)  # Giảm từ 9 xuống 7
        pdf.multi_cell(0, 4, ai_sections["trend"], align='J')  # Justify
    
    # 9. Valuation (COMPACT)
    print("   Đang tính toán định giá...")
    # BỎ add_page() - gộp vào trang hiện tại
    pdf.add_section_header("7. ĐỊNH GIÁ CỔ PHIẾU")
    
    eps_value, bvps_value = get_eps_bvps_2024(stock_code)
    industry_pe, industry_pb = valuation_index(stock_code)
    valuation_price = calculate_stock_price(eps_value, bvps_value, industry_pe, industry_pb)
    
    if valuation_price is not None:
        # Compact valuation - chỉ hiển thị kết quả
        pdf.set_font("DejaVu", "B", 8)
        pdf.cell(0, 4, f"Giá định giá (P/E & P/B): {valuation_price:.3f} VND", 0, 1, "L")
        pdf.set_font("DejaVu", "", 7)
        pdf.cell(0, 4, f"EPS: {eps_value:,.0f} | BVPS: {bvps_value:,.0f} | P/E ngành: {industry_pe} | P/B ngành: {industry_pb}", 0, 1, "L")
    else:
        pdf.set_font("DejaVu", "", 7)
        pdf.set_text_color(*COLOR_WARNING)
        pdf.cell(0, 4, "Không đủ dữ liệu để tính giá định giá.", 0, 1, "L")
        pdf.set_text_color(0, 0, 0)
    
    # BỎ SWOT Analysis (theo yêu cầu redesign)
    
    # 10. Risk Assessment (COMPACT)
    print("   Đang thêm đánh giá rủi ro...")
    # BỎ add_page() - gộp vào trang hiện tại
    pdf.add_section_header("8. ĐÁNH GIÁ RỦI RO")
    
    # Dùng ai_sections["risk"] - đã có sẵn (COMPACT)
    if ai_sections.get("risk"):
        pdf.set_font("DejaVu", "", 7)  # Giảm từ 9 xuống 7
        pdf.multi_cell(0, 4, ai_sections["risk"], align='J')  # Justify
    
    # BỎ Macro News (theo yêu cầu redesign)
    # BỎ Khuyến nghị đầu tư (theo yêu cầu user)
    
    # 9. Technical Analysis Charts (COMPACT - TẤT CẢ GROUP2 CHARTS)
    print("   Đang chèn biểu đồ phân tích kỹ thuật...")
    pdf.add_page()
    pdf.add_section_header("9. PHÂN TÍCH KỸ THUẬT")
    
    group1, group2, group3 = generate_image_groups(pdf, stock_code, FILEPATH)

    # LẤY TẤT CẢ GROUP2 CHARTS (bao gồm plot_indicator_charts_1, 2, 3, 4)
    # Chiến lược: 2 ảnh/trang, height=100mm mỗi ảnh
    
    if group2:
        # LẤY TẤT CẢ charts trong group2
        img_count = 0
        
        for image_path in group2:
            if image_path and os.path.exists(image_path):
                try:
                    # 2 ảnh/trang
                    if img_count > 0 and img_count % 2 == 0:
                        pdf.add_page()
                    
                    # Compact: width=190mm, height=100mm (2 ảnh fit 1 trang)
                    pdf.image(image_path, x=10, w=190, h=100)
                    pdf.ln(1)  # Spacing minimal
                    img_count += 1
                except Exception as e:
                    print(f"Warning: Could not insert image {image_path}: {e}")
    
    # 10. CHỈ SỐ ĐÁNH GIÁ DOANH NGHIỆP (GROUP3: draw_chart_1-8)
    print("   Đang chèn biểu đồ chỉ số đánh giá doanh nghiệp...")
    if group3:
        pdf.add_page()
        pdf.add_section_header("10. CHỈ SỐ ĐÁNH GIÁ DOANH NGHIỆP")
        
        img_count = 0
        
        for image_path in group3:
            if image_path and os.path.exists(image_path):
                try:
                    # 2 ảnh/trang
                    if img_count > 0 and img_count % 2 == 0:
                        pdf.add_page()
                    
                    # Compact: width=190mm, height=100mm
                    pdf.image(image_path, x=10, w=190, h=100)
                    pdf.ln(1)  # Spacing minimal
                    img_count += 1
                except Exception as e:
                    print(f"Warning: Could not insert image {image_path}: {e}")
    
    # BỎ Appendices (theo yêu cầu redesign)
    
    # Save PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"Report_{stock_code.upper()}_{timestamp}.pdf"
    export_dir = REPORT_EXPORT_DIR
    export_dir.mkdir(parents=True, exist_ok=True)
    output_path = str((export_dir / filename).resolve())
    
    # Check if DejaVu fonts are loaded
    if not PDF._has_dejavu:
        print("\n" + "="*60)
        print("❌ ERROR: DejaVu fonts not installed!")
        print("="*60)
        print("Vietnamese text cannot be encoded without DejaVu fonts.")
        print("\nPlease install fonts using one of these methods:")
        print("\n1. AUTO-INSTALL (Recommended):")
        print("   cd Back_end")
        print("   python download_fonts.py")
        print("\n2. MANUAL INSTALL:")
        print("   Download: https://dejavu-fonts.github.io/Download.html")
        print("   Extract and copy .ttf files to: Back_end/assets/fonts/")
        print("="*60 + "\n")
        raise RuntimeError(
            "Cannot generate PDF without DejaVu fonts. "
            "Vietnamese text requires Unicode font support. "
            "Please run: python Back_end/download_fonts.py"
        )
    
    try:
        pdf.output(output_path, 'F')
        print(f"✅ Báo cáo đã được lưu tại: {output_path}")
        return output_path
    except UnicodeEncodeError as e:
        print(f"\n❌ Unicode encoding error: {e}")
        print("This usually means fonts are not properly loaded.")
        print("Please ensure DejaVu fonts are installed in Back_end/assets/fonts/")
        raise
