import re
import pandas as pd
from data_processor import balance_sheet, income_statement, cash_flow, get_financial_ratios_vci
from datetime import datetime

def balance_sheet_final(df):
    r"""
    Làm phẳng dữ liệu của df_balance_sheet và gộp các cột lại theo chỉ tiêu tài chính.
    Ánh xạ hậu tố của tên cột thành năm như sau:
      - Nếu không có hậu tố: năm = 2020.
      - Nếu có hậu tố với số X:
            X = 2 -> năm 2021
            X = 3 -> năm 2022
            X = 4 -> năm 2023
            X = 5 -> năm 2024
    Tạo DataFrame với các dòng:
      "Mã cổ phiếu", "TÀI SẢN NGẮN HẠN", "TÀI SẢN DÀI HẠN", "TỔNG CỘNG TÀI SẢN",
      "Nợ ngắn hạn", "Nợ dài hạn", "NỢ PHẢI TRẢ", "VỐN CHỦ SỞ HỮU", "TỔNG CỘNG NGUỒN VỐN"
    Và các cột ứng với năm 2020 đến 2024.
    Nếu không có dữ liệu cho năm nào, giá trị là None.
    Sau đó, với các giá trị số:
      - Năm 2020, 2021, 2022 chia cho 1,000,000,000
      - Năm 2023, 2024 chia cho 1,000.
    Cuối cùng, định dạng (ngoại trừ "Mã cổ phiếu") với 3 chữ số sau dấu thập phân.
    """
    stock_code = df["Mã"].iloc[0] if "Mã" in df.columns else None

    flat_data = {}
    for col in df.columns:
        if col == "Mã":
            continue
        parts = col.split("_")
        base = parts[0].strip()
        if len(parts) == 1:
            year = 2020
        else:
            match = re.search(r'\d+', parts[1])
            if match:
                num = int(match.group())
                if num == 2:
                    year = 2021
                elif num == 3:
                    year = 2022
                elif num == 4:
                    year = 2023
                elif num == 5:
                    year = 2024
                else:
                    continue
            else:
                year = 2020
        value = df[col].iloc[0]
        flat_data.setdefault(base, {})[year] = value

    years = [2020, 2021, 2022, 2023, 2024]
    data_rows = []
    row_labels = []
    for base, year_values in flat_data.items():
        row = [year_values.get(y, None) for y in years]
        data_rows.append(row)
        row_labels.append(base)
    df_flat = pd.DataFrame(data_rows, index=row_labels, columns=[str(y) for y in years])

    stock_row = pd.DataFrame([[stock_code] * len(years)], index=["Mã cổ phiếu"], columns=[str(y) for y in years])
    df_result = pd.concat([stock_row, df_flat])

    desired_order = ["Mã cổ phiếu", "TÀI SẢN NGẮN HẠN", "TÀI SẢN DÀI HẠN", 
                     "TỔNG CỘNG TÀI SẢN", "Nợ ngắn hạn", "Nợ dài hạn", 
                     "NỢ PHẢI TRẢ", "VỐN CHỦ SỞ HỮU", "TỔNG CỘNG NGUỒN VỐN"]
    ordered_rows = [r for r in desired_order if r in df_result.index]
    remaining = [r for r in df_result.index if r not in ordered_rows]
    final_order = ordered_rows + remaining
    df_result = df_result.reindex(final_order)

    for year in ["2020", "2021", "2022"]:
        if year in df_result.columns:
            mask = df_result.index != "Mã cổ phiếu"
            df_result.loc[mask, year] = pd.to_numeric(df_result.loc[mask, year], errors='coerce') / 1_000_000_000
    for year in ["2023", "2024"]:
        if year in df_result.columns:
            mask = df_result.index != "Mã cổ phiếu"
            df_result.loc[mask, year] = pd.to_numeric(df_result.loc[mask, year], errors='coerce') / 1_000

    numeric_mask = df_result.index != "Mã cổ phiếu"
    df_result.loc[numeric_mask] = df_result.loc[numeric_mask].applymap(
        lambda x: f"{x:.3f}" if pd.notnull(x) else x
    )

    return df_result

