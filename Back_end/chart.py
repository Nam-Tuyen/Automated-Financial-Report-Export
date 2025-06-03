import sys
import os
import re
import glob
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
from datetime import datetime
from fpdf import FPDF

# Các module được import từ project của bạn:
from financial_statement import financial_ratios_final
from data_processor import (
    get_stock_and_exchange_history_vci, 
    industry_classification, 
    get_stock_volume_vci,
    get_top_shareholders_vci,
    balance_sheet, income_statement, cash_flow,
    get_financial_ratios_vci
)
from indicator import (
    get_close_data_from_csv,
    SMA_50_20,
    bollinger_band,
    RSI,
    MACD
)
from financial_statement import financial_ratios_final

# Đường dẫn chứa file lưu ảnh
FILEPATH = r"\Data\Data_store"

# ------------------ Các hàm vẽ biểu đồ hiện có ------------------
# (Các hàm dưới đây như draw_normalized_linegraph, draw_volume_comparison, plot_top_shareholders,
#  plot_indicator_charts, get_df_chart_financial_ratios, process_df_chart, draw_chart, ... đã được định nghĩa trước đó.)
# Ví dụ: 
def draw_normalized_linegraph(stock_code):
    # (Code vẽ normalized line graph như đã định nghĩa trước đó)
    # Ở cuối hàm: thay plt.show() bằng plt.show() (sẽ bị ghi đè trong hàm export)
    # ...
    df_stock, df_index = get_stock_and_exchange_history_vci(stock_code)
    if "time" not in df_stock.columns:
        df_stock = df_stock.reset_index().rename(columns={'index': 'time'})
    if not df_index.empty and "time" not in df_index.columns:
        df_index = df_index.reset_index().rename(columns={'index': 'time'})
    df_stock['time'] = pd.to_datetime(df_stock['time'])
    if not df_index.empty:
        df_index['time'] = pd.to_datetime(df_index['time'])
    start_date = pd.to_datetime("2024-01-01")
    end_date = pd.to_datetime("2025-04-01")
    df_stock = df_stock[(df_stock['time'] >= start_date) & (df_stock['time'] <= end_date)]
    if not df_index.empty:
        df_index = df_index[(df_index['time'] >= start_date) & (df_index['time'] <= end_date)]
    df_stock['close'] = df_stock['close'].interpolate(method='linear', limit_direction='both')
    if not df_index.empty:
        df_index['close'] = df_index['close'].interpolate(method='linear', limit_direction='both')
    norm_stock = df_stock['close'] / df_stock['close'].iloc[0]
    if not df_index.empty:
        norm_exchange = df_index['close'] / df_index['close'].iloc[0]
    df_class = industry_classification(stock_code)
    if not df_class.empty:
        exchange_name = df_class.iloc[0]["Sàn"].strip().upper()
    else:
        exchange_name = "Exchange"
    plt.figure(figsize=(12, 6))
    plt.plot(df_stock['time'], norm_stock, label=stock_code, color='blue')
    if not df_index.empty:
        plt.plot(df_index['time'], norm_exchange, label=exchange_name, color='red')
    plt.xlabel("Thời gian", fontsize=16, fontweight='bold')
    plt.ylabel("Mức độ tăng giảm", fontsize=16, fontweight='bold')
    plt.title(f"Diễn biến giá của cổ phiếu {stock_code} so với sàn {exchange_name}", fontsize=16, fontweight='bold')
    plt.legend()
    plt.grid(True)
    plt.gca().set_axisbelow(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def draw_volume_comparison(stock_code, ref_date_str="2025-04-01"):
    # (Code vẽ biểu đồ cột so sánh volume như đã định nghĩa trước đó)
    df_volume = get_stock_volume_vci(stock_code)
    if df_volume.empty:
        print(f"Không có dữ liệu volume cho mã cổ phiếu: {stock_code}")
        return
    df_volume['time'] = pd.to_datetime(df_volume['time'])
    ref_date = pd.to_datetime(ref_date_str)
    df_filtered = df_volume[df_volume['time'] <= ref_date]
    vol_day_series = df_filtered[df_filtered['time'] == ref_date]['volume']
    if vol_day_series.empty:
        available_date = df_filtered['time'].max()
        print(f"Không tìm thấy dữ liệu cho ngày {ref_date.strftime('%Y-%m-%d')}. Sử dụng ngày {available_date.strftime('%Y-%m-%d')} thay thế.")
        ref_date = available_date
        vol_day_series = df_filtered[df_filtered['time'] == ref_date]['volume']
        if vol_day_series.empty:
            print(f"Không tìm thấy dữ liệu cho ngày {ref_date.strftime('%Y-%m-%d')}.")
            return
    vol_day = vol_day_series.iloc[0]
    week_start = ref_date - pd.Timedelta(days=6)
    week_avg = df_filtered[(df_filtered['time'] >= week_start) & (df_filtered['time'] <= ref_date)]['volume'].mean()
    month_start = ref_date - pd.DateOffset(months=1)
    month_avg = df_filtered[(df_filtered['time'] >= month_start) & (df_filtered['time'] <= ref_date)]['volume'].mean()
    three_month_start = ref_date - pd.DateOffset(months=3)
    three_month_avg = df_filtered[(df_filtered['time'] >= three_month_start) & (df_filtered['time'] <= ref_date)]['volume'].mean()
    categories = [ref_date.strftime('%Y-%m-%d'), '1 Week Avg', '1 Month Avg', '3 Month Avg']
    volumes = [vol_day, week_avg, month_avg, three_month_avg]
    cmap = plt.get_cmap("Blues")
    colors = [cmap(0.3 + 0.1 * i) for i in range(4)]
    plt.figure(figsize=(8, 6))
    bars = plt.bar(categories, volumes, color=colors)
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height, f'{height:,.0f}', ha='center', va='bottom')
    plt.xlabel("Khoảng thời gian", fontsize=16, fontweight='bold')
    plt.ylabel("Khối lượng giao dịch", fontsize=16, fontweight='bold')
    plt.title(f"So sánh khối lượng giao dịch của {stock_code} với các mốc thời gian", fontsize=16, fontweight='bold')
    plt.grid(True)
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.show()

