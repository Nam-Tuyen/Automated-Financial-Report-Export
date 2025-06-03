import pandas as pd

# Đường dẫn tới file CSV
file_path = "Data/Data raw/FT2325.csv"

def get_close_data_from_csv(stock_code):
    """
    Lấy dữ liệu giá đóng cửa và thời gian cho một cổ phiếu từ file CSV.
    
    - Dữ liệu được lấy từ file CSV có định dạng với cột 'Ticker', 'Date', và 'Close'.
    - Dữ liệu được lọc theo mã cổ phiếu (stock_code) và khoảng thời gian từ 03/01/2023 đến 04/03/2025.
    
    Parameters:
    - stock_code (str): Mã cổ phiếu cần lấy dữ liệu.
    
    Returns:
    - DataFrame chứa các cột "Date" và "Close" của cổ phiếu trong khoảng thời gian yêu cầu.
    """
    # Đọc dữ liệu từ file CSV
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File không tồn tại: {file_path}")
        return pd.DataFrame()

    # Đảm bảo rằng cột 'Date' được chuyển thành kiểu datetime
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

    # Lọc dữ liệu theo mã cổ phiếu
    df_filtered = df[df['Ticker'] == stock_code]

    # Lọc dữ liệu theo thời gian từ 03/01/2023 đến 04/03/2025
    start_date = pd.to_datetime("2023-01-03")
    end_date = pd.to_datetime("2025-03-04")
    df_filtered = df_filtered[(df_filtered['Date'] >= start_date) & (df_filtered['Date'] <= end_date)]

    # Kiểm tra nếu dữ liệu trống
    if df_filtered.empty:
        print(f"Không có dữ liệu cho mã cổ phiếu {stock_code} trong khoảng thời gian yêu cầu.")
        return pd.DataFrame()

    # Trả về chỉ cột "Date" và "Close"
    return df_filtered[['Date', 'Close']]


def fill_missing(series):
    """
    Điền giá trị bị thiếu trong chuỗi dữ liệu bằng phương pháp nội suy tuyến tính.
    Phương pháp này lấy trung bình của giá trị đứng trước và sau giá trị bị thiếu.
    """
    return series.interpolate(method='linear', limit_direction='both')


def SMA_50_20(df_stock):
    """
    Tính toán đường trung bình động đơn giản (SMA) cho 50 ngày và 20 ngày từ giá đóng cửa.
    
    Tham số:
    - df_stock: DataFrame chứa dữ liệu lịch sử giá cổ phiếu với ít nhất cột "time" và "close".
    
    Trả về:
    - df_stock với thêm các cột "SMA_50" và "SMA_20" cho các giá trị SMA tương ứng.
    """
    # Đảm bảo rằng DataFrame có cột "close"
    if 'Close' not in df_stock.columns:
        raise ValueError("DataFrame không có cột 'Close'.")

    # Tính toán SMA 50 và SMA 20
    df_stock['SMA_50'] = df_stock['Close'].rolling(window=50).mean()
    df_stock['SMA_20'] = df_stock['Close'].rolling(window=20).mean()
    
    # Điền giá trị thiếu (NaN) bằng nội suy tuyến tính sau khi tính toán SMA
    df_stock['SMA_50'] = fill_missing(df_stock['SMA_50'])
    df_stock['SMA_20'] = fill_missing(df_stock['SMA_20'])

    return df_stock


def bollinger_band(df_stock, window=20):
    """
    Tính toán các dải Bollinger (Upper Band, Lower Band) và SMA từ giá đóng cửa.
    
    Tham số:
    - df_stock: DataFrame chứa dữ liệu lịch sử giá cổ phiếu với ít nhất cột "time" và "close".
    - window: Số ngày tính toán cho SMA và độ lệch chuẩn, mặc định là 20 ngày.
    
    Trả về:
    - DataFrame với các cột bổ sung: "SMA", "Upper Band", "Lower Band".
    """
    # Đảm bảo rằng DataFrame có cột "Close"
    if 'Close' not in df_stock.columns:
        raise ValueError("DataFrame không có cột 'Close'.")
    
    # Tính toán SMA
    df_stock['SMA'] = df_stock['Close'].rolling(window=window).mean()
    
    # Tính độ lệch chuẩn của giá đóng cửa
    df_stock['std_dev'] = df_stock['Close'].rolling(window=window).std()
    
    # Tính dải trên và dải dưới
    df_stock['Upper Band'] = df_stock['SMA'] + (2 * df_stock['std_dev'])
    df_stock['Lower Band'] = df_stock['SMA'] - (2 * df_stock['std_dev'])

    # Điền giá trị thiếu trong các dải Bollinger
    df_stock['Upper Band'] = fill_missing(df_stock['Upper Band'])
    df_stock['Lower Band'] = fill_missing(df_stock['Lower Band'])
    
    # Xóa cột "std_dev" nếu không cần thiết nữa
    df_stock = df_stock.drop(columns=['std_dev'])
    
    return df_stock


