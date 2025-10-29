# fundamental_analyst.py
"""
Module tính toán các chỉ số phân tích cơ bản (Fundamental Analysis) cho cổ phiếu.
Bao gồm các nhóm chỉ số: Thanh khoản, Đòn bẩy, Hiệu quả hoạt động, Sinh lợi, Định giá, Tăng trưởng, Dòng tiền.
"""

import os
import sys
import re
import unicodedata
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

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
from data_processor import (
    get_financial_ratios_vci, industry_classification,
    balance_sheet, income_statement, cash_flow, tm_data, bctckh_data
)
from financial_statement import financial_ratios_final
from paths import DATA_STORE_DIR, DATA_RAW_DIR, MARKET_INDEX_FILE


# ==================== HÀM HỖ TRỢ ====================

def safe_divide(numerator, denominator, default=None):
    """Chia an toàn với xử lý None và chia cho 0."""
    if denominator is None or pd.isna(denominator) or denominator == 0:
        return default
    if numerator is None or pd.isna(numerator):
        return default
    try:
        return float(numerator) / float(denominator)
    except (ValueError, TypeError):
        return default

def safe_get_value(df, column, year=None, default=None):
    """Lấy giá trị an toàn từ DataFrame."""
    try:
        if year is not None:
            if isinstance(df, pd.DataFrame):
                if "Năm" in df.columns:
                    row = df[df["Năm"] == year]
                    if not row.empty and column in row.columns:
                        val = row[column].iloc[0]
                        return val if not pd.isna(val) else default
                elif year in df.index:
                    if column in df.columns:
                        val = df.loc[year, column]
                        return val if not pd.isna(val) else default
        else:
            if column in df.columns:
                val = df[column].iloc[0] if len(df) > 0 else default
                return val if not pd.isna(val) else default
    except Exception:
        pass
    return default

def get_year_data(df, year):
    """Lấy dữ liệu của một năm cụ thể từ DataFrame."""
    if df.empty:
        return {}
    try:
        if "Năm" in df.columns:
            year_data = df[df["Năm"] == year].iloc[0].to_dict() if not df[df["Năm"] == year].empty else {}
        elif year in df.index:
            year_data = df.loc[year].to_dict()
        else:
            year_data = {}
        return {k: v for k, v in year_data.items() if not pd.isna(v)}
    except Exception:
        return {}


# ==================== NHÓM 1: CHỈ SỐ THANH KHOẢN ====================

def calculate_liquidity_ratios(stock_code, years=[2020, 2021, 2022, 2023, 2024]):
    """
    Tính các chỉ số thanh khoản:
    - Current Ratio = Tài sản ngắn hạn / Nợ ngắn hạn
    - Quick Ratio = (Tài sản ngắn hạn - Hàng tồn kho) / Nợ ngắn hạn
    - Cash Ratio = Tiền và tương đương tiền / Nợ ngắn hạn
    - Net Working Capital = Tài sản ngắn hạn - Nợ ngắn hạn
    """
    bs_df = balance_sheet(stock_code)
    tm_df = tm_data(stock_code)
    
    results = {}
    for year in years:
        year_data = {}
        
        # Lấy dữ liệu từ Balance Sheet
        current_assets = safe_get_value(bs_df, "TÀI SẢN NGẮN HẠN", year)
        current_liabilities = safe_get_value(bs_df, "Nợ ngắn hạn", year)
        inventory = safe_get_value(tm_df, "Hàng tồn kho", year) or safe_get_value(bs_df, "Hàng tồn kho, ròng", year)
        cash = safe_get_value(tm_df, "Tiền và tương đương tiền", year) or safe_get_value(bs_df, "Tiền và tương đương tiền", year)
        
        # Current Ratio
        year_data["Current Ratio"] = safe_divide(current_assets, current_liabilities)
        
        # Quick Ratio
        quick_assets = current_assets - (inventory if inventory else 0)
        year_data["Quick Ratio"] = safe_divide(quick_assets, current_liabilities)
        
        # Cash Ratio
        year_data["Cash Ratio"] = safe_divide(cash, current_liabilities)
        
        # Net Working Capital
        if current_assets is not None and current_liabilities is not None:
            year_data["Net Working Capital"] = current_assets - current_liabilities
        
        results[year] = year_data
    
    return results


