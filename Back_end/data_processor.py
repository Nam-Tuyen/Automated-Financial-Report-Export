import os
import sys
import pandas as pd
from vnstock import Quote, Company, Finance, Vnstock
from pathlib import Path
from paths import DATA_CLEANED_DIR

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

#########################################
# NHÓM 1: HÀM ĐỌC DỮ LIỆU TỪ FILE EXCEL (LOCAL)
#########################################

def balance_sheet(stock_code):
    """
    Đọc dữ liệu cân đối kế toán từ file Excel local và chuyển đổi đơn vị từ triệu sang tỷ VND.
    Sử dụng file "data_CĐKT.xlsx".
    """
    file_path = str((DATA_CLEANED_DIR / "data_CĐKT.xlsx").resolve())
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    sheets = ["data1_CĐKT", "data2_CĐKT", "data3_CĐKT", "data4_CĐKT", "data5_CĐKT"]
    desired_columns = [
        "Mã", "Năm",
        # TÀI SẢN NGẮN HẠN
        "TÀI SẢN NGẮN HẠN", "Tiền và tương đương tiền", "Đầu tư tài chính ngắn hạn",
        "Các khoản phải thu ngắn hạn", "Hàng tồn kho, ròng", "Tài sản ngắn hạn khác",
        # TÀI SẢN DÀI HẠN
        "TÀI SẢN DÀI HẠN", "Phải thu dài hạn", "Tài sản cố định",
        "GTCL TSCĐ hữu hình", "GTCL Tài sản thuê tài chính", "GTCL tài sản cố định vô hình",
        "Xây dựng cơ bản dở dang (trước 2015)", "Giá trị ròng tài sản đầu tư",
        "Tài sản dở dang dài hạn", "Đầu tư dài hạn", "Lợi thế thương mại (trước 2015)",
        "Tài sản dài hạn khác", "Lợi thế thương mại",
        # TỔNG CỘNG TÀI SẢN
        "TỔNG CỘNG TÀI SẢN",
        # NỢ PHẢI TRẢ
        "NỢ PHẢI TRẢ", "Nợ ngắn hạn", "Phải trả người bán ngắn hạn",
        "Người mua trả tiền trước ngắn hạn", "Doanh thu chưa thực hiện ngắn hạn",
        "Vay và nợ thuê tài chính ngắn hạn", "Nợ dài hạn", "Phải trả nhà cung cấp dài hạn",
        "Người mua trả tiền trước dài hạn", "Doanh thu chưa thực hiên dài hạn",
        "Vay và nợ thuê tài chính dài hạn",
        # VỐN CHỦ SỞ HỮU
        "VỐN CHỦ SỞ HỮU", "Vốn và các quỹ", "Vốn góp của chủ sở hữu",
        "Thặng dư vốn cổ phần", "Vốn khác", "Lãi chưa phân phối",
        "LNST chưa phân phối lũy kế đến cuối kỳ trước", "LNST chưa phân phối kỳ này",
        "Lợi ích cổ đông không kiểm soát", "Nguồn kinh phí và quỹ khác",
        "LỢI ÍCH CỦA CỔ ĐÔNG KHÔNG KIỂM SOÁT (trước 2015)",
        # TỔNG CỘNG NGUỒN VỐN
        "TỔNG CỘNG NGUỒN VỐN"
    ]
    result_df = pd.DataFrame()

    for sheet in sheets:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl')
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
    file_path = str((DATA_CLEANED_DIR / "data_KQKD.xlsx").resolve())
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    sheets = ["data1_KQKD", "data2_KQKD", "data3_KQKD", "data4_KQKD", "data5_KQKD"]
    desired_columns = [
        "Mã", "Năm",
        # Doanh thu
        "Doanh thu bán hàng và cung cấp dịch vụ", "Doanh thu thuần",
        "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ",
        # Hoạt động tài chính
        "Doanh thu hoạt động tài chính", "Chi phí tài chính",
        "Trong đó: Chi phí lãi vay",
        # Công ty liên doanh
        "Lãi/lỗ từ công ty liên doanh",
        # Chi phí
        "Chi phí bán hàng", "Chi phí quản lý doanh nghiệp",
        # Lợi nhuận
        "Lợi nhuận thuần từ hoạt động kinh doanh", "Lợi nhuận khác",
        "Lãi/ lỗ từ công ty liên doanh (trước 2015)",
        "Tổng lợi nhuận kế toán trước thuế",
        # Thuế và lợi nhuận sau thuế
        "Chi phí thuế thu nhập doanh nghiệp",
        "Lợi nhuận sau thuế thu nhập doanh nghiệp",
        # Cổ đông
        "Lợi ích của cổ đông thiểu số", "Cổ đông của Công ty mẹ",
        # Chỉ số
        "Lãi cơ bản trên cổ phiếu"
    ]
    result_df = pd.DataFrame()

    for sheet in sheets:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl')
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
    file_path = str((DATA_CLEANED_DIR / "data_LCTT.xlsx").resolve())
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    sheets = ["data1_LCTT", "data2_LCTT", "data3_LCTT", "data4_LCTT", "data5_LCTT"]
    desired_columns = [
        "Mã", "Năm",
        # Hoạt động sản xuất kinh doanh
        "Lãi trước thuế", "Khấu hao TSCĐ",
        "Lãi/(lỗ) trước những thay đổi vốn lưu động",
        "Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh (TT)",
        # Hoạt động đầu tư
        "Tiền chi để mua sắm, xây dựng TSCĐ và các tài sản dài hạn khác (TT)",
        "Tiền thu từ thanh lý, nhượng bán TSCĐ và các tài sản dài hạn khác (TT)",
        "Tiền chi cho vay, mua các công cụ nợ của đợn vị khác (TT)",
        "Tiền thu hồi cho vay, bán lại các công cụ nợ của đơn vị khác (TT)",
        "Lưu chuyển tiền tệ ròng từ hoạt động đầu tư (TT)",
        "Đầu tư vào doanh nghiệp khác",
        # Hoạt động tài chính
        "Tiền thu từ phát hành cổ phiếu, nhận góp vốn của chủ sở hữu (TT)",
        "Tiền trả lại vốn góp cho các chủ sở hữu, mua lại cổ phiếu của doanh nghiệp đã phát hành (TT)",
        "Tiền thu được các khoản đi vay (TT)",
        "Tiền trả nợ gốc vay (TT)",
        "Tiền thanh toán vốn gốc đi thuê tài chính (TT)",
        "Cổ tức đã trả (TT)",
        "Lưu chuyển tiền tệ từ hoạt động tài chính (TT)",
        # Tổng hợp và cuối kỳ
        "Lưu chuyển tiền thuần trong kỳ (TT)",
        "Tiền và tương đương tiền đầu kỳ (TT)",
        "Ảnh hưởng của chênh lệch tỷ giá (TT)",
        "Tiền và tương đương tiền cuối kỳ (TT)"
    ]
    result_df = pd.DataFrame()

    for sheet in sheets:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl')
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

