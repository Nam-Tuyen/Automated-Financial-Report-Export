import streamlit as st
import os
import pandas as pd
from datetime import datetime

# Import các hàm từ các module trong project
from data_processor import balance_sheet, income_statement, cash_flow
from financial_statement import export_financial_reports, export_financial_ratios
from indicator import get_close_data_from_csv, SMA_50_20, bollinger_band, RSI, MACD
from fundamental_analyst import get_eps_bvps_2024, valuation_index, calculate_stock_price
from chart import export_all_plots
from report_generator import generate_stock_report

def main():
    st.set_page_config(page_title="Báo cáo tài chính & Phân tích cổ phiếu",
                       layout="wide", initial_sidebar_state="expanded")
    
    # Header đẹp
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2C3E50;
            text-align: center;
            margin-bottom: 2rem;
        }
        .step-header {
            font-size: 1.2rem;
            font-weight: bold;
            color: #34495E;
            margin-top: 1rem;
        }
        </style>
        """, unsafe_allow_html=True
    )
    st.markdown("<div class='main-title'>Hệ thống xuất báo cáo phân tích tài chính tự động</div>", unsafe_allow_html=True)
    
    # --- Sidebar: Thanh tìm kiếm & gợi ý cổ phiếu ---
    st.sidebar.markdown("### Nhập mã hoặc tên công ty để tìm kiếm")
    # Đường dẫn tới file gợi ý (định dạng Excel)
    suggestion_file_path = r"Data\Data cleaned\Phan_loai_nganh(cleaned).xlsx"
    try:
        df_suggestion = pd.read_excel(suggestion_file_path, engine='openpyxl')
    except Exception as e:
        st.sidebar.error("Lỗi đọc file gợi ý: " + str(e))
        df_suggestion = None

    # Thanh tìm kiếm duy nhất
    search_input = st.sidebar.text_input("Nhập mã hoặc tên công ty:", value="")

    # Nếu có file gợi ý và người dùng đã nhập ký tự
    if df_suggestion is not None and search_input != "":
        # Lọc các dòng theo cột "Mã" hoặc "Tên công ty" bắt đầu bằng ký tự người dùng nhập (không phân biệt hoa thường)
        mask = df_suggestion["Mã"].astype(str).str.lower().str.startswith(search_input.lower()) | \
               df_suggestion["Tên công ty"].astype(str).str.lower().str.startswith(search_input.lower())
        df_filtered = df_suggestion[mask]
        if not df_filtered.empty:
            # Tạo danh sách gợi ý theo định dạng "{Mã} - {Tên công ty}"
            suggestion_list = df_filtered.apply(lambda row: f"{row['Mã']} - {row['Tên công ty']}", axis=1).tolist()
            # Hiển thị dropdown gợi ý để người dùng lựa chọn
            selected_suggestion = st.sidebar.selectbox("Chọn cổ phiếu từ gợi ý:", options=suggestion_list)
            stock_code = str(selected_suggestion.split(" - ")[0])
        else:
            # Nếu không có gợi ý phù hợp, dùng luôn giá trị nhập vào
            stock_code = search_input
    else:
        # Nếu không nhập gì thì sử dụng giá trị mặc định
        stock_code = "GEX"
    
    st.sidebar.markdown("---")
    progress_bar = st.progress(0)
    progress = 0  # Giá trị progress ban đầu

    if st.sidebar.button("Chạy báo cáo"):
        # Bước 1: Xử lý dữ liệu từ file Excel (Data Processor)
        st.markdown("<div class='step-header'>Bước 1: Xử lý dữ liệu từ file Excel (Data Processor)</div>", unsafe_allow_html=True)
        try:
            bs_df = balance_sheet(stock_code)
            is_df = income_statement(stock_code)
            cf_df = cash_flow(stock_code)
            st.info("Dữ liệu cân đối kế toán, kết quả kinh doanh và lưu chuyển tiền tệ đã được xử lý.")
            progress += 16
            progress_bar.progress(progress)
        except Exception as e:
            st.error("Lỗi Data Processor: " + str(e))
            return

        # Bước 2: Xử lý báo cáo tài chính (Financial Statement)
        st.markdown("<div class='step-header'>Bước 2: Xử lý báo cáo tài chính (Financial Statement)</div>", unsafe_allow_html=True)
        try:
            export_financial_reports(bs_df, is_df, cf_df)
            export_financial_ratios(stock_code, period='year', lang='vi', dropna=True)
            st.info("Báo cáo tài chính và tỷ số tài chính đã được xuất ra file Excel.")
            progress += 16
            progress_bar.progress(progress)
        except Exception as e:
            st.error("Lỗi Financial Statement: " + str(e))
            return
        
        # Bước 3: Tính toán các chỉ báo kỹ thuật (Indicators)
        st.markdown("<div class='step-header'>Bước 3: Tính toán các chỉ báo kỹ thuật (Indicators)</div>", unsafe_allow_html=True)
        try:
            df_close = get_close_data_from_csv(stock_code)
            if df_close.empty:
                st.warning("Không có dữ liệu giá đóng cửa từ CSV.")
            else:
                df_sma = SMA_50_20(df_close.copy())
                df_boll = bollinger_band(df_close.copy())
                df_rsi = RSI(df_close.copy())
                df_macd = MACD(df_close.copy())
                st.info("Các chỉ báo kỹ thuật đã được tính toán.")
            progress += 16
            progress_bar.progress(progress)
        except Exception as e:
            st.error("Lỗi Indicators: " + str(e))
            return
        
        # Bước 4: Vẽ và xuất biểu đồ (Charts)
        st.markdown("<div class='step-header'>Bước 4: Vẽ và xuất biểu đồ (Charts)</div>", unsafe_allow_html=True)
        try:
            export_all_plots(stock_code)
            st.info("Các biểu đồ đã được tạo và lưu thành công.")
            progress += 16
            progress_bar.progress(progress)
        except Exception as e:
            st.error("Lỗi Charts: " + str(e))
            return
        
        # Bước 5: Phân tích định giá (Fundamental Analysis)
        st.markdown("<div class='step-header'>Bước 5: Phân tích định giá (Fundamental Analysis)</div>", unsafe_allow_html=True)
        try:
            eps, bvps = get_eps_bvps_2024(stock_code)
            industry_pe, industry_pb = valuation_index(stock_code)
            if eps is None or bvps is None or industry_pe is None or industry_pb is None:
                st.warning("Không đủ dữ liệu để tính giá cổ phiếu định giá.")
            else:
                stock_price = calculate_stock_price(eps, bvps, industry_pe, industry_pb)
                st.write(f"<div class='step-header'>Giá cổ phiếu định giá (trung bình P/E và P/B): {stock_price:.3f} VND</div>", unsafe_allow_html=True)
                st.info("Phân tích định giá thành công.")
            progress += 16
            progress_bar.progress(progress)
        except Exception as e:
            st.error("Lỗi Fundamental Analysis: " + str(e))
            return
        
        # Bước 6: Tạo báo cáo tổng hợp (Report Generator)
        st.markdown("<div class='step-header'>Bước 6: Tạo báo cáo tổng hợp (Report Generator)</div>", unsafe_allow_html=True)
        try:
            generate_stock_report(stock_code)
            st.info("Báo cáo PDF đã được tạo và lưu thành công!")
            progress = 100
            progress_bar.progress(progress)
        except Exception as e:
            st.error("Lỗi Report Generator: " + str(e))
            return
        
        st.success("Quá trình hoàn tất!")

if __name__ == '__main__':
    main()