# ==================== NHÓM 2: CHỈ SỐ ĐÒN BẨY ====================

def calculate_leverage_ratios(stock_code, years=[2020, 2021, 2022, 2023, 2024]):
    """
    Tính các chỉ số đòn bẩy:
    - Debt/Equity = Tổng nợ / Vốn chủ sở hữu
    - Debt/Assets = Tổng nợ / Tổng tài sản
    - Equity Multiplier = Tổng tài sản / Vốn chủ sở hữu
    - Debt-to-Capital = Tổng nợ / (Tổng nợ + Vốn chủ sở hữu)
    - Interest Coverage = EBIT / Chi phí lãi vay
    """
    bs_df = balance_sheet(stock_code)
    is_df = income_statement(stock_code)
    tm_df = tm_data(stock_code)
    
    results = {}
    for year in years:
        year_data = {}
        
        total_assets = safe_get_value(bs_df, "TỔNG CỘNG TÀI SẢN", year)
        total_debt = safe_get_value(bs_df, "NỢ PHẢI TRẢ", year)
        equity = safe_get_value(bs_df, "VỐN CHỦ SỞ HỮU", year)
        
        # Debt/Equity
        year_data["Debt/Equity"] = safe_divide(total_debt, equity)
        
        # Debt/Assets
        year_data["Debt/Assets"] = safe_divide(total_debt, total_assets)
        
        # Equity Multiplier
        year_data["Equity Multiplier"] = safe_divide(total_assets, equity)
        
        # Debt-to-Capital
        capital = (total_debt if total_debt else 0) + (equity if equity else 0)
        year_data["Debt-to-Capital"] = safe_divide(total_debt, capital) if capital > 0 else None
        
        # Interest Coverage
        ebit = safe_get_value(is_df, "Tổng lợi nhuận kế toán trước thuế", year)
        interest_expense = safe_get_value(tm_df, "Lãi tiền vay", year) or safe_get_value(is_df, "Trong đó: Chi phí lãi vay", year)
        year_data["Interest Coverage"] = safe_divide(ebit, interest_expense)
        
        results[year] = year_data
    
    return results


# ==================== NHÓM 3: CHỈ SỐ HIỆU QUẢ HOẠT ĐỘNG ====================

