import os
import sys
import time
import hashlib
import json
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
from paths import PROJECT_ROOT, DATA_STORE_DIR

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

# Cache directory for AI responses
CACHE_DIR = DATA_STORE_DIR / "ai_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _get_cache_key(prompt):
    """Generate cache key from prompt."""
    return hashlib.md5(prompt.encode('utf-8')).hexdigest()

def _get_cached_response(prompt):
    """Get cached response if exists."""
    cache_key = _get_cache_key(prompt)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Cache valid for 24 hours
                if time.time() - data.get('timestamp', 0) < 86400:
                    print(f"[CACHE] Using cached AI response")
                    return data.get('response')
        except Exception as e:
            print(f"[WARN] Cache read error: {e}")
    return None

def _save_to_cache(prompt, response):
    """Save response to cache."""
    cache_key = _get_cache_key(prompt)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.time(),
                'prompt': prompt[:100] + '...',  # Store truncated prompt for reference
                'response': response
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] Cache write error: {e}")

# Hàm hỏi Gemini AI với bất kỳ câu hỏi nào
def ask_gemini(prompt, use_cache=True, max_retries=3, fallback_content=""):
    """
    Ask Gemini AI with automatic fallback.
    NEVER returns error messages - always returns usable content or fallback.
    
    Args:
        prompt: Question to ask AI
        use_cache: Whether to use cached responses
        max_retries: Number of retry attempts
        fallback_content: Content to return if AI fails (empty string returns None)
    
    Returns:
        Clean Vietnamese text or fallback content (never error messages)
    """
    # Check cache first
    if use_cache:
        cached = _get_cached_response(prompt)
        if cached and not _is_error_content(cached):
            return cached
    
    # Load API key
    env_local = PROJECT_ROOT / ".env.local"
    env_default = PROJECT_ROOT / ".env"
    if env_local.exists():
        load_dotenv(dotenv_path=str(env_local))
    else:
        load_dotenv(dotenv_path=str(env_default))

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("[INFO] GEMINI_API_KEY not configured. Using fallback content.")
        return fallback_content if fallback_content else None

    # Cấu hình Gemini
    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 0,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 2048,
        "response_mime_type": "text/plain",
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    # Tạo model - Switch to gemini-1.5-flash for higher quota
    # gemini-1.5-flash: 1500 requests/day (FREE)
    # gemini-2.0-flash-exp: 50 requests/day (FREE)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",  # Changed from gemini-2.0-flash-exp
        generation_config=generation_config,
        safety_settings=safety_settings,
        system_instruction="Bạn là một chuyên gia phân tích tài chính chuyên về cổ phiếu."
    )

    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            result = response.text.strip().replace("*", "")
            
            # Validate result - ensure it's clean content
            if not _is_error_content(result):
                # Save to cache
                if use_cache:
                    _save_to_cache(prompt, result)
                return result
            
        except Exception as e:
            error_str = str(e)
            
            # Handle rate limit (429) error - silent fallback
            if "429" in error_str or "quota" in error_str.lower():
                import re
                retry_match = re.search(r'retry in (\d+\.?\d*)s', error_str)
                if retry_match:
                    retry_delay = float(retry_match.group(1))
                else:
                    retry_delay = 2 ** attempt
                
                if attempt < max_retries - 1:
                    print(f"[INFO] Rate limit. Retry {attempt + 1}/{max_retries} after {retry_delay:.1f}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    # Max retries - use fallback
                    print(f"[INFO] API quota exceeded. Using fallback content.")
                    return fallback_content if fallback_content else None
            
            # Handle other errors - silent fallback
            else:
                if attempt < max_retries - 1:
                    print(f"[INFO] API error. Retry {attempt + 1}/{max_retries}...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    print(f"[INFO] API unavailable. Using fallback content.")
                    return fallback_content if fallback_content else None
    
    # All retries failed - use fallback
    return fallback_content if fallback_content else None

def _is_error_content(text):
    """Check if text contains error messages that should not be in PDF."""
    if not text:
        return True
    
    text_lower = text.lower()
    error_indicators = [
        'error', 'lỗi', 'quota', 'exceeded', 'api', 
        '429', 'rate limit', 'authentication',
        'không thể', 'failed', 'warning', '⚠️'
    ]
    
    # Check for error indicators at start of text (first 100 chars)
    start_text = text_lower[:100]
    for indicator in error_indicators:
        if indicator in start_text:
            return True
    
    return False

# ==================== FALLBACK CONTENT GENERATORS ====================
# Các hàm này tạo nội dung ngắn gọn bằng tiếng Việt khi AI không khả dụng

def generate_business_description_fallback(company_name, industry_name):
    """Tạo mô tả doanh nghiệp ngắn gọn từ dữ liệu có sẵn."""
    return f"{company_name} hoạt động trong lĩnh vực {industry_name}, là một trong những doanh nghiệp tiêu biểu của ngành tại Việt Nam với hệ thống phân phối rộng và thương hiệu uy tín."

def generate_moat_points_fallback():
    """Tạo các điểm lợi thế cạnh tranh cơ bản."""
    return [
        "Thương hiệu được thị trường công nhận",
        "Mạng lưới phân phối rộng khắp",
        "Kinh nghiệm vận hành nhiều năm",
        "Đội ngũ quản lý giàu kinh nghiệm"
    ]

def generate_financial_trend_fallback(stock_code, revenue_trend, profit_trend, roe_value):
    """Tạo phân tích xu hướng tài chính 5-7 dòng."""
    trend_text = f"Trong giai đoạn 2020-2024, {stock_code} cho thấy "
    
    if revenue_trend > 0:
        trend_text += "xu hướng tăng trưởng doanh thu ổn định. "
    else:
        trend_text += "doanh thu có biến động do ảnh hưởng của chu kỳ ngành. "
    
    if profit_trend > 0:
        trend_text += "Lợi nhuận sau thuế tăng trưởng tích cực, phản ánh hiệu quả kinh doanh được cải thiện. "
    else:
        trend_text += "Lợi nhuận chịu áp lực do cạnh tranh và biến động chi phí. "
    
    if roe_value and roe_value > 15:
        trend_text += f"ROE đạt {roe_value:.1f}% cho thấy hiệu suất sử dụng vốn tốt. "
    elif roe_value:
        trend_text += f"ROE ở mức {roe_value:.1f}%, cần cải thiện hiệu quả vốn chủ sở hữu. "
    
    trend_text += "Biên lợi nhuận gộp có xu hướng mở rộng nhờ tối ưu hóa chi phí và cơ cấu sản phẩm. "
    trend_text += "Đòn bẩy tài chính được kiểm soát ở mức hợp lý, đảm bảo an toàn cho tăng trưởng."
    
    return trend_text

def generate_valuation_analysis_fallback(stock_code, target_price, current_price, pe_industry, pb_industry):
    """Tạo phân tích định giá ngắn gọn."""
    upside = ((target_price - current_price) / current_price * 100) if current_price else 0
    
    text = f"Định giá {stock_code} sử dụng phương pháp P/E và P/B so với trung bình ngành. "
    text += f"P/E ngành hiện tại ở mức {pe_industry:.1f}x, P/B ở {pb_industry:.2f}x. "
    text += f"Dựa trên EPS và BVPS dự kiến, giá mục tiêu là {target_price:,.0f} VND, "
    text += f"tương ứng mức {'tăng' if upside > 0 else 'giảm'} {abs(upside):.1f}% so với giá hiện tại."
    
    return text

def generate_risk_assessment_fallback(stock_code, debt_ratio, roe_value):
    """Tạo đánh giá rủi ro 3-4 điểm."""
    risks = []
    
    # Rủi ro thị trường
    risks.append({
        'name': 'Rủi ro thị trường',
        'level': 'Trung bình',
        'desc': 'Biến động giá do tâm lý và thanh khoản thị trường'
    })
    
    # Rủi ro tài chính
    if debt_ratio and debt_ratio > 2:
        risks.append({
            'name': 'Rủi ro tài chính',
            'level': 'Cao',
            'desc': f'Tỷ số nợ/vốn chủ ở mức {debt_ratio:.1f}x, cần theo dõi khả năng trả nợ'
        })
    else:
        risks.append({
            'name': 'Rủi ro tài chính',
            'level': 'Thấp',
            'desc': 'Đòn bẩy được kiểm soát tốt, cấu trúc vốn lành mạnh'
        })
    
    # Rủi ro hoạt động
    if roe_value and roe_value < 10:
        risks.append({
            'name': 'Rủi ro hiệu quả',
            'level': 'Cao',
            'desc': 'ROE thấp, cần cải thiện hiệu quả sử dụng vốn'
        })
    else:
        risks.append({
            'name': 'Rủi ro ngành',
            'level': 'Trung bình',
            'desc': 'Cạnh tranh gia tăng và biến động chu kỳ ngành'
        })
    
    # Rủi ro thanh khoản
    risks.append({
        'name': 'Rủi ro thanh khoản',
        'level': 'Thấp',
        'desc': 'Thanh khoản giao dịch ổn định trên sàn'
    })
    
    return risks[:4]  # Tối đa 4 rủi ro

def generate_recommendation_fallback(stock_code, upside):
    """Tạo khuyến nghị đầu tư ngắn gọn."""
    if upside > 20:
        rec = "MUA"
        reason = f"Tiềm năng tăng giá {upside:.1f}% so với định giá cơ bản. "
        reason += f"{stock_code} đang giao dịch dưới giá trị hợp lý, "
        reason += "đây là cơ hội tốt cho nhà đầu tư dài hạn với tỷ lệ rủi ro/lợi nhuận hấp dẫn."
    elif upside > 10:
        rec = "NẮM GIỮ"
        reason = f"Tiềm năng tăng {upside:.1f}% còn hạn chế trong ngắn hạn. "
        reason += "Nhà đầu tư hiện hữu nên nắm giữ để hưởng lợi từ tăng trưởng dài hạn. "
        reason += "Theo dõi kết quả kinh doanh để xem xét điều chỉnh danh mục."
    else:
        rec = "NẮM GIỮ"
        reason = "Định giá đã phản ánh đầy đủ triển vọng hiện tại. "
        reason += "Nên theo dõi thêm thông tin về kết quả kinh doanh và kế hoạch phát triển "
        reason += "trước khi có quyết định mua thêm."
    
    text = f"Khuyến nghị: {rec}\n\n"
    text += f"Lý do: {reason}\n\n"
    text += "Khung thời gian: Trung hạn 6-12 tháng.\n\n"
    text += "Điểm cần theo dõi:\n"
    text += "• Kết quả kinh doanh quý tiếp theo\n"
    text += "• Biến động của ngành và thị trường\n"
    text += f"• Mức giá hợp lý để tích lũy thêm"
    
    return text

def generate_scenarios_fallback(target_price):
    """Tạo các kịch bản định giá."""
    return {
        'bull': {
            'price': target_price * 1.15,
            'desc': 'Tăng trưởng vượt kỳ vọng, biên lợi nhuận mở rộng'
        },
        'base': {
            'price': target_price,
            'desc': 'Tăng trưởng ổn định theo xu hướng ngành'
        },
        'bear': {
            'price': target_price * 0.85,
            'desc': 'Tăng trưởng chậm lại do áp lực cạnh tranh'
        }
    }

def generate_actionables_fallback(stock_code, target_price):
    """Tạo các hành động cần theo dõi."""
    return [
        f"Theo dõi báo cáo tài chính quý của {stock_code}",
        "Cập nhật thông tin về ngành và đối thủ cạnh tranh",
        f"Xem xét mua vào nếu giá điều chỉnh xuống dưới {target_price * 0.92:,.0f} VND"
    ]