def bctckh_data(stock_code):
    """
    Đọc dữ liệu báo cáo tài chính hợp nhất từ file Excel local và chuyển đổi đơn vị từ triệu sang tỷ VND.
    Sử dụng file "data_BCTCKH.xlsx" với các sheet data1_BCTCKH, data2_BCTCKH, data3_BCTCKH, data4_BCTCKH, data5_BCTCKH.
    """
    file_path = str((DATA_CLEANED_DIR / "data_BCTCKH.xlsx").resolve())
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    sheets = ["data1_BCTCKH", "data2_BCTCKH", "data3_BCTCKH", "data4_BCTCKH", "data5_BCTCKH"]
    desired_columns = [
        "Mã", "Năm", "Doanh thu kế hoạch",
        "Tổng lợi nhuận kế toán trước thuế",
        "Lợi nhuận sau thuế thu nhập doanh nghiệp"
    ]
    result_df = pd.DataFrame()

    for sheet in sheets:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl')
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

def tm_data(stock_code):
    """
    Đọc dữ liệu thương mại từ file Excel local và chuyển đổi đơn vị từ triệu sang tỷ VND.
    Sử dụng file "data_TM.xlsx" với các sheet data1_TM, data2_TM, data3_TM, data4_TM, data5_TM.
    """
    file_path = str((DATA_CLEANED_DIR / "data_TM.xlsx").resolve())
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    sheets = ["data1__TM", "data2__TM", "data3__TM", "data4__TM", "data5__TM"]
    desired_columns = [
        "Mã", "Năm",
        # Tiền và tương đương tiền
        "Tiền", "Tiền mặt", "Tiền gửi Ngân hàng", "Tiền đang chuyển",
        "Tiền và tương đương tiền",
        # Đầu tư tài chính ngắn hạn
        "Đầu tư tài chính NH", "Chứng khoán đầu tư ngắn hạn",
        "Đầu tư nắm giữ đến ngày đáo hạn", "Đầu tư ngắn hạn",
        "Đầu tư NH khác", "Dự phòng giảm giá ĐTNH",
        # Hàng tồn kho
        "Hàng tồn kho", "Hàng mua đang đi đường", "Nguyên liệu, vật liệu",
        "Công cụ, dụng cụ", "Chi phí SX, KD dở dang", "Thành phẩm",
        "Hàng hóa", "Hàng gửi đi bán", "Hàng hoá kho bảo thuế",
        "Hàng hoá bất động sản",
        # Đầu tư dài hạn
        "Đầu tư dài hạn", "Đầu tư dài hạn khác", "Đầu tư cổ phiếu",
        "Đầu tư trái phiếu", "Đầu tư tín phiếu, kỳ phiếu",
        "Cho vay dài hạn", "Đầu tư dài hạn khác.1",
        # Vay và nợ
        "Vay và nợ ngắn hạn", "Vay ngắn hạn", "Vay dài hạn đến hạn trả",
        # Lợi thế thương mại
        "Giá gốc Lợi thế thương mại", "Số dư đầu kỳ", "Tăng trong kỳ",
        "Giảm trong kỳ", "Phân bổ Lũy kế",
        "Số dư dầu kỳ", "Tăng trong kỳ.1", "Giảm trong kỳ.1",
        # Vay dài hạn
        "Vay Dài hạn", "Vay ngân hàng", "Vay đối tượng khác",
        "Trái phiếu phát hành", "Thuê tài chính", "Nợ dài hạn khác",
        # Vốn chủ sở hữu
        "Vốn chủ sở hữu", "Vốn chủ sở hữu.1", "Vốn đầu tư của đối tượng khác",
        # Doanh thu và chi phí tài chính
        "Lãi tiền gửi, tiền cho vay", "Lãi đầu tư trái phiếu, kỳ phiếu, tín phiếu",
        "Cổ tức, lợi nhuận được chia", "Lãi từ bán, thanh lý các khoản đầu tư",
        "Lãi bán ngoại tệ", "Lãi chênh lệch tỷ giá đã thực hiện",
        "Lãi chênh lệch tỷ giá chưa thực hiện", "Lãi bán hành trả chậm",
        "Doanh thu hoạt động tài chính khác", "Chi phí tài chính",
        "Lãi tiền vay", "Chiết khấu thanh toán, lãi bán hàng trả chậm",
        "Lỗ do thanh lý các khoản đầu tư ngắn hạn, dài hạn", "Lỗ bán ngoại tệ",
        "Lỗ chênh lệch tỷ giá đã thực hiện", "Lỗ chênh lệch tỷ giá chưa thực hiện",
        "Dự phòng giảm giá các khoản đầu tư ngắn hạn, dài hạn",
        "Chi phí tài chính khác",
        # Chi phí sản xuất theo yếu tố
        "Chi phí sản xuất theo yếu tố", "Chi phí nguyên liệu, vật liệu",
        "Chi phí nhân công", "Chi phí khấu hao tài sản cố định",
        "Chi phí dịch vụ mua ngoài", "Chi phí khác bằng tiền"
    ]
    result_df = pd.DataFrame()

    for sheet in sheets:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl')
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
    file_path = str((DATA_CLEANED_DIR / "Phan_loai_nganh(cleaned).xlsx").resolve())
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    try:
        df = pd.read_excel(file_path, engine='openpyxl')
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

    # Sử dụng API mới: Quote
    quote_stock = Quote(symbol=stock_code, source="VCI")
    df_stock = quote_stock.history(start="2023-01-01", end="2025-03-01", interval="1D")
    if hasattr(df_stock, 'reset_index'):
        df_stock = df_stock.reset_index()

    if index_symbol is not None:
        quote_index = Quote(symbol=index_symbol, source="VCI")
        df_index = quote_index.history(start="2023-01-01", end="2025-03-01", interval="1D")
        if hasattr(df_index, 'reset_index'):
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
    # Sử dụng API mới: Quote
    quote = Quote(symbol=stock_code, source="VCI")
    df_stock = quote.history(start="2023-01-01", end="2025-03-01", interval="1D")
    if hasattr(df_stock, 'reset_index'):
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
        # Sử dụng API mới: Company
        company = Company(symbol=stock_code, source="VCI")
        df_shareholders = company.shareholders()
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
        # Sử dụng API mới: Company
        company = Company(symbol=stock_code, source="VCI")
        df_officers = company.officers(filter_by=filter_by)
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
        finance.ratio(period='year', lang='vi', dropna=True).head()
    
    Trả về 5 dòng đầu tiên của DataFrame có định dạng:
      Meta, Chỉ tiêu cơ cấu nguồn vốn, Chỉ tiêu khả năng sinh lợi, Chỉ tiêu thanh khoản, Chỉ tiêu định giá, ...
    
    Nếu xảy ra lỗi, hàm sẽ in ra thông báo và trả về một DataFrame rỗng.
    """
    try:
        # Sử dụng API mới: Finance
        finance = Finance(symbol=stock_code, source='VCI')
        ratios = finance.ratio(period=period, lang=lang, dropna=dropna).head()
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
    
    Sử dụng Company với source='TCBS' theo API mới.
    
    Trả về một DataFrame chứa thông tin tổng quan của công ty. Nếu có lỗi, in ra thông báo và trả về DataFrame rỗng.
    """
    try:
        # Sử dụng API mới: Company với source='TCBS'
        # TCBS vẫn có thể dùng Vnstock().stock() hoặc Company trực tiếp
        company = Company(symbol=stock_code, source='TCBS')
        overview_df = company.overview()
        return overview_df
    except Exception as e:
        # Fallback về cách cũ nếu API mới không hỗ trợ
        try:
            company_obj = Vnstock().stock(symbol=stock_code, source='TCBS').company
            overview_df = company_obj.overview()
            return overview_df
        except Exception as e2:
            print(f"Lỗi khi lấy thông tin tổng quan của {stock_code} từ TCBS: {e2}")
            return pd.DataFrame()