def calculate_efficiency_ratios(stock_code, years=[2020, 2021, 2022, 2023, 2024]):
    """
    Tính các chỉ số hiệu quả hoạt động:
    - Asset Turnover = Doanh thu thuần / Tổng tài sản trung bình
    - Inventory Turnover = Giá vốn hàng bán / Hàng tồn kho trung bình
    - Receivables Turnover = Doanh thu thuần / Phải thu trung bình
    - Days Sales Outstanding = 365 / Receivables Turnover
    - Days Inventory Outstanding = 365 / Inventory Turnover
    - Days Payable Outstanding = 365 / Payables Turnover
    """
    bs_df = balance_sheet(stock_code)
    is_df = income_statement(stock_code)
    tm_df = tm_data(stock_code)
    
    results = {}
    prev_year_assets = None
    prev_year_inventory = None
    prev_year_receivables = None
    prev_year_payables = None
    
    for year in years:
        year_data = {}
        
        revenue = safe_get_value(is_df, "Doanh thu thuần", year)
        total_assets = safe_get_value(bs_df, "TỔNG CỘNG TÀI SẢN", year)
        inventory = safe_get_value(tm_df, "Hàng tồn kho", year) or safe_get_value(bs_df, "Hàng tồn kho, ròng", year)
        receivables = safe_get_value(bs_df, "Các khoản phải thu ngắn hạn", year)
        payables = safe_get_value(bs_df, "Phải trả người bán ngắn hạn", year)
        
        # Giá vốn hàng bán (ước tính từ Doanh thu - Lợi nhuận gộp)
        gross_profit = safe_get_value(is_df, "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ", year)
        cogs = revenue - gross_profit if revenue and gross_profit else None
        
        # Asset Turnover
        avg_assets = (total_assets + prev_year_assets) / 2 if prev_year_assets else total_assets
        year_data["Asset Turnover"] = safe_divide(revenue, avg_assets)
        
        # Inventory Turnover
        avg_inventory = (inventory + prev_year_inventory) / 2 if prev_year_inventory else inventory
        year_data["Inventory Turnover"] = safe_divide(cogs, avg_inventory)
        
        # Receivables Turnover
        avg_receivables = (receivables + prev_year_receivables) / 2 if prev_year_receivables else receivables
        year_data["Receivables Turnover"] = safe_divide(revenue, avg_receivables)
        
        # Days Sales Outstanding
        year_data["Days Sales Outstanding"] = safe_divide(365, year_data["Receivables Turnover"])
        
        # Days Inventory Outstanding
        year_data["Days Inventory Outstanding"] = safe_divide(365, year_data["Inventory Turnover"])
        
        # Payables Turnover và Days Payable Outstanding
        avg_payables = (payables + prev_year_payables) / 2 if prev_year_payables else payables
        payables_turnover = safe_divide(cogs, avg_payables)
        year_data["Payables Turnover"] = payables_turnover
        year_data["Days Payable Outstanding"] = safe_divide(365, payables_turnover)
        
        # Cash Conversion Cycle
        if all([year_data.get("Days Sales Outstanding"), year_data.get("Days Inventory Outstanding"), year_data.get("Days Payable Outstanding")]):
            year_data["Cash Conversion Cycle"] = (
                year_data["Days Sales Outstanding"] + 
                year_data["Days Inventory Outstanding"] - 
                year_data["Days Payable Outstanding"]
            )
        
        # Cập nhật giá trị cho năm sau
        prev_year_assets = total_assets
        prev_year_inventory = inventory
        prev_year_receivables = receivables
        prev_year_payables = payables
        
        results[year] = year_data
    
    return results


# ==================== NHÓM 4: CHỈ SỐ SINH LỢI ====================

def calculate_profitability_ratios(stock_code, years=[2020, 2021, 2022, 2023, 2024]):
    """
    Tính các chỉ số sinh lợi:
    - Gross Margin = Lợi nhuận gộp / Doanh thu thuần
    - Operating Margin = Lợi nhuận thuần từ HĐKD / Doanh thu thuần
    - Net Margin = Lợi nhuận sau thuế / Doanh thu thuần
    - ROE = Lợi nhuận sau thuế / Vốn chủ sở hữu trung bình
    - ROA = Lợi nhuận sau thuế / Tổng tài sản trung bình
    - ROIC = NOPAT / (Vốn chủ sở hữu + Nợ có lãi)
    """
    bs_df = balance_sheet(stock_code)
    is_df = income_statement(stock_code)
    
    results = {}
    prev_year_equity = None
    prev_year_assets = None
    
    for year in years:
        year_data = {}
        
        revenue = safe_get_value(is_df, "Doanh thu thuần", year)
        gross_profit = safe_get_value(is_df, "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ", year)
        operating_profit = safe_get_value(is_df, "Lợi nhuận thuần từ hoạt động kinh doanh", year)
        net_profit = safe_get_value(is_df, "Lợi nhuận sau thuế thu nhập doanh nghiệp", year)
        
        equity = safe_get_value(bs_df, "VỐN CHỦ SỞ HỮU", year)
        total_assets = safe_get_value(bs_df, "TỔNG CỘNG TÀI SẢN", year)
        
        # Margins
        year_data["Gross Margin (%)"] = safe_divide(gross_profit, revenue, default=0) * 100
        year_data["Operating Margin (%)"] = safe_divide(operating_profit, revenue, default=0) * 100
        year_data["Net Margin (%)"] = safe_divide(net_profit, revenue, default=0) * 100
        
        # ROE và ROA
        avg_equity = (equity + prev_year_equity) / 2 if prev_year_equity else equity
        avg_assets = (total_assets + prev_year_assets) / 2 if prev_year_assets else total_assets
        
        year_data["ROE (%)"] = safe_divide(net_profit, avg_equity, default=0) * 100
        year_data["ROA (%)"] = safe_divide(net_profit, avg_assets, default=0) * 100
        
        # ROIC
        interest_expense = safe_get_value(is_df, "Trong đó: Chi phí lãi vay", year)
        tax_rate = safe_get_value(is_df, "Chi phí thuế thu nhập doanh nghiệp", year)
        ebit = safe_get_value(is_df, "Tổng lợi nhuận kế toán trước thuế", year)
        
        if ebit and tax_rate:
            tax_rate_pct = safe_divide(tax_rate, ebit, default=0.2)  # Ước tính 20% nếu không có
            nopat = operating_profit * (1 - tax_rate_pct) if operating_profit else None
            
            total_debt = safe_get_value(bs_df, "NỢ PHẢI TRẢ", year)
            invested_capital = (equity if equity else 0) + (total_debt if total_debt else 0)
            year_data["ROIC (%)"] = safe_divide(nopat, invested_capital, default=0) * 100 if nopat else None
        
        # Cập nhật giá trị cho năm sau
        prev_year_equity = equity
        prev_year_assets = total_assets
        
        results[year] = year_data
    
    return results


