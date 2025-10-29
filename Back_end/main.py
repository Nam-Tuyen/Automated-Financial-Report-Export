import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
from paths import SUGGESTION_XLSX, REPORT_EXPORT_DIR, ensure_output_dirs

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

# Import các hàm từ các module trong project
from data_processor import balance_sheet, income_statement, cash_flow
from financial_statement import export_financial_reports, export_financial_ratios
from indicator import get_close_data_from_csv, SMA_50_20, bollinger_band, RSI, MACD
from fundamental_analyst import get_eps_bvps_2024, valuation_index, calculate_stock_price
from chart import export_all_plots
from report_generator import generate_stock_report


def inject_custom_css():
    """Inject custom CSS for modern, harmonious design."""
    st.markdown(
        """
        <style>
        /* Import Google Fonts and Icons */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css');
        
        /* Smooth color scheme - Modern and harmonious */
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --bg-dark: #0f172a;
            --bg-card: rgba(30, 41, 59, 0.8);
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --border-color: rgba(148, 163, 184, 0.2);
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1);
            --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.2);
            --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.3);
            --shadow-xl: 0 16px 64px rgba(0, 0, 0, 0.4);
        }
        
        /* Main app styling */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            background-attachment: fixed;
            color: var(--text-primary);
        }
        
        html, body, [class*="css"] {
            font-family: 'Inter', 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            background: transparent !important;
            color: var(--text-primary) !important;
        }
        
        /* Main container */
        .main .block-container {
            padding-top: 3rem;
            padding-bottom: 3rem;
            max-width: 1000px;
            background: transparent;
        }
        
        /* Header container - Modern card design */
        .header-container {
            text-align: center;
            padding: 4rem 3rem;
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            margin-bottom: 3rem;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-xl);
            position: relative;
            overflow: hidden;
        }
        
        .header-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--primary-gradient);
        }
        
        .app-title {
            font-family: 'Poppins', sans-serif;
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -1px;
            line-height: 1.2;
        }
        
        .app-subtitle {
            font-size: 1.15rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
            font-weight: 400;
            letter-spacing: 0.3px;
        }
        
        /* Search input container - Modern glassmorphism card */
        div[data-testid="stElementContainer"]:has(input[placeholder*="mã cổ phiếu"]),
        div[data-testid="stElementContainer"][data-stale="false"]:has(input) {
            background: var(--bg-card) !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 24px !important;
            padding: 2.5rem !important;
            margin: 2.5rem 0 !important;
            box-shadow: var(--shadow-lg) !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative;
            overflow: hidden;
        }
        
        div[data-testid="stElementContainer"]:has(input[placeholder*="mã cổ phiếu"])::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--primary-gradient);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        div[data-testid="stElementContainer"]:has(input[placeholder*="mã cổ phiếu"]):hover::before {
            opacity: 1;
        }
        
        div[data-testid="stElementContainer"]:has(input[placeholder*="mã cổ phiếu"]):hover {
            box-shadow: var(--shadow-xl) !important;
            border-color: rgba(102, 126, 234, 0.5) !important;
            transform: translateY(-2px);
        }
        
        /* Hide text input label */
        .stTextInput label,
        label[data-testid="stWidgetLabel"] {
            display: none !important;
        }
        
        /* Modern input field styling - Ultra Premium */
        .stTextInput input[type="text"],
        input[type="text"][placeholder*="mã cổ phiếu"],
        input[type="text"][id^="text_input"],
        input.st-ae.st-bd.st-be.st-bf,
        input[class*="st-"] {
            background: transparent !important;
            color: var(--text-primary) !important;
            border: none !important;
            border-radius: 18px !important;
            padding: 1.5rem 2rem !important;
            font-size: 1.2rem !important;
            font-weight: 400 !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }
        
        .stTextInput input[type="text"]:focus,
        input[type="text"][placeholder*="mã cổ phiếu"]:focus,
        input.st-ae.st-bd.st-be.st-bf:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2), 0 8px 24px rgba(102, 126, 234, 0.3) !important;
            outline: none !important;
            background: rgba(15, 23, 42, 0.9) !important;
            transform: translateY(-1px) scale(1.01);
        }
        
        .stTextInput input[type="text"]::placeholder,
        input[type="text"][placeholder*="mã cổ phiếu"]::placeholder {
            color: var(--text-muted) !important;
            font-weight: 400 !important;
            opacity: 0.7 !important;
        }
        
        /* Input container wrapper */
        div[data-baseweb="input"],
        div[data-baseweb="base-input"] {
            background: transparent !important;
        }
        
        /* Search icon area enhancement */
        div[data-testid="stElementContainer"]:has(input[placeholder*="mã cổ phiếu"])::after {
            content: '🔍';
            position: absolute;
            right: 3rem;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1.5rem;
            opacity: 0.5;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }
        
        div[data-testid="stElementContainer"]:has(input[placeholder*="mã cổ phiếu"]:focus)::after {
            opacity: 0.8;
        }
        
        /* Autocomplete suggestions - Modern glassmorphism */
        .suggestions-box {
            margin-top: 1.5rem;
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            max-height: 320px;
            overflow-y: auto;
            box-shadow: var(--shadow-md);
        }
        
        .suggestion-item {
            padding: 0.875rem 1.5rem;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            border-bottom: 1px solid var(--border-color);
        }
        
        .suggestion-item:hover {
            background: rgba(102, 126, 234, 0.1);
            padding-left: 2rem;
        }
        
        .suggestion-item:last-child {
            border-bottom: none;
        }
        
        .suggestion-code {
            font-weight: 600;
            color: #667eea;
            font-family: 'Poppins', sans-serif;
        }
        
        .suggestion-name {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        /* Style suggestion buttons */
        .suggestions-box button {
            background: rgba(30, 41, 59, 0.5) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
            padding: 0.875rem 1.25rem !important;
            margin: 0.375rem 0 !important;
            text-align: left !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            font-weight: 400 !important;
        }
        
        .suggestions-box button:hover {
            background: rgba(102, 126, 234, 0.15) !important;
            border-color: #667eea !important;
            transform: translateX(8px) !important;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2) !important;
        }
        
        /* Button styling - Premium gradient */
        .stButton > button {
            width: 100%;
            background: var(--primary-gradient) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 16px !important;
            padding: 1.4rem 2.5rem !important;
            font-size: 1.15rem !important;
            font-weight: 600 !important;
            font-family: 'Poppins', sans-serif !important;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            margin-top: 2rem;
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
            letter-spacing: 0.5px;
        }
        
        .stButton > button:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 12px 40px rgba(102, 126, 234, 0.5);
        }
        
        .stButton > button:active {
            transform: translateY(-1px) scale(1);
        }
        
        /* Progress bar - Smooth gradient */
        .stProgress > div > div > div > div {
            background: var(--primary-gradient) !important;
            border-radius: 4px !important;
        }
        
        /* Expander styling - Modern cards */
        .streamlit-expanderHeader {
            background: var(--bg-card) !important;
            color: var(--text-primary) !important;
            border-radius: 16px !important;
            border: 1px solid var(--border-color) !important;
            padding: 1rem 1.5rem !important;
            margin-bottom: 0.5rem !important;
            transition: all 0.2s ease !important;
        }
        
        .streamlit-expanderHeader:hover {
            background: rgba(30, 41, 59, 0.95) !important;
            border-color: rgba(102, 126, 234, 0.4) !important;
        }
        
        .streamlit-expanderContent {
            background: rgba(30, 41, 59, 0.6) !important;
            border-radius: 0 0 16px 16px !important;
            padding: 1.5rem !important;
            border: 1px solid var(--border-color) !important;
            border-top: none !important;
        }
        
        /* Success/Error messages - Modern alerts */
        .stSuccess {
            background: rgba(34, 197, 94, 0.15) !important;
            border-left: 4px solid #22c55e !important;
            color: var(--text-primary) !important;
            border-radius: 12px !important;
            padding: 1rem 1.5rem !important;
        }
        
        .stError {
            background: rgba(239, 68, 68, 0.15) !important;
            border-left: 4px solid #ef4444 !important;
            color: var(--text-primary) !important;
            border-radius: 12px !important;
            padding: 1rem 1.5rem !important;
        }
        
        .stWarning {
            background: rgba(251, 191, 36, 0.15) !important;
            border-left: 4px solid #fbbf24 !important;
            color: var(--text-primary) !important;
            border-radius: 12px !important;
            padding: 1rem 1.5rem !important;
        }
        
        /* Step indicator - Modern badge */
        .step-indicator {
            display: flex;
            align-items: center;
            gap: 1.25rem;
            padding: 1.25rem 1.5rem;
            margin: 0.75rem 0;
            background: var(--bg-card);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            border: 1px solid var(--border-color);
            transition: all 0.2s ease;
        }
        
        .step-indicator:hover {
            border-color: rgba(102, 126, 234, 0.4);
            box-shadow: var(--shadow-md);
        }
        
        .step-number {
            background: var(--primary-gradient);
            color: white;
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.1rem;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .step-text {
            flex: 1;
            color: var(--text-primary);
            font-weight: 500;
            font-size: 1rem;
        }
        
        /* Download section - Premium card */
        .download-container {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 2.5rem;
            margin: 2.5rem 0;
            text-align: center;
            box-shadow: var(--shadow-xl);
        }
        
        .stDownloadButton > button {
            background: var(--accent-gradient) !important;
            color: white !important;
            border-radius: 14px !important;
            padding: 0.875rem 2rem !important;
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            font-family: 'Poppins', sans-serif !important;
            box-shadow: 0 6px 24px rgba(79, 172, 254, 0.4) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        
        .stDownloadButton > button:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 10px 36px rgba(79, 172, 254, 0.5) !important;
        }
        
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* Custom scrollbar - Modern style */
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.5);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 10px;
            border: 2px solid rgba(15, 23, 42, 0.5);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #764ba2, #667eea);
        }
        
        /* Metrics styling */
        [data-testid="stMetricValue"] {
            color: #667eea !important;
            font-family: 'Poppins', sans-serif !important;
            font-weight: 600 !important;
        }
        
        /* Additional modern touches */
        h1, h2, h3 {
            font-family: 'Poppins', sans-serif !important;
        }
        
        /* Smooth animations */
        * {
            transition: background-color 0.2s ease, border-color 0.2s ease;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def get_stock_suggestions(search_input, df_suggestion, limit=10):
    """Get stock suggestions based on search input with limit."""
    if df_suggestion is None or search_input == "" or len(search_input) < 1:
        return []
    
    search_lower = search_input.lower()
    mask = (
        df_suggestion["Mã"].astype(str).str.lower().str.contains(search_lower, na=False) |
        df_suggestion["Tên công ty"].astype(str).str.lower().str.contains(search_lower, na=False)
    )
    df_filtered = df_suggestion[mask].head(limit)
    
    if df_filtered.empty:
        return []
    
    suggestions = []
    for _, row in df_filtered.iterrows():
        suggestions.append({
            'code': str(row['Mã']),
            'name': str(row['Tên công ty'])
        })
    
    return suggestions


def main():
    st.set_page_config(
        page_title="Hệ thống xuất báo cáo phân tích cổ phiếu tự động",
        page_icon="📊",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Inject custom CSS
    inject_custom_css()
    
    # Main title and subtitle
    st.markdown(
        '<div class="header-container">'
        '<h1 class="app-title"><i class="fas fa-chart-line"></i> HỆ THỐNG XUẤT BÁO CÁO PHÂN TÍCH CỔ PHIẾU TỰ ĐỘNG</h1>'
        '<p class="app-subtitle"><i class="fas fa-search"></i> Hãy nhập mã cổ phiếu của bạn</p>'
        '</div>',
        unsafe_allow_html=True
    )
    
    # Ensure output directories exist
    ensure_output_dirs()
    
    # Load stock suggestions
    suggestion_file_path = str(SUGGESTION_XLSX.resolve())
    try:
        df_suggestion = pd.read_excel(suggestion_file_path, engine='openpyxl')
    except Exception as e:
        st.error(f"Lỗi đọc file gợi ý: {str(e)}")
        df_suggestion = None
    
    # Main search input with autocomplete - Modern design
    # Pre-fill if we have selected_stock
    input_value = ""
    if 'selected_stock' in st.session_state and st.session_state.selected_stock:
        input_value = st.session_state.selected_stock
    
    # Add search icon wrapper with modern styling
    col_search_left, col_search_main, col_search_right = st.columns([0.05, 0.9, 0.05])
    
    with col_search_main:
        search_input = st.text_input(
            label="",
            value=input_value if input_value else "",
            placeholder="🔍 Nhập mã cổ phiếu hoặc tên công ty bạn muốn tìm...",
            key="stock_search"
        )
    
    # Clear selected_stock if user types new input
    if search_input and 'selected_stock' in st.session_state:
        if st.session_state.selected_stock != search_input.strip().upper():
            del st.session_state.selected_stock
    
    # Real-time autocomplete suggestions
    if search_input and len(search_input) >= 1 and 'selected_stock' not in st.session_state:
        suggestions = get_stock_suggestions(search_input, df_suggestion, limit=8)
        
        if suggestions:
            # Display suggestions as clickable items
            st.markdown('<div class="suggestions-box">', unsafe_allow_html=True)
            st.markdown('<p style="padding: 0.5rem 1rem; color: #a0a0a0; font-size: 0.9rem; margin-bottom: 0.5rem;"><i class="fas fa-lightbulb"></i> Gợi ý:</p>', unsafe_allow_html=True)
            for idx, sug in enumerate(suggestions):
                if st.button(
                    f"📈 {sug['code']} - {sug['name']}",
                    key=f"suggestion_{idx}_{sug['code']}",
                    use_container_width=True
                ):
                    # Store selected stock in session state
                    st.session_state.selected_stock = sug['code']
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Get selected stock
    selected_stock = None
    if 'selected_stock' in st.session_state and st.session_state.selected_stock:
        selected_stock = st.session_state.selected_stock
    elif search_input:
        selected_stock = search_input.strip().upper()
    
    # Run button (centered, prominent)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        run_button = st.button(
            "🚀 Tạo Báo Cáo",
            type="primary",
            use_container_width=True
        )
    
    # Processing section
    if run_button and selected_stock:
        stock_code = selected_stock
        
        # Initialize progress tracking
        progress_bar = st.progress(0)
        status_container = st.container()
        
        steps = [
            "Xử lý dữ liệu từ file Excel",
            "Xử lý báo cáo tài chính",
            "Tính toán chỉ báo kỹ thuật",
            "Vẽ và xuất biểu đồ",
            "Phân tích định giá",
            "Tạo báo cáo tổng hợp"
        ]
        
        current_step = 0
        progress = 0
        
        with status_container:
            # Step 1: Data Processor
            current_step = 1
            with st.expander(f"✅ Bước {current_step}: {steps[current_step-1]}", expanded=True):
                st.markdown(f'<div class="step-indicator"><div class="step-number">{current_step}</div><div class="step-text">{steps[current_step-1]}</div></div>', unsafe_allow_html=True)
                try:
                    bs_df = balance_sheet(stock_code)
                    is_df = income_statement(stock_code)
                    cf_df = cash_flow(stock_code)
                    st.success("✓ Dữ liệu đã được xử lý thành công")
                    progress += 16
                    progress_bar.progress(progress)
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
                    st.stop()
            
            # Step 2: Financial Statement
            current_step = 2
            with st.expander(f"✅ Bước {current_step}: {steps[current_step-1]}", expanded=True):
                st.markdown(f'<div class="step-indicator"><div class="step-number">{current_step}</div><div class="step-text">{steps[current_step-1]}</div></div>', unsafe_allow_html=True)
                try:
                    export_financial_reports(bs_df, is_df, cf_df)
                    export_financial_ratios(stock_code, period='year', lang='vi', dropna=True)
                    st.success("✓ Báo cáo tài chính đã được xuất")
                    progress += 16
                    progress_bar.progress(progress)
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
                    st.stop()
            
            # Step 3: Indicators
            current_step = 3
            with st.expander(f"✅ Bước {current_step}: {steps[current_step-1]}", expanded=True):
                st.markdown(f'<div class="step-indicator"><div class="step-number">{current_step}</div><div class="step-text">{steps[current_step-1]}</div></div>', unsafe_allow_html=True)
                try:
                    df_close = get_close_data_from_csv(stock_code)
                    if df_close.empty:
                        st.warning("⚠ Không có dữ liệu giá đóng cửa từ CSV")
                    else:
                        df_sma = SMA_50_20(df_close.copy())
                        df_boll = bollinger_band(df_close.copy())
                        df_rsi = RSI(df_close.copy())
                        df_macd = MACD(df_close.copy())
                        st.success("✓ Chỉ báo kỹ thuật đã được tính toán")
                    progress += 16
                    progress_bar.progress(progress)
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
                    st.stop()
            
            # Step 4: Charts
            current_step = 4
            with st.expander(f"✅ Bước {current_step}: {steps[current_step-1]}", expanded=True):
                st.markdown(f'<div class="step-indicator"><div class="step-number">{current_step}</div><div class="step-text">{steps[current_step-1]}</div></div>', unsafe_allow_html=True)
                try:
                    export_all_plots(stock_code)
                    st.success("✓ Biểu đồ đã được tạo và lưu")
                    progress += 16
                    progress_bar.progress(progress)
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
                    st.stop()
            
            # Step 5: Fundamental Analysis
            current_step = 5
            with st.expander(f"✅ Bước {current_step}: {steps[current_step-1]}", expanded=True):
                st.markdown(f'<div class="step-indicator"><div class="step-number">{current_step}</div><div class="step-text">{steps[current_step-1]}</div></div>', unsafe_allow_html=True)
                try:
                    eps, bvps = get_eps_bvps_2024(stock_code)
                    industry_pe, industry_pb = valuation_index(stock_code)
                    if eps is None or bvps is None or industry_pe is None or industry_pb is None:
                        st.warning("⚠ Không đủ dữ liệu để tính giá cổ phiếu định giá")
                    else:
                        stock_price = calculate_stock_price(eps, bvps, industry_pe, industry_pb)
                        st.metric("Giá cổ phiếu định giá", f"{stock_price:.3f} VND" if stock_price else "N/A")
                        st.success("✓ Phân tích định giá thành công")
                    progress += 16
                    progress_bar.progress(progress)
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
                    st.stop()
            
            # Step 6: Report Generator
            current_step = 6
            with st.expander(f"✅ Bước {current_step}: {steps[current_step-1]}", expanded=True):
                st.markdown(f'<div class="step-indicator"><div class="step-number">{current_step}</div><div class="step-text">{steps[current_step-1]}</div></div>', unsafe_allow_html=True)
                try:
                    generate_stock_report(stock_code)
                    st.success("✓ Báo cáo PDF đã được tạo thành công!")
                    progress = 100
                    progress_bar.progress(progress)
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
                    st.stop()
            
            # Final success message
            st.balloons()
            st.success("🎉 Quá trình hoàn tất! Báo cáo đã sẵn sàng để tải xuống.")
            
            # Get the most recent report (just created)
            all_reports = sorted(
                REPORT_EXPORT_DIR.glob(f"Report_{stock_code.upper()}_*.pdf"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            # Only show the most recent report (just created)
            if all_reports:
                latest_report = all_reports[0]
                st.markdown("---")
                st.markdown(
                    '<div class="download-container">'
                    '<h3 style="color: #60a5fa; margin-bottom: 1.5rem;"><i class="fas fa-download"></i> Tải xuống báo cáo</h3>'
                    '</div>',
                    unsafe_allow_html=True
                )
                
                with open(latest_report, "rb") as pdf_file:
                    st.download_button(
                        label=f"⬇️ Tải báo cáo {stock_code.upper()}",
                        data=pdf_file.read(),
                        file_name=latest_report.name,
                        mime="application/pdf",
                        key="download_current_report",
                        use_container_width=True
                    )
    
    elif run_button and not selected_stock:
        st.warning("⚠️ Vui lòng nhập mã cổ phiếu trước khi tạo báo cáo")


if __name__ == '__main__':
    main()