def income_statement_final(df):
    r"""
    Làm phẳng dữ liệu của df_income_statement và gộp các cột lại theo các chỉ tiêu tài chính.
    Ánh xạ hậu tố của tên cột thành năm như sau:
      - Nếu không có hậu tố: năm = 2020.
      - Nếu có hậu tố với số X:
            X = 2 -> năm 2021
            X = 3 -> năm 2022
            X = 4 -> năm 2023
            X = 5 -> năm 2024
    Tạo DataFrame với các dòng:
      "Mã cổ phiếu", "Doanh thu thuần", "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ",
      "Lợi nhuận thuần từ hoạt động kinh doanh", "Tổng lợi nhuận kế toán trước thuế",
      "Lợi nhuận sau thuế thu nhập doanh nghiệp"
    Và các cột ứng với năm 2020 đến 2024.
    Sau đó, với các giá trị số:
      - Năm 2020, 2021, 2022 chia cho 1,000,000,000
      - Năm 2023, 2024 chia cho 1,000.
    Cuối cùng, định dạng (ngoại trừ "Mã cổ phiếu") với 3 chữ số sau dấu thập phân.
    """
    stock_code = df["Mã"].iloc[0] if "Mã" in df.columns else None

    flat_data = {}
    for col in df.columns:
        if col == "Mã":
            continue
        parts = col.split("_")
        base = parts[0].strip()
        if len(parts) == 1:
            year = 2020
        else:
            match = re.search(r'\d+', parts[1])
            if match:
                num = int(match.group())
                if num == 2:
                    year = 2021
                elif num == 3:
                    year = 2022
                elif num == 4:
                    year = 2023
                elif num == 5:
                    year = 2024
                else:
                    continue
            else:
                year = 2020
        value = df[col].iloc[0]
        flat_data.setdefault(base, {})[year] = value

    years = [2020, 2021, 2022, 2023, 2024]
    data_rows = []
    row_labels = []
    for base, year_values in flat_data.items():
        row = [year_values.get(y, None) for y in years]
        data_rows.append(row)
        row_labels.append(base)
    df_flat = pd.DataFrame(data_rows, index=row_labels, columns=[str(y) for y in years])

    stock_row = pd.DataFrame([[stock_code] * len(years)], index=["Mã cổ phiếu"], columns=[str(y) for y in years])
    df_result = pd.concat([stock_row, df_flat])

    desired_order = [
        "Mã cổ phiếu", 
        "Doanh thu thuần", 
        "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ",
        "Lợi nhuận thuần từ hoạt động kinh doanh", 
        "Tổng lợi nhuận kế toán trước thuế",
        "Lợi nhuận sau thuế thu nhập doanh nghiệp"
    ]
    ordered_rows = [r for r in desired_order if r in df_result.index]
    remaining = [r for r in df_result.index if r not in ordered_rows]
    final_order = ordered_rows + remaining
    df_result = df_result.reindex(final_order)

    for year in ["2020", "2021", "2022"]:
        if year in df_result.columns:
            mask = df_result.index != "Mã cổ phiếu"
            df_result.loc[mask, year] = pd.to_numeric(df_result.loc[mask, year], errors='coerce') / 1_000_000_000
    for year in ["2023", "2024"]:
        if year in df_result.columns:
            mask = df_result.index != "Mã cổ phiếu"
            df_result.loc[mask, year] = pd.to_numeric(df_result.loc[mask, year], errors='coerce') / 1_000

    numeric_mask = df_result.index != "Mã cổ phiếu"
    df_result.loc[numeric_mask] = df_result.loc[numeric_mask].applymap(
        lambda x: f"{x:.3f}" if pd.notnull(x) else x
    )

    return df_result