# ==================== NHÓM 5: CHỈ SỐ ĐỊNH GIÁ ====================

def get_eps_bvps_2024(stock_code):
    """
    Lấy ra EPS (VND) và BVPS (VND) năm 2024 từ file Excel được lưu trong đường dẫn DATA_STORE_DIR.
    File có định dạng: {stock_code}_financialratios_{ngày tháng năm xuất ra}.xlsx.
    Nếu có nhiều file, chọn file có ngày gần hiện tại nhất.
    """
    import glob
    
    pattern = str(DATA_STORE_DIR / f"{stock_code}_financialratios_*.xlsx")
    files = glob.glob(pattern)
    
    if not files:
        print(f"Không tìm thấy file tỷ số tài chính cho mã {stock_code} trong {DATA_STORE_DIR}.")
        return None, None

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

    files_with_dates = [(f, extract_date(f)) for f in files if extract_date(f) is not None]
    if not files_with_dates:
        print("Không trích xuất được ngày từ tên file tỷ số tài chính.")
        return None, None

    best_file, best_date = max(files_with_dates, key=lambda x: x[1])
    print(f"Đang sử dụng file tỷ số tài chính: {best_file}")

    try:
        df = pd.read_excel(best_file, index_col=0)
        
        if "2024" not in df.index:
            print("Không tìm thấy dòng năm 2024 trong file tỷ số tài chính.")
            return None, None
        if "EPS (VND)" not in df.columns or "BVPS (VND)" not in df.columns:
            print("Không tìm thấy cột 'EPS (VND)' hoặc 'BVPS (VND)' trong file tỷ số tài chính.")
            return None, None

        eps_str = df.loc["2024", "EPS (VND)"]
        bvps_str = df.loc["2024", "BVPS (VND)"]
        
        try:
            eps_float = float(str(eps_str).replace(',', '').replace(' ', ''))
            bvps_float = float(str(bvps_str).replace(',', '').replace(' ', ''))
        except Exception as e:
            print("Lỗi chuyển đổi EPS/BVPS sang float:", e)
            return None, None

        return eps_float, bvps_float
    except Exception as e:
        print(f"Lỗi khi đọc file tỷ số tài chính: {e}")
        return None, None