def plot_top_shareholders(stock_code, top_n=5):
    # (Code vẽ biểu đồ top cổ đông như đã định nghĩa trước đó)
    df_shareholders = get_top_shareholders_vci(stock_code, top_n=top_n)
    if df_shareholders.empty:
        print(f"Không có thông tin cổ đông cho mã {stock_code}.")
        return
    df_sorted = df_shareholders.sort_values(by='share_own_percent', ascending=False)
    shareholders = df_sorted['share_holder']
    share_percent = df_sorted['share_own_percent']
    cmap = plt.get_cmap("Blues")
    colors = [cmap(0.3 + (0.4 * i/(top_n-1))) for i in range(top_n)] if top_n > 1 else [cmap(0.5)]
    wrapped_labels = ["\n".join(textwrap.wrap(label, width=10)) for label in shareholders]
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(wrapped_labels)), share_percent, color=colors)
    plt.xlabel("Cổ đông", fontsize=16, fontweight='bold')
    plt.ylabel("Phần trăm sở hữu", fontsize=16, fontweight='bold')
    plt.title(f"Top {top_n} cổ đông của {stock_code}", fontsize=16, fontweight='bold')
    plt.xticks(range(len(wrapped_labels)), wrapped_labels, rotation=0, ha='center')
    for i, v in enumerate(share_percent):
        plt.text(i, v + 0.001, f"{v:.2%}", ha='center', va='bottom')
    plt.grid(True)
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.show()

