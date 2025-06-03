import os
import pandas as pd
from vnstock import Vnstock

#########################################
# NHÓM 1: HÀM ĐỌC DỮ LIỆU TỪ FILE EXCEL (LOCAL)
#########################################

def balance_sheet(stock_code):
    """
    Đọc dữ liệu cân đối kế toán từ file Excel local và chuyển đổi đơn vị từ triệu sang tỷ VND.
    Sử dụng file "data_CĐKT.xlsx".
    """
    file_path = os.path.join(
        "\\Data\\Data cleaned",
        "data_CĐKT.xlsx"
    )
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    sheets = ["data1_CĐKT", "data2_CĐKT", "data3_CĐKT", "data4_CĐKT", "data5_CĐKT"]
    desired_columns = [
        "Mã", "TÀI SẢN NGẮN HẠN", "TÀI SẢN DÀI HẠN",
        "TỔNG CỘNG TÀI SẢN", "Nợ ngắn hạn", "Nợ dài hạn",
        "NỢ PHẢI TRẢ", "VỐN CHỦ SỞ HỮU", "TỔNG CỘNG NGUỒN VỐN"
    ]
    result_df = pd.DataFrame()

    for sheet in sheets:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet)
            df.columns = df.columns.str.strip()
        except Exception as e:
            print(f"Lỗi khi đọc sheet {sheet}: {e}")
            continue

        df_filtered = df[df["Mã"] == stock_code]
        if df_filtered.empty:
            continue

        available = [col for col in desired_columns if col in df_filtered.columns]
        df_selected = df_filtered[available].copy()

        if result_df.empty:
            result_df = df_selected
        else:
            result_df = pd.merge(result_df, df_selected, on="Mã", how="outer", suffixes=("", f"_{sheet}"))

    # Chuyển đổi các giá trị số từ triệu sang tỷ VND (chia cho 1000)
    numeric_cols = result_df.select_dtypes(include=["number"]).columns
    result_df[numeric_cols] = result_df[numeric_cols] / 1000

    return result_df

def income_statement(stock_code):
    """
    Đọc dữ liệu kết quả kinh doanh từ file Excel local và chuyển đổi đơn vị từ triệu sang tỷ VND.
    """
    file_path = os.path.join(
        "\\Data\\Data cleaned",
        "data_KQKD.xlsx"
    )
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    sheets = ["data1_KQKD", "data2_KQKD", "data3_KQKD", "data4_KQKD", "data5_KQKD"]
    desired_columns = [
        "Mã", "Doanh thu thuần", "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ",
        "Lợi nhuận thuần từ hoạt động kinh doanh", "Tổng lợi nhuận kế toán trước thuế",
        "Lợi nhuận sau thuế thu nhập doanh nghiệp"
    ]
    result_df = pd.DataFrame()

    for sheet in sheets:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet)
            df.columns = df.columns.str.strip()
        except Exception as e:
            print(f"Lỗi khi đọc sheet {sheet}: {e}")
            continue

        df_filtered = df[df["Mã"] == stock_code]
        if df_filtered.empty:
            continue

        available = [col for col in desired_columns if col in df_filtered.columns]
        df_selected = df_filtered[available].copy()

        if result_df.empty:
            result_df = df_selected
        else:
            result_df = pd.merge(result_df, df_selected, on="Mã", how="outer", suffixes=("", f"_{sheet}"))

    # Chuyển đổi các giá trị số từ triệu sang tỷ VND (chia cho 1000)
    numeric_cols = result_df.select_dtypes(include=["number"]).columns
    result_df[numeric_cols] = result_df[numeric_cols] / 1000

    return result_df

def cash_flow(stock_code):
    """
    Đọc dữ liệu lưu chuyển tiền tệ từ file Excel local và chuyển đổi đơn vị từ triệu sang tỷ VND.
    """
    file_path = os.path.join(
        "\\Data\\Data cleaned",
        "data_LCTT.xlsx"
    )
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    sheets = ["data1_LCTT", "data2_LCTT", "data3_LCTT", "data4_LCTT", "data5_LCTT"]
    desired_columns = [
        "Mã", "Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh (TT)",
        "Lưu chuyển tiền tệ ròng từ hoạt động đầu tư (TT)",
        "Lưu chuyển tiền tệ từ hoạt động tài chính (TT)",
        "Lưu chuyển tiền thuần trong kỳ (TT)"
    ]
    result_df = pd.DataFrame()

    for sheet in sheets:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet)
            df.columns = df.columns.str.strip()
        except Exception as e:
            print(f"Lỗi khi đọc sheet {sheet}: {e}")
            continue

        df_filtered = df[df["Mã"] == stock_code]
        if df_filtered.empty:
            continue

        available = [col for col in desired_columns if col in df_filtered.columns]
        df_selected = df_filtered[available].copy()

        if result_df.empty:
            result_df = df_selected
        else:
            result_df = pd.merge(result_df, df_selected, on="Mã", how="outer", suffixes=("", f"_{sheet}"))

    # Chuyển đổi các giá trị số từ triệu sang tỷ VND (chia cho 1000)
    numeric_cols = result_df.select_dtypes(include=["number"]).columns
    result_df[numeric_cols] = result_df[numeric_cols] / 1000

    return result_df