def valuation_index(stock_code):
    """
    Lấy chỉ số định giá của ngành của cổ phiếu dựa vào thông tin phân loại ngành và chỉ số ngành.
    """
    def remove_accents(text):
        try:
            text = unicodedata.normalize('NFD', text)
            text = ''.join([char for char in text if unicodedata.category(char) != 'Mn'])
            return text
        except Exception:
            return text

    df_class = industry_classification(stock_code)
    if df_class.empty or "Ngành ICB - cấp 2" not in df_class.columns:
        print(f"Không tìm thấy thông tin phân loại ngành cho cổ phiếu {stock_code}.")
        return None, None

    industry = df_class["Ngành ICB - cấp 2"].iloc[0].strip()
    industry_normalized = remove_accents(industry).lower()
    
    file_path = str(MARKET_INDEX_FILE.resolve())
    if not os.path.exists(file_path):
        print(f"File chỉ số ngành không tồn tại: {file_path}")
        return None, None

    try:
        df_index = pd.read_excel(file_path)
        df_index.columns = df_index.columns.str.strip()
        df_index["Ngành"] = df_index["Ngành"].astype(str).str.strip()
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

    pe_col = find_col(df_index, "P/E ngành")
    pb_col = find_col(df_index, "P/B ngành")
    
    if pe_col is None or pb_col is None:
        print("Không tìm thấy cột định giá P/E hoặc P/B trong file chỉ số ngành.")
        return None, None

    df_filtered = df_index[df_index["Ngành_normalized"] == industry_normalized]
    if df_filtered.empty:
        print(f"Không tìm thấy dữ liệu chỉ số ngành cho ngành: {industry}")
        return None, None

    try:
        pe_industry = df_filtered[pe_col].iloc[0]
        pb_industry = df_filtered[pb_col].iloc[0]
        if isinstance(pe_industry, str):
            pe_industry = float(pe_industry.replace(",", "."))
        if isinstance(pb_industry, str):
            pb_industry = float(pb_industry.replace(",", "."))
    except Exception as e:
        print(f"Lỗi chuyển đổi giá trị định giá: {e}")
        return None, None

    return pe_industry, pb_industry


def calculate_valuation_ratios(stock_code, years=[2020, 2021, 2022, 2023, 2024]):
    """
    Tính các chỉ số định giá:
    - P/E = Giá cổ phiếu / EPS
    - P/B = Giá cổ phiếu / BVPS
    - P/S = Giá cổ phiếu * Số cổ phiếu / Doanh thu
    """
    # Lấy dữ liệu từ financial ratios (đã có P/E, P/B)
    try:
        fr_df = financial_ratios_final(stock_code)
    except Exception:
        fr_df = pd.DataFrame()
    
    results = {}
    for year in years:
        year_data = {}
        
        # P/E và P/B từ financial ratios
        if not fr_df.empty and str(year) in fr_df.index:
            year_data["P/E"] = safe_get_value(fr_df, "P/E", str(year))
            year_data["P/B"] = safe_get_value(fr_df, "P/B", str(year))
            year_data["EPS (VND)"] = safe_get_value(fr_df, "EPS (VND)", str(year))
            year_data["BVPS (VND)"] = safe_get_value(fr_df, "BVPS (VND)", str(year))
        
        results[year] = year_data
    
    return results


def calculate_stock_price(eps, bvps, industry_pe, industry_pb):
    """
    Tính giá cổ phiếu dựa trên 2 phương pháp:
      - Phương pháp P/E: Giá = EPS * P/E (của ngành)
      - Phương pháp P/B: Giá = BVPS * P/B (của ngành)
    Sau đó, lấy trung bình của 2 kết quả trên làm giá cổ phiếu định giá, chia cho 1000.
    """
    if eps is None or bvps is None or industry_pe is None or industry_pb is None:
        print("Không đủ dữ liệu để tính giá cổ phiếu định giá.")
        return None
    
    try:
        eps = float(eps)
        bvps = float(bvps)
        industry_pe = float(industry_pe)
        industry_pb = float(industry_pb)
    except (ValueError, TypeError) as e:
        print(f"Lỗi chuyển đổi giá trị sang float: {e}")
        return None

    if any(pd.isna(val) for val in [eps, bvps, industry_pe, industry_pb]):
        print("Có giá trị NaN trong dữ liệu đầu vào.")
        return None

    price_pe = eps * industry_pe
    price_pb = bvps * industry_pb
    stock_price = (price_pe + price_pb) / 2
    stock_price_converted = stock_price / 1000  # Chia cho 1000
    return stock_price_converted