def cash_flow_final(df):
    r"""
    Làm phẳng dữ liệu của df_cash_flow và gộp các cột lại theo các chỉ tiêu của lưu chuyển tiền tệ.
    Ánh xạ hậu tố của tên cột thành năm như sau:
      - Nếu không có hậu tố: năm = 2020.
      - Nếu có hậu tố với số X:
            X = 2 -> năm 2021
            X = 3 -> năm 2022
            X = 4 -> năm 2023
            X = 5 -> năm 2024
    Tạo DataFrame với các dòng:
      "Mã cổ phiếu", 
      "Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh (TT)",
      "Lưu chuyển tiền tệ ròng từ hoạt động đầu tư (TT)",
      "Lưu chuyển tiền tệ từ hoạt động tài chính (TT)",
      "Lưu chuyển tiền thuần trong kỳ (TT)"
    Và các cột ứng với năm 2020 đến 2024.
    Sau đó, với các giá trị số:
      - Năm 2020, 2021, 2022 chia cho 1,000,000,000 
      - Năm 2023, 2024 chia cho 1,000.
    Cuối cùng, định dạng các giá trị số (ngoại trừ dòng "Mã cổ phiếu")
    thành chuỗi với 3 chữ số sau dấu thập phân.
    """
    stock_code = df["Mã"].iloc[0] if "Mã" in df.columns else None

    flat_data = {}
    for col in df.columns:
        if col == "Mã":
            continue
        parts = col.split("_")
        base = parts[0].strip()
        if len(parts) == 1:
            year = 2020
        else:
            match = re.search(r'\d+', parts[1])
            if match:
                num = int(match.group())
                if num == 2:
                    year = 2021
                elif num == 3:
                    year = 2022
                elif num == 4:
                    year = 2023
                elif num == 5:
                    year = 2024
                else:
                    continue
            else:
                year = 2020
        value = df[col].iloc[0]
        flat_data.setdefault(base, {})[year] = value

    years = [2020, 2021, 2022, 2023, 2024]
    data_rows = []
    row_labels = []
    for base, year_values in flat_data.items():
        row = [year_values.get(y, None) for y in years]
        data_rows.append(row)
        row_labels.append(base)
    df_flat = pd.DataFrame(data_rows, index=row_labels, columns=[str(y) for y in years])

    stock_row = pd.DataFrame([[stock_code] * len(years)], index=["Mã cổ phiếu"], columns=[str(y) for y in years])
    df_result = pd.concat([stock_row, df_flat])

    desired_order = [
        "Mã cổ phiếu",
        "Lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh (TT)",
        "Lưu chuyển tiền tệ ròng từ hoạt động đầu tư (TT)",
        "Lưu chuyển tiền tệ từ hoạt động tài chính (TT)",
        "Lưu chuyển tiền thuần trong kỳ (TT)"
    ]
    ordered_rows = [r for r in desired_order if r in df_result.index]
    remaining = [r for r in df_result.index if r not in ordered_rows]
    final_order = ordered_rows + remaining
    df_result = df_result.reindex(final_order)

    for year in ["2020", "2021", "2022"]:
        if year in df_result.columns:
            mask = df_result.index != "Mã cổ phiếu"
            df_result.loc[mask, year] = pd.to_numeric(df_result.loc[mask, year], errors='coerce') / 1_000_000_000
    for year in ["2023", "2024"]:
        if year in df_result.columns:
            mask = df_result.index != "Mã cổ phiếu"
            df_result.loc[mask, year] = pd.to_numeric(df_result.loc[mask, year], errors='coerce') / 1_000

    numeric_mask = df_result.index != "Mã cổ phiếu"
    df_result.loc[numeric_mask] = df_result.loc[numeric_mask].applymap(
        lambda x: f"{x:.3f}" if pd.notnull(x) else x
    )

    return df_result

def export_financial_reports(df_balance_sheet, df_income_statement, df_cash_flow):
    r"""
    Xử lý dữ liệu từ các DataFrame báo cáo tài chính và xuất ra 3 file Excel:
      - {Mã cổ phiếu}_bs_{ngày tháng xuất báo cáo}.xlsx
      - {Mã cổ phiếu}_is_{ngày tháng xuất báo cáo}.xlsx
      - {Mã cổ phiếu}_cf_{ngày tháng xuất báo cáo}.xlsx
    Các báo cáo bao gồm:
      - Bảng cân đối kế toán (balance sheet)
      - Báo cáo kết quả hoạt động kinh doanh (income statement)
      - Báo cáo lưu chuyển tiền tệ (cash flow)
      
    Tại đường dẫn:
      \Data\Data_store
    """
    df_bs_final = balance_sheet_final(df_balance_sheet)
    df_is_final = income_statement_final(df_income_statement)
    df_cf_final = cash_flow_final(df_cash_flow)

    stock_code = df_bs_final.loc["Mã cổ phiếu", "2020"]

    report_date = datetime.now().strftime("%d%m%Y")
    file_path = "\\Data\\Data_store"

    file_bs = f"{file_path}\\{stock_code}_bs_{report_date}.xlsx"
    file_is = f"{file_path}\\{stock_code}_is_{report_date}.xlsx"
    file_cf = f"{file_path}\\{stock_code}_cf_{report_date}.xlsx"

    df_bs_final.to_excel(file_bs, index=True)
    df_is_final.to_excel(file_is, index=True)
    df_cf_final.to_excel(file_cf, index=True)

    print("Xuất file báo cáo tài chính thành công!")