def plot_indicator_charts(stock_code):
    # (Code vẽ 4 biểu đồ kỹ thuật: SMA, RSI, Bollinger Bands, MACD)
    df_data = get_close_data_from_csv(stock_code)
    if df_data.empty:
        print(f"Không có dữ liệu giá cho mã {stock_code} từ CSV.")
        return
    if "Date" in df_data.columns:
        df_data['time'] = pd.to_datetime(df_data['Date'], format='%d/%m/%Y')
    else:
        if "time" not in df_data.columns:
            df_data = df_data.reset_index().rename(columns={'index': 'time'})
        df_data['time'] = pd.to_datetime(df_data['time'])
    start_date = pd.to_datetime("2024-01-01")
    end_date = pd.to_datetime("2025-04-01")
    df_data = df_data[(df_data['time'] >= start_date) & (df_data['time'] <= end_date)]
    
    # Biểu đồ SMA
    df_sma = SMA_50_20(df_data.copy())
    plt.figure(figsize=(12, 6))
    plt.plot(df_data['time'], df_data['Close'], label='Close', color='blue')
    plt.plot(df_sma['time'], df_sma['SMA_20'], label='SMA 20', color='orange')
    plt.plot(df_sma['time'], df_sma['SMA_50'], label='SMA 50', color='purple')
    plt.xlabel("Thời gian", fontsize=16, fontweight='bold')
    plt.ylabel("Giá", fontsize=16, fontweight='bold')
    plt.title("Giá đóng cửa với SMA20 và SMA50", fontsize=16, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.show()
    
    # Biểu đồ RSI
    df_rsi = RSI(df_data.copy())
    plt.figure(figsize=(12, 6))
    plt.plot(df_rsi['time'], df_rsi['rsi'], label='RSI', color='purple')
    plt.axhline(y=80, color='purple', linestyle='--', alpha=0.5, label='Mức 80')
    plt.axhline(y=20, color='purple', linestyle='--', alpha=0.5, label='Mức 20')
    plt.xlabel("Thời gian", fontsize=16, fontweight='bold')
    plt.ylabel("Thang đo", fontsize=16, fontweight='bold')
    plt.title("Chỉ báo RSI", fontsize=16, fontweight='bold')
    plt.legend()
    plt.grid(True)
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.show()
    
    # Biểu đồ Bollinger Bands
    df_boll = bollinger_band(df_data.copy())
    plt.figure(figsize=(12, 6))
    plt.plot(df_data['time'], df_data['Close'], label='Close', color='red')
    plt.plot(df_boll['time'], df_boll['SMA'], label='SMA (Bollinger)', color='orange')
    plt.plot(df_boll['time'], df_boll['Upper Band'], label='Upper Band', color='blue', linestyle='--')
    plt.plot(df_boll['time'], df_boll['Lower Band'], label='Lower Band', color='blue', linestyle='--')
    plt.xlabel("Thời gian", fontsize=16, fontweight='bold')
    plt.ylabel("Thang đo", fontsize=16, fontweight='bold')
    plt.title("Bollinger Bands", fontsize=16, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.show()
    
    # Biểu đồ MACD
    df_macd = MACD(df_data.copy())
    plt.figure(figsize=(12, 6))
    plt.plot(df_macd['time'], df_macd['MACD'], label='MACD', color='blue')
    plt.plot(df_macd['time'], df_macd['Signal Line'], label='Signal Line', color='red')
    plt.xlabel("Thời gian", fontsize=16, fontweight='bold')
    plt.ylabel("Thang đo", fontsize=16, fontweight='bold')
    plt.title("MACD", fontsize=16, fontweight='bold')
    plt.legend()
    plt.grid(True)
    plt.gca().set_axisbelow(True)
    plt.tight_layout()
    plt.show()

def get_df_chart_financial_ratios(stock_code):
    """
    Lấy dữ liệu chỉ số tài chính của một cổ phiếu, xử lý với financial_ratios_final và lọc ra các chỉ số mong muốn.
    Trả về DataFrame có các cột là các chỉ số được chọn và index là các năm 2020 đến 2024.
    """
    df_final = financial_ratios_final(stock_code, period='year', lang='vi', dropna=True)
    df_chart = df_final.drop("Phân loại", errors="ignore").copy()
    desired_metrics = [
        "(Vay NH+DH)/VCSH", "Nợ/VCSH", "TSCĐ / Vốn CSH", "Vốn CSH/Vốn điều lệ", 
        "Số ngày thu tiền bình quân", "Số ngày tồn kho bình quân", "Số ngày thanh toán bình quân",
        "Biên lợi nhuận gộp (%)", "Biên lợi nhuận ròng (%)", "ROE (%)", "ROA (%)",
        "Chỉ số thanh toán nhanh", "Đòn bẩy tài chính", "Chỉ số thanh toán hiện thời", "Khả năng chi trả lãi vay",
        "P/E", "P/B", "EPS (VND)", "BVPS (VND)"
    ]
    existing_metrics = [metric for metric in desired_metrics if metric in df_chart.columns]
    df_chart = df_chart[existing_metrics].copy()
    return df_chart

def process_df_chart(df_chart):
    """
    Xử lý DataFrame từ financial_ratios_final:
      - Loại bỏ hàng "Phân loại" (nếu có).
      - Chuyển giá trị chuỗi sang float.
      - Với các cột "EPS (VND)" và "BVPS (VND)", chia thêm cho 1000 và làm tròn 3 số sau dấu thập phân.
    """
    if "Phân loại" in df_chart.index:
        df_chart = df_chart.drop("Phân loại")
    for col in df_chart.columns:
        df_chart[col] = df_chart[col].apply(lambda x: float(str(x).replace(',', '')) if pd.notnull(x) else x)
    for col in ["EPS (VND)", "BVPS (VND)"]:
        if col in df_chart.columns:
            df_chart[col] = (df_chart[col] / 1000).round(3)
    return df_chart

def plot_line_chart_group(df, metrics, title, y_lim=None, y_label=""):
    years = ["2020", "2021", "2022", "2023", "2024"]
    plt.figure(figsize=(12, 8))
    group_values = []
    for metric in metrics:
        try:
            values = [float(str(x).replace(',', '')) for x in df.loc[years, metric]]
        except Exception:
            values = df.loc[years, metric].tolist()
        group_values.extend(values)
        plt.plot(years, values, marker='o', label=metric, zorder=3, linewidth=2)
    if y_lim is None:
        min_val = min(group_values)
        max_val = max(group_values)
        margin = 0.1 * (max_val - min_val) if max_val != min_val else 1
        y_lim = (min_val - margin, max_val + margin)
    plt.ylim(y_lim)
    plt.xlabel("Năm", fontsize=16, fontweight='bold')
    plt.ylabel(y_label, fontsize=16, fontweight='bold')
    plt.title(title, fontsize=16, fontweight='bold')
    plt.legend(loc='upper right', fontsize='small')
    plt.grid(True, linestyle='--', zorder=0)
    plt.show()

def plot_bar_chart_group(df, metrics, title, y_lim=None, y_label=""):
    years = ["2020", "2021", "2022", "2023", "2024"]
    plt.figure(figsize=(12, 8))
    metric = metrics[0]
    try:
        values = [float(str(x).replace(',', '')) for x in df.loc[years, metric]]
    except Exception:
        values = df.loc[years, metric].tolist()
    if y_lim is None:
        min_val = min(values)
        max_val = max(values)
        margin = 0.1 * (max_val - min_val) if max_val != min_val else 1
        y_lim = (min_val - margin, max_val + margin)
    plt.bar(years, values, zorder=3)
    plt.ylim(y_lim)
    plt.xlabel("Năm", fontsize=16, fontweight='bold')
    plt.ylabel(y_label, fontsize=16, fontweight='bold')
    plt.title(title, fontsize=16, fontweight='bold')
    plt.legend([metric], loc='upper right', fontsize='small')
    plt.grid(True, axis='y', linestyle='--', zorder=0)
    plt.show()

def draw_chart(df_chart_processed):
    # Group 1: Cơ cấu nguồn vốn (Line)
    group1_metrics = ["(Vay NH+DH)/VCSH", "Nợ/VCSH", "TSCĐ / Vốn CSH", "Vốn CSH/Vốn điều lệ"]
    plot_line_chart_group(df_chart_processed, group1_metrics,
                          title="Chỉ tiêu cơ cấu nguồn vốn", y_lim=None, y_label="Mức độ tăng trưởng (lần)")
    # Group 2: Khả năng sinh lời (Line)
    group2_metrics = ["Biên lợi nhuận ròng (%)", "Biên lợi nhuận gộp (%)", "ROE (%)", "ROA (%)"]
    plot_line_chart_group(df_chart_processed, group2_metrics,
                          title="Chỉ tiêu khả năng sinh lời", y_lim=None, y_label="Mức độ tăng trưởng (%)")
    # Group 3: Hiệu quả hoạt động (Line)
    group3_metrics = ["Số ngày thu tiền bình quân", "Số ngày tồn kho bình quân", "Số ngày thanh toán bình quân"]
    plot_line_chart_group(df_chart_processed, group3_metrics,
                          title="Chỉ tiêu hiệu quả hoạt động", y_lim=None, y_label="Mức độ tăng trưởng (lần)")
    # Group 4: Thanh khoản (Line)
    group4_metrics = ["Chỉ số thanh toán nhanh", "Đòn bẩy tài chính", "Chỉ số thanh toán hiện thời", "Khả năng chi trả lãi vay"]
    plot_line_chart_group(df_chart_processed, group4_metrics,
                          title="Chỉ tiêu thanh khoản", y_lim=None, y_label="Mức độ tăng trưởng (lần)")
    # Group 5: Định giá P/E (Bar)
    group5_metrics = ["P/E"]
    plot_bar_chart_group(df_chart_processed, group5_metrics,
                         title="Chỉ tiêu định giá P/E", y_lim=None, y_label="Mức độ tăng trưởng (lần)")
    # Group 6: Định giá P/B (Bar)
    group6_metrics = ["P/B"]
    plot_bar_chart_group(df_chart_processed, group6_metrics,
                         title="Chỉ tiêu định giá P/B", y_lim=None, y_label="Mức độ tăng trưởng (lần)")
    # Group 7: Định giá EPS (Line)
    group7_metrics = ["EPS (VND)"]
    plot_line_chart_group(df_chart_processed, group7_metrics,
                          title="Chỉ tiêu định giá EPS", y_lim=None, y_label="Số tiền lời trên 1 cổ phiếu (VND)")
    # Group 8: Định giá BVPS (Line)
    group8_metrics = ["BVPS (VND)"]
    plot_line_chart_group(df_chart_processed, group8_metrics,
                          title="Chỉ tiêu định giá BVPS", y_lim=None, y_label="Giá trị sổ sách của 1 cổ phiếu (VND)")

# ------------------ Hàm xuất tất cả các biểu đồ ra file PNG ------------------
def save_current_plot(stock_code, func_name):
    date_str = datetime.now().strftime("%d%m%Y")
    filename = f"{stock_code}_{func_name}_{date_str}.png"
    file_path = os.path.join(FILEPATH, filename)
    plt.savefig(file_path)
    plt.close()
    print(f"Saved plot: {file_path}")

def export_all_plots(stock_code):
    # Để tránh plt.show() hiển thị ra màn hình, ta ghi đè plt.show tạm thời.
    old_show = plt.show

    # 1. Normalized Line Graph
    plt.show = lambda: None
    draw_normalized_linegraph(stock_code)
    plt.show = old_show
    save_current_plot(stock_code, "draw_normalized_linegraph")
    
    # 2. Volume Comparison
    plt.show = lambda: None
    draw_volume_comparison(stock_code)
    plt.show = old_show
    save_current_plot(stock_code, "draw_volume_comparison")
    
    # 3. Top Shareholders
    plt.show = lambda: None
    plot_top_shareholders(stock_code)
    plt.show = old_show
    save_current_plot(stock_code, "plot_top_shareholders")
    
    # 4. Indicator Charts (nhiều biểu đồ)
    plt.show = lambda: None
    plot_indicator_charts(stock_code)
    plt.show = old_show
    # Lấy danh sách các figure hiện có
    fig_nums = plt.get_fignums()
    for i, fig_num in enumerate(fig_nums):
        plt.figure(fig_num)
        save_current_plot(stock_code, f"plot_indicator_charts_{i+1}")
    
    # 5. Financial Ratios Charts
    df_chart = get_df_chart_financial_ratios(stock_code)
    df_chart_processed = process_df_chart(df_chart)
    plt.show = lambda: None
    draw_chart(df_chart_processed)
    plt.show = old_show
    fig_nums = plt.get_fignums()
    for i, fig_num in enumerate(fig_nums):
        plt.figure(fig_num)
        save_current_plot(stock_code, f"draw_chart_{i+1}")