# ==================== NHÓM 6: CHỈ SỐ TĂNG TRƯỞNG ====================

def calculate_growth_ratios(stock_code, years=[2020, 2021, 2022, 2023, 2024]):
    """
    Tính các chỉ số tăng trưởng:
    - Revenue Growth = (Doanh thu năm N - Doanh thu năm N-1) / Doanh thu năm N-1
    - Net Income Growth = (LNST năm N - LNST năm N-1) / LNST năm N-1
    - EPS Growth = (EPS năm N - EPS năm N-1) / EPS năm N-1
    - Asset Growth = (Tài sản năm N - Tài sản năm N-1) / Tài sản năm N-1
    """
    is_df = income_statement(stock_code)
    bs_df = balance_sheet(stock_code)
    
    try:
        fr_df = financial_ratios_final(stock_code)
    except Exception:
        fr_df = pd.DataFrame()
    
    results = {}
    prev_revenue = None
    prev_net_income = None
    prev_eps = None
    prev_assets = None
    
    for year in sorted(years):
        year_data = {}
        
        revenue = safe_get_value(is_df, "Doanh thu thuần", year)
        net_income = safe_get_value(is_df, "Lợi nhuận sau thuế thu nhập doanh nghiệp", year)
        total_assets = safe_get_value(bs_df, "TỔNG CỘNG TÀI SẢN", year)
        
        if not fr_df.empty and str(year) in fr_df.index:
            eps = safe_get_value(fr_df, "EPS (VND)", str(year))
        else:
            eps = None
        
        # Revenue Growth
        if prev_revenue and revenue:
            year_data["Revenue Growth (%)"] = safe_divide(revenue - prev_revenue, prev_revenue, default=0) * 100
        
        # Net Income Growth
        if prev_net_income and net_income:
            year_data["Net Income Growth (%)"] = safe_divide(net_income - prev_net_income, prev_net_income, default=0) * 100
        
        # EPS Growth
        if prev_eps and eps:
            year_data["EPS Growth (%)"] = safe_divide(eps - prev_eps, prev_eps, default=0) * 100
        
        # Asset Growth
        if prev_assets and total_assets:
            year_data["Asset Growth (%)"] = safe_divide(total_assets - prev_assets, prev_assets, default=0) * 100
        
        # Cập nhật giá trị cho năm sau
        prev_revenue = revenue
        prev_net_income = net_income
        prev_eps = eps
        prev_assets = total_assets
        
        results[year] = year_data
    
    return results


# ==================== NHÓM 7: CHỈ SỐ DÒNG TIỀN ====================

def calculate_cash_flow_ratios(stock_code, years=[2020, 2021, 2022, 2023, 2024]):
    """
    Tính các chỉ số dòng tiền:
    - Operating Cash Flow / Net Income
    - Free Cash Flow = OCF - Capital Expenditures
    - Cash Flow Margin = OCF / Revenue
    """
    cf_df = cash_flow(stock_code)
    is_df = income_statement(stock_code)
    
    results = {}
    for year in years:
        year_data = {}
        
        ocf = safe_get_value(cf_df, "Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh (TT)", year)
        capex = safe_get_value(cf_df, "Tiền chi để mua sắm, xây dựng TSCĐ và các tài sản dài hạn khác (TT)", year)
        net_income = safe_get_value(is_df, "Lợi nhuận sau thuế thu nhập doanh nghiệp", year)
        revenue = safe_get_value(is_df, "Doanh thu thuần", year)
        
        # Operating Cash Flow / Net Income
        year_data["OCF/Net Income"] = safe_divide(ocf, net_income)
        
        # Free Cash Flow
        if ocf is not None and capex is not None:
            year_data["Free Cash Flow"] = ocf - abs(capex) if capex else ocf
        
        # Cash Flow Margin
        year_data["Cash Flow Margin (%)"] = safe_divide(ocf, revenue, default=0) * 100
        
        results[year] = year_data
    
    return results