def RSI(df_stock, window=14):
    """
    Tính toán chỉ số sức mạnh tương đối (RSI) từ giá đóng cửa của cổ phiếu.
    
    Tham số:
    - df_stock: DataFrame chứa dữ liệu lịch sử giá cổ phiếu với ít nhất cột "time" và "close".
    - window: Số ngày tính toán RSI, mặc định là 14 ngày.
    
    Trả về:
    - DataFrame với thêm cột "RSI" chứa giá trị RSI tính toán.
    """
    # Đảm bảo rằng DataFrame có cột "Close"
    if 'Close' not in df_stock.columns:
        raise ValueError("DataFrame không có cột 'Close'.")

    # Tính toán thay đổi giá
    df_stock['delta'] = df_stock['Close'].diff()

    # Tính toán giá trị tăng và giá trị giảm
    df_stock['gain'] = df_stock['delta'].where(df_stock['delta'] > 0, 0)
    df_stock['loss'] = -df_stock['delta'].where(df_stock['delta'] < 0, 0)

    # Tính toán trung bình động (SMA) của giá trị tăng và giảm trong cửa sổ `window` ngày
    df_stock['avg_gain'] = df_stock['gain'].rolling(window=window).mean()
    df_stock['avg_loss'] = df_stock['loss'].rolling(window=window).mean()

    # Tránh trường hợp chia cho 0
    df_stock['rs'] = df_stock['avg_gain'] / df_stock['avg_loss']
    df_stock['rsi'] = 100 - (100 / (1 + df_stock['rs']))

    # Điền giá trị thiếu (NaN) trong RSI bằng nội suy tuyến tính
    df_stock['rsi'] = fill_missing(df_stock['rsi'])

    # Loại bỏ các cột không cần thiết
    df_stock = df_stock.drop(columns=['delta', 'gain', 'loss', 'avg_gain', 'avg_loss', 'rs'])
    
    return df_stock


def MACD(df_stock, fast_window=12, slow_window=26, signal_window=9):
    """
    Tính toán chỉ số MACD, Signal Line và Histogram từ giá đóng cửa của cổ phiếu.
    
    Tham số:
    - df_stock: DataFrame chứa dữ liệu lịch sử giá cổ phiếu với ít nhất cột "time" và "close".
    - fast_window: Số ngày tính toán EMA ngắn hạn (mặc định 12 ngày).
    - slow_window: Số ngày tính toán EMA dài hạn (mặc định 26 ngày).
    - signal_window: Số ngày tính toán Signal Line (mặc định 9 ngày).
    
    Trả về:
    - DataFrame với các cột bổ sung: "MACD", "Signal Line", "Histogram".
    """
    # Đảm bảo rằng DataFrame có cột "Close"
    if 'Close' not in df_stock.columns:
        raise ValueError("DataFrame không có cột 'Close'.")
    
    # Tính toán EMA của giá đóng cửa
    df_stock['EMA_fast'] = df_stock['Close'].ewm(span=fast_window, adjust=False).mean()
    df_stock['EMA_slow'] = df_stock['Close'].ewm(span=slow_window, adjust=False).mean()

    # Tính toán MACD Line (Sự chênh lệch giữa EMA(12) và EMA(26))
    df_stock['MACD'] = df_stock['EMA_fast'] - df_stock['EMA_slow']

    # Tính toán Signal Line (EMA của MACD trong cửa sổ 9 ngày)
    df_stock['Signal Line'] = df_stock['MACD'].ewm(span=signal_window, adjust=False).mean()

    # Tính toán Histogram (MACD Line - Signal Line)
    df_stock['Histogram'] = df_stock['MACD'] - df_stock['Signal Line']

    # Điền giá trị thiếu trong MACD, Signal Line và Histogram bằng nội suy tuyến tính
    df_stock['MACD'] = fill_missing(df_stock['MACD'])
    df_stock['Signal Line'] = fill_missing(df_stock['Signal Line'])
    df_stock['Histogram'] = fill_missing(df_stock['Histogram'])

    # Xóa các cột không cần thiết nếu không sử dụng nữa
    df_stock = df_stock.drop(columns=['EMA_fast', 'EMA_slow'])

    return df_stock