def industry_classification(stock_code):
    """
    Đọc thông tin phân loại ngành từ file Excel local.
    """
    file_path = os.path.join(
        "\\Data\\Data cleaned",
        "Phan_loai_nganh(cleaned).xlsx"
    )
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
    except Exception as e:
        raise Exception(f"Lỗi khi đọc file phân loại ngành: {e}")

    df_filtered = df[df["Mã"] == stock_code]
    if df_filtered.empty:
        print(f"Không tìm thấy dữ liệu cho mã cổ phiếu {stock_code}.")
        return pd.DataFrame()

    desired = ["Mã", "Tên công ty", "Sàn", "Ngành ICB - cấp 1", "Ngành ICB - cấp 2", "Ngành ICB - cấp 3", "Ngành ICB - cấp 4"]
    available = [col for col in desired if col in df_filtered.columns]
    return df_filtered[available].copy()


#########################################
# NHÓM 2: DỮ LIỆU TỪ VNCSTOCK - NGUỒN VCI (source="VCI")
#########################################

def get_stock_and_exchange_history_vci(stock_code):
    """
    Lấy lịch sử giá đóng cửa của cổ phiếu và chỉ số sàn từ nguồn VCI.
      - Cổ phiếu được lấy từ mã stock_code.
      - Chỉ số được xác định dựa trên cột "Sàn" từ industry_classification:
          HOSE -> VNINDEX, HNX -> HNXINDEX, UPCOM -> UPCOMINDEX.
    """
    df_class = industry_classification(stock_code)
    if df_class.empty:
        print("Không có thông tin phân loại ngành. Không thể xác định sàn giao dịch.")
        return pd.DataFrame(), pd.DataFrame()

    exchange = df_class.iloc[0]["Sàn"].strip().upper()
    if exchange == "HOSE":
        index_symbol = "VNINDEX"
    elif exchange == "HNX":
        index_symbol = "HNXINDEX"
    elif exchange == "UPCOM":
        index_symbol = "UPCOMINDEX"
    else:
        print(f"Sàn giao dịch '{exchange}' không được hỗ trợ.")
        index_symbol = None

    stock_obj = Vnstock().stock(symbol=stock_code, source="VCI")
    df_stock = stock_obj.quote.history(start="2023-01-01", end="2025-03-01", interval="1D")
    df_stock = df_stock.reset_index()

    if index_symbol is not None:
        index_obj = Vnstock().stock(symbol=index_symbol, source="VCI")
        df_index = index_obj.quote.history(start="2023-01-01", end="2025-03-01", interval="1D")
        df_index = df_index.reset_index()
    else:
        df_index = pd.DataFrame()

    if "close" in df_stock.columns:
        df_stock = df_stock[["time", "close"]]
    if not df_index.empty and "close" in df_index.columns:
        df_index = df_index[["time", "close"]]

    return df_stock, df_index

def get_stock_volume_vci(stock_code):
    """
    Lấy cột "volume" của mã cổ phiếu từ nguồn VCI.
    Chỉ lấy dữ liệu của cổ phiếu (không bao gồm dữ liệu của sàn giao dịch),
    bổ sung thêm cột "time" canh với cột "volume".
    """
    stock_obj = Vnstock().stock(symbol=stock_code, source="VCI")
    df_stock = stock_obj.quote.history(start="2023-01-01", end="2025-03-01", interval="1D")
    df_stock = df_stock.reset_index()

    if "volume" in df_stock.columns:
        df_stock = df_stock[["time", "volume"]]
        return df_stock
    else:
        print(f"Không có dữ liệu volume cho mã cổ phiếu: {stock_code}")
        return pd.DataFrame()

def get_top_shareholders_vci(stock_code, top_n=10):
    """
    Lấy Top các cổ đông của công ty từ nguồn VCI.
    """
    try:
        company_obj = Vnstock().stock(symbol=stock_code, source="VCI").company
        df_shareholders = company_obj.shareholders()
        if df_shareholders.empty:
            print(f"Không có thông tin cổ đông cho mã {stock_code} từ VCI.")
            return pd.DataFrame()
        return df_shareholders.head(top_n)
    except Exception as e:
        print(f"Lỗi khi lấy thông tin cổ đông của {stock_code} từ VCI: {e}")
        return pd.DataFrame()