# ==================== HÀM TỔNG HỢP ====================

def calculate_comprehensive_fundamental_analysis(stock_code, years=[2020, 2021, 2022, 2023, 2024]):
    """
    Hàm tổng hợp tính toán tất cả các chỉ số phân tích cơ bản.
    Trả về DataFrame với các chỉ số được nhóm theo loại.
    """
    print(f"Đang tính toán các chỉ số phân tích cơ bản cho {stock_code}...")
    
    # Tính toán từng nhóm chỉ số
    liquidity = calculate_liquidity_ratios(stock_code, years)
    leverage = calculate_leverage_ratios(stock_code, years)
    efficiency = calculate_efficiency_ratios(stock_code, years)
    profitability = calculate_profitability_ratios(stock_code, years)
    valuation = calculate_valuation_ratios(stock_code, years)
    growth = calculate_growth_ratios(stock_code, years)
    cashflow = calculate_cash_flow_ratios(stock_code, years)
    
    # Tạo DataFrame tổng hợp
    all_metrics = {}
    for year in years:
        year_metrics = {}
        year_metrics.update(liquidity.get(year, {}))
        year_metrics.update(leverage.get(year, {}))
        year_metrics.update(efficiency.get(year, {}))
        year_metrics.update(profitability.get(year, {}))
        year_metrics.update(valuation.get(year, {}))
        year_metrics.update(growth.get(year, {}))
        year_metrics.update(cashflow.get(year, {}))
        all_metrics[year] = year_metrics
    
    # Chuyển sang DataFrame
    df_result = pd.DataFrame.from_dict(all_metrics, orient='index')
    df_result.index.name = 'Năm'
    
    # Sắp xếp cột theo nhóm
    column_order = [
        # Thanh khoản
        'Current Ratio', 'Quick Ratio', 'Cash Ratio', 'Net Working Capital',
        # Đòn bẩy
        'Debt/Equity', 'Debt/Assets', 'Equity Multiplier', 'Debt-to-Capital', 'Interest Coverage',
        # Hiệu quả
        'Asset Turnover', 'Inventory Turnover', 'Receivables Turnover', 'Payables Turnover',
        'Days Sales Outstanding', 'Days Inventory Outstanding', 'Days Payable Outstanding', 'Cash Conversion Cycle',
        # Sinh lợi
        'Gross Margin (%)', 'Operating Margin (%)', 'Net Margin (%)',
        'ROE (%)', 'ROA (%)', 'ROIC (%)',
        # Định giá
        'P/E', 'P/B', 'EPS (VND)', 'BVPS (VND)',
        # Tăng trưởng
        'Revenue Growth (%)', 'Net Income Growth (%)', 'EPS Growth (%)', 'Asset Growth (%)',
        # Dòng tiền
        'OCF/Net Income', 'Free Cash Flow', 'Cash Flow Margin (%)'
    ]
    
    # Chỉ giữ các cột có trong DataFrame
    existing_columns = [col for col in column_order if col in df_result.columns]
    other_columns = [col for col in df_result.columns if col not in column_order]
    final_columns = existing_columns + other_columns
    
    df_result = df_result[final_columns]
    
    return df_result


def export_fundamental_analysis(stock_code, years=[2020, 2021, 2022, 2023, 2024]):
    """
    Tính toán và xuất kết quả phân tích cơ bản ra file Excel.
    """
    df_analysis = calculate_comprehensive_fundamental_analysis(stock_code, years)
    
    report_date = datetime.now().strftime("%d%m%Y")
    file_path = DATA_STORE_DIR / f"{stock_code}_fundamental_analysis_{report_date}.xlsx"
    
    df_analysis.to_excel(str(file_path), index=True)
    print(f"Đã xuất file phân tích cơ bản: {file_path}")
    
    return df_analysis