def financial_ratios_final(stock_code, period='year', lang='vi', dropna=True):
    r"""
    Sử dụng hàm get_financial_ratios_vci để lấy thông tin tỷ số tài chính của công ty,
    reframe kết quả theo định dạng:
    
    +---------------------------------------------------------------------------------------------------------------+
    | Chỉ số           | (Vay NH+DH)/VCSH | Nợ/VCSH | TSCĐ / Vốn CSH | Vốn CSH/Vốn điều lệ | Số ngày thu tiền bình quân | Số ngày tồn kho bình quân | Số ngày thanh toán bình quân | Biên lợi nhuận gộp (%) | Biên lợi nhuận ròng (%) | ROE (%) | ROA (%) | Chỉ số thanh toán hiện thời | Chỉ số thanh toán nhanh | Khả năng chi trả lãi vay | Đòn bẩy tài chính | P/E  | P/B  | EPS (VND) | BVPS (VND) |
    +---------------------------------------------------------------------------------------------------------------+
    | 2020             | 2,414           | 2,305   | 0.715          | 0.956             | ...                       | ...                      | ...                         | ...                   | ...                   | ...     | ...     | ...                       | ...                   | ...                  | ...             | ...  | ...  | ...       | ...       |
    | 2021             | 1,750           | 1,985   | 0.843          | 2.385             | ...                       | ...                      | ...                         | ...                   | ...                   | ...     | ...     | ...                       | ...                   | ...                  | ...             | ...  | ...  | ...       | ...       |
    | 2022             | 1,259           | 1,489   | 0.806          | 2.449             | ...                       | ...                      | ...                         | ...                   | ...                   | ...     | ...     | ...                       | ...                   | ...                  | ...             | ...  | ...  | ...       | ...       |
    | 2023             | 1,419           | 1,595   | 0.886          | 2.470             | ...                       | ...                      | ...                         | ...                   | ...                   | ...     | ...     | ...                       | ...                   | ...                  | ...             | ...  | ...  | ...       | ...       |
    | 2024             | 1,069           | 1,312   | 0.596          | 2.706             | ...                       | ...                      | ...                         | ...                   | ...                   | ...     | ...     | ...                       | ...                   | ...                  | ...             | ...  | ...  | ...       | ...       |
    | Phân loại      | Chỉ tiêu cơ cấu nguồn vốn | Chỉ tiêu cơ cấu nguồn vốn | Chỉ tiêu cơ cấu nguồn vốn | Chỉ tiêu cơ cấu nguồn vốn | Chỉ tiêu hiệu quả hoạt động | Chỉ tiêu hiệu quả hoạt động | Chỉ tiêu hiệu quả hoạt động | Chỉ tiêu khả năng sinh lợi | Chỉ tiêu khả năng sinh lợi | Chỉ tiêu khả năng sinh lợi | Chỉ tiêu khả năng sinh lợi | Chỉ tiêu thanh khoản | Chỉ tiêu thanh khoản | Chỉ tiêu thanh khoản | Chỉ tiêu thanh khoản | Chỉ tiêu định giá | Chỉ tiêu định giá | Chỉ tiêu định giá | Chỉ tiêu định giá |
    +---------------------------------------------------------------------------------------------------------------+
    """
    ratios = get_financial_ratios_vci(stock_code, period, lang, dropna)
    
    if isinstance(ratios.columns, pd.MultiIndex):
        ratio_names = ratios.columns.get_level_values(1).tolist()
        classifications = ratios.columns.get_level_values(0).tolist()
        ratios.columns = ratio_names
    else:
        classification_mapping = {
            "(Vay NH+DH)/VCSH": "Chỉ tiêu cơ cấu nguồn vốn",
            "Nợ/VCSH": "Chỉ tiêu cơ cấu nguồn vốn",
            "TSCĐ / Vốn CSH": "Chỉ tiêu cơ cấu nguồn vốn",
            "Vốn CSH/Vốn điều lệ": "Chỉ tiêu cơ cấu nguồn vốn",
            "Số ngày thu tiền bình quân": "Chỉ tiêu hiệu quả hoạt động",
            "Số ngày tồn kho bình quân": "Chỉ tiêu hiệu quả hoạt động",
            "Số ngày thanh toán bình quân": "Chỉ tiêu hiệu quả hoạt động",
            "Biên lợi nhuận gộp (%)": "Chỉ tiêu khả năng sinh lợi",
            "Biên lợi nhuận ròng (%)": "Chỉ tiêu khả năng sinh lợi",
            "ROE (%)": "Chỉ tiêu khả năng sinh lợi",
            "ROA (%)": "Chỉ tiêu khả năng sinh lợi",
            "Chỉ số thanh toán hiện thời": "Chỉ tiêu thanh khoản",
            "Chỉ số thanh toán nhanh": "Chỉ tiêu thanh khoản",
            "Khả năng chi trả lãi vay": "Chỉ tiêu thanh khoản",
            "Đòn bẩy tài chính": "Chỉ tiêu thanh khoản",
            "P/E": "Chỉ tiêu định giá",
            "P/B": "Chỉ tiêu định giá",
            "EPS (VND)": "Chỉ tiêu định giá",
            "BVPS (VND)": "Chỉ tiêu định giá"
        }
        ratio_names = ratios.columns.tolist()
        classifications = [classification_mapping.get(name, "") for name in ratio_names]

    desired_columns = [
        "(Vay NH+DH)/VCSH", "Nợ/VCSH", "TSCĐ / Vốn CSH", "Vốn CSH/Vốn điều lệ",
        "Số ngày thu tiền bình quân", "Số ngày tồn kho bình quân", "Số ngày thanh toán bình quân",
        "Biên lợi nhuận gộp (%)", "Biên lợi nhuận ròng (%)", "ROE (%)", "ROA (%)",
        "Chỉ số thanh toán hiện thời", "Chỉ số thanh toán nhanh",
        "Khả năng chi trả lãi vay", "Đòn bẩy tài chính",
        "P/E", "P/B", "EPS (VND)", "BVPS (VND)"
    ]
    existing_columns = [col for col in desired_columns if col in ratios.columns]
    ratios = ratios[existing_columns]

    if ratios.shape[0] == 5:
        new_index = ['2020', '2021', '2022', '2023', '2024']
        ratios = ratios.iloc[::-1]
        ratios.index = new_index

    classification_series = pd.Series(classifications, index=ratio_names)
    classification_row = classification_series[existing_columns].to_frame().T
    classification_row.index = ["Phân loại"]

    final_df = pd.concat([ratios, classification_row])
    final_df.index.name = "Chỉ số"

    def format_value(x):
        try:
            num = float(x)
            if num >= 1000:
                return f"{num:,.0f}"
            else:
                return f"{num:.3f}"
        except Exception:
            return x

    formatted_df = final_df.copy()
    for idx in formatted_df.index:
        if idx != "Phân loại":
            formatted_df.loc[idx] = formatted_df.loc[idx].apply(format_value)

    print("Các tỷ số tài chính của công ty", stock_code, ":")
    print(formatted_df.to_string())
    return formatted_df

def export_financial_ratios(stock_code, period='year', lang='vi', dropna=True):
    r"""
    Lấy thông tin tỷ số tài chính thông qua hàm financial_ratios_final và xuất kết quả ra file Excel với tên:
      {Mã cổ phiếu}_financialratios_{ngày tháng xuất báo cáo}.xlsx
    Tại đường dẫn:
      \Data\Data_store
    """
    df_ratios = financial_ratios_final(stock_code, period, lang, dropna)
    report_date = datetime.now().strftime("%d%m%Y")
    file_path = "\\Data\\Data_store"
    file_ratios = f"{file_path}\\{stock_code}_financialratios_{report_date}.xlsx"
    df_ratios.to_excel(file_ratios, index=True)
    print("Xuất file tỷ số tài chính thành công!")