def get_executives_vci(stock_code, filter_by='working'):
    """
    Lấy danh sách ban lãnh đạo của công ty từ nguồn VCI.
    Chỉ lấy 10 người đầu tiên nếu danh sách có nhiều hơn 10 người.
    """
    try:
        company_obj = Vnstock().stock(symbol=stock_code, source="VCI").company
        df_officers = company_obj.officers(filter_by=filter_by)
        if df_officers.empty:
            print(f"Không có thông tin ban lãnh đạo ({filter_by}) cho mã {stock_code} từ VCI.")
        else:
            df_officers = df_officers.head(9)
        return df_officers
    except Exception as e:
        print(f"Lỗi khi lấy thông tin ban lãnh đạo của {stock_code} từ VCI: {e}")
        return pd.DataFrame()

def get_financial_ratios_vci(stock_code, period='year', lang='vi', dropna=True):
    """
    Lấy thông tin tỷ số tài chính của công ty từ nguồn VCI.
    
    Ví dụ sử dụng:
        stock.finance.ratio(period='year', lang='vi', dropna=True).head()
    
    Trả về 5 dòng đầu tiên của DataFrame có định dạng:
      Meta, Chỉ tiêu cơ cấu nguồn vốn, Chỉ tiêu khả năng sinh lợi, Chỉ tiêu thanh khoản, Chỉ tiêu định giá, ...
    
    Nếu xảy ra lỗi, hàm sẽ in ra thông báo và trả về một DataFrame rỗng.
    """
    try:
        stock_obj = Vnstock().stock(symbol=stock_code, source='VCI')
        ratios = stock_obj.finance.ratio(period=period, lang=lang, dropna=dropna).head()
        return ratios
    except Exception as e:
        print(f"Lỗi khi lấy thông tin tài chính của {stock_code} từ VCI: {e}")
        return pd.DataFrame()


#########################################
# NHÓM 3: DỮ LIỆU TỪ VNCSTOCK - NGUỒN TCBS (source="TCBS")
#########################################

def get_company_overview_tcbs(stock_code):
    """
    Lấy thông tin tổng quan của công ty từ nguồn TCBS thông qua thư viện Vnstock.
    
    Sử dụng phương thức company.overview() của đối tượng company từ Vnstock với source='TCBS'.
    
    Trả về một DataFrame chứa thông tin tổng quan của công ty. Nếu có lỗi, in ra thông báo và trả về DataFrame rỗng.
    """
    try:
        company_obj = Vnstock().stock(symbol=stock_code, source='TCBS').company
        overview_df = company_obj.overview()
        return overview_df
    except Exception as e:
        print(f"Lỗi khi lấy thông tin tổng quan của {stock_code} từ TCBS: {e}")
        return pd.DataFrame()

def get_company_profile_tcbs(stock_code):
    """
    Lấy thông tin hồ sơ công ty từ nguồn TCBS thông qua thư viện Vnstock.
    
    Sử dụng phương thức company.profile() của đối tượng company từ Vnstock với source='TCBS'.
    
    Trả về một DataFrame chứa thông tin hồ sơ của công ty. Nếu có lỗi, in ra thông báo và trả về DataFrame rỗng.
    """
    try:
        company_obj = Vnstock().stock(symbol=stock_code, source='TCBS').company
        profile_df = company_obj.profile()
        return profile_df
    except Exception as e:
        print(f"Lỗi khi lấy thông tin hồ sơ của {stock_code} từ TCBS: {e}")
        return pd.DataFrame()

def get_subsidiaries_tcbs(stock_code):
    """
    Lấy danh sách công ty con của công ty từ nguồn TCBS.
    Chỉ lấy top 10 công ty có giá trị "sub_own_percent" lớn nhất.
    """
    try:
        company_obj = Vnstock().stock(symbol=stock_code, source="TCBS").company
        df_subsidiaries = company_obj.subsidiaries()
        if df_subsidiaries.empty:
            print(f"Không có thông tin công ty con cho mã {stock_code} từ TCBS.")
        else:
            if "sub_own_percent" in df_subsidiaries.columns:
                df_subsidiaries = df_subsidiaries.sort_values(by="sub_own_percent", ascending=False).head(5)
            else:
                print("Không tìm thấy cột 'sub_own_percent' trong dữ liệu công ty con.")
        return df_subsidiaries
    except Exception as e:
        print(f"Lỗi khi lấy thông tin công ty con của {stock_code} từ TCBS: {e}")
        return pd.DataFrame()