def get_company_profile_tcbs(stock_code):
    """
    Lấy thông tin hồ sơ công ty từ nguồn TCBS thông qua thư viện Vnstock.
    
    Sử dụng Company với source='TCBS' theo API mới.
    
    Trả về một DataFrame chứa thông tin hồ sơ của công ty. Nếu có lỗi, in ra thông báo và trả về DataFrame rỗng.
    """
    try:
        # Sử dụng API mới: Company với source='TCBS'
        company = Company(symbol=stock_code, source='TCBS')
        profile_df = company.profile()
        return profile_df
    except Exception as e:
        # Fallback về cách cũ nếu API mới không hỗ trợ
        try:
            company_obj = Vnstock().stock(symbol=stock_code, source='TCBS').company
            profile_df = company_obj.profile()
            return profile_df
        except Exception as e2:
            print(f"Lỗi khi lấy thông tin hồ sơ của {stock_code} từ TCBS: {e2}")
            return pd.DataFrame()

def get_subsidiaries_tcbs(stock_code):
    """
    Lấy danh sách công ty con của công ty từ nguồn TCBS.
    Chỉ lấy top 10 công ty có giá trị "sub_own_percent" lớn nhất.
    """
    try:
        # Sử dụng API mới: Company với source='TCBS'
        company = Company(symbol=stock_code, source="TCBS")
        df_subsidiaries = company.subsidiaries()
        if df_subsidiaries.empty:
            print(f"Không có thông tin công ty con cho mã {stock_code} từ TCBS.")
        else:
            if "sub_own_percent" in df_subsidiaries.columns:
                df_subsidiaries = df_subsidiaries.sort_values(by="sub_own_percent", ascending=False).head(5)
            else:
                print("Không tìm thấy cột 'sub_own_percent' trong dữ liệu công ty con.")
        return df_subsidiaries
    except Exception as e:
        # Fallback về cách cũ nếu API mới không hỗ trợ
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
        except Exception as e2:
            print(f"Lỗi khi lấy thông tin công ty con của {stock_code} từ TCBS: {e2}")
            return pd.DataFrame()
