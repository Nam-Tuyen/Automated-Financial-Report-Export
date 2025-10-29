# ai_sections.py - Gom tất cả AI sections vào 1 prompt JSON
import json
import re
from ai_cache import load_cache, save_cache, _hash_context, ai_backoff_sleep

SECTIONS = ["executive", "industry", "trend", "risk", "recommendation"]

def build_context_for_ai(stock_code, company_name, industry_name, key_metrics, trend_data):
    """
    Build context từ dữ liệu sẵn có.
    
    Args:
        stock_code: Mã cổ phiếu
        company_name: Tên công ty
        industry_name: Ngành
        key_metrics: Dict các chỉ số chính (ROE, EPS, P/E, P/B, etc.)
        trend_data: Dict {year: {ROE, ROA, EPS, PE}}
    
    Returns:
        dict: Context để hash và gửi cho AI
    """
    return {
        "stock": stock_code.upper(),
        "company": company_name,
        "industry": industry_name,
        "key": {k: str(v) for k, v in (key_metrics or {}).items()},
        "trend": trend_data,
        "lang": "vi",
        "lengths": {
            "executive": "4-5 dòng",
            "industry": "4-5 dòng",
            "trend": "4-5 dòng",
            "risk": "4 rủi ro",
            "recommendation": "4-5 dòng"
        }
    }

def ai_prompt_from_context(ctx: dict) -> str:
    """
    Tạo prompt yêu cầu AI trả về JSON thuần với tất cả sections.
    
    Returns:
        str: Prompt đầy đủ cho AI
    """
    return (
f"""Bạn là chuyên gia phân tích cổ phiếu chuyên sâu. Trả về JSON **thuần** (không markdown), schema:

{{
  "executive": "<4-5 dòng phân tích đầu tư có chiều sâu>",
  "industry": "<4-5 dòng phân tích bối cảnh ngành với insight>",
  "trend": "<4-5 dòng phân tích xu hướng tài chính có chiều sâu>",
  "risk": "<4 rủi ro quan trọng, mỗi rủi ro 1 dòng ngắn gọn với mức độ>",
  "recommendation": "<4-5 dòng khuyến nghị đầu tư chi tiết>"
}}

Dữ liệu phân tích:

Mã: {ctx['stock']}
Công ty: {ctx['company']}
Ngành: {ctx['industry']}
Chỉ số chính: {json.dumps(ctx['key'], ensure_ascii=False)}
Xu hướng 2020-2024: {json.dumps(ctx['trend'], ensure_ascii=False)}

YÊU CẦU PHÂN TÍCH:

1. EXECUTIVE (4-5 dòng):
   - Luận điểm đầu tư chính dựa trên số liệu
   - Điểm nổi bật về tài chính và vị thế cạnh tranh
   - Đánh giá định giá hiện tại
   - Triển vọng ngắn-trung hạn
   
2. INDUSTRY (4-5 dòng):
   - Bối cảnh vĩ mô ảnh hưởng đến ngành
   - Động lực tăng trưởng hoặc thách thức của ngành
   - Vị thế của công ty trong ngành (nếu suy luận được)
   - Triển vọng ngành 1-2 năm tới
   
3. TREND (4-5 dòng):
   - Phân tích sâu xu hướng ROE, ROA, EPS qua 5 năm
   - Giải thích nguyên nhân biến động (tăng/giảm)
   - Đánh giá chất lượng lợi nhuận
   - So sánh với chu kỳ trước và kỳ vọng tương lai
   
4. RISK (4 rủi ro):
   - Mỗi rủi ro: [Tên] (Mức độ: Cao/TrB/Thấp): [Mô tả ngắn]
   - Ưu tiên rủi ro quan trọng nhất
   - Dựa trên số liệu tài chính và ngành
   
5. RECOMMENDATION (4-5 dòng):
   - Khuyến nghị rõ ràng: MUA/NẮM GIỮ/BÁN
   - Giá mục tiêu (nếu đủ dữ liệu)
   - 3-4 lý do chính hỗ trợ khuyến nghị
   - Điều kiện để nâng/hạ khuyến nghị
   - Khung thời gian đầu tư

NGUYÊN TẮC:
- Mỗi section PHẢI đủ 4-5 dòng, không được ngắn hơn
- Phân tích có chiều sâu, không chỉ liệt kê số liệu
- Giải thích "tại sao" và "điều gì tiếp theo"
- Dùng số liệu để chứng minh luận điểm
- 100% tiếng Việt, không nhắc AI/API/quota
- Trả về JSON hợp lệ, không bọc ```
"""
    ).strip()

def parse_json_loose(txt: str) -> dict:
    """
    Parse JSON từ response, xử lý cả trường hợp model bọc ```json ... ```.
    
    Args:
        txt: Response text từ AI
    
    Returns:
        dict: Parsed JSON
    
    Raises:
        json.JSONDecodeError: Nếu không parse được
    """
    # Nếu model lỡ bọc ```json ... ```
    txt = txt.strip()
    
    # Remove markdown code block nếu có
    if txt.startswith("```"):
        # Extract JSON từ code block
        m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", txt, flags=re.S)
        if m:
            txt = m.group(1)
    
    # Extract JSON object từ text
    m = re.search(r"\{.*\}", txt, flags=re.S)
    raw = m.group(0) if m else txt
    
    return json.loads(raw)

def offline_fallback(ctx: dict) -> dict:
    """
    Tạo nội dung 4-5 dòng có chiều sâu khi hết quota hoặc API lỗi.
    
    Args:
        ctx: Context dict từ build_context_for_ai()
    
    Returns:
        dict: Tất cả sections với fallback content (4-5 dòng mỗi section)
    """
    key = ctx.get("key", {})
    stock = ctx.get("stock", "")
    company = ctx.get("company", "")
    industry = ctx.get("industry", "")
    trend_data = ctx.get("trend", {})
    
    roe = key.get("ROE", "N/A")
    pe = key.get("P/E", "N/A")
    eps = key.get("EPS", "N/A")
    pb = key.get("P/B", "N/A")
    debt = key.get("Nợ/VCSH", "N/A")
    
    # Phân tích xu hướng ROE nếu có data
    roe_trend = ""
    if trend_data:
        years = sorted(trend_data.keys())
        if len(years) >= 2:
            first_year = years[0]
            last_year = years[-1]
            first_roe = trend_data[first_year].get("ROE", "")
            last_roe = trend_data[last_year].get("ROE", "")
            if first_roe and last_roe:
                try:
                    first_val = float(first_roe.replace("%", ""))
                    last_val = float(last_roe.replace("%", ""))
                    if last_val > first_val:
                        roe_trend = "cải thiện"
                    else:
                        roe_trend = "điều chỉnh"
                except:
                    pass
    
    # Executive summary (4-5 dòng có chiều sâu)
    executive = (
        f"{stock} – {company} hoạt động trong ngành {industry} với vị thế cạnh tranh ổn định. "
        f"Hiệu quả sử dụng vốn chủ đạt ROE {roe}, phản ánh khả năng sinh lời hợp lý từ vốn đầu tư. "
        f"Định giá hiện tại với P/E {pe} và P/B {pb} cho thấy thị trường đánh giá công ty ở mức trung bình so với ngành. "
        f"Triển vọng ngắn hạn phụ thuộc vào khả năng duy trì biên lợi nhuận và tối ưu hóa hiệu quả hoạt động. "
        f"Nhà đầu tư nên theo dõi sát xu hướng doanh thu và biến động chi phí trong các quý tới để đánh giá tiềm năng tăng trưởng."
    )
    
    # Industry analysis (4-5 dòng có insight)
    industry_text = (
        f"Ngành {industry} đang trong giai đoạn tái cấu trúc với cạnh tranh gia tăng về giá và dịch vụ. "
        "Nhu cầu thị trường duy trì ổn định nhờ tăng trưởng kinh tế vĩ mô, tuy nhiên áp lực biên lợi nhuận từ chi phí đầu vào và chiết khấu khuyến mãi vẫn là thách thức lớn. "
        "Các doanh nghiệp có lợi thế về chuỗi cung ứng, quan hệ nhà cung cấp và mạng lưới phân phối sẽ giữ được thị phần trong môi trường cạnh tranh khốc liệt. "
        "Xu hướng số hóa và thương mại điện tử đang thay đổi hành vi tiêu dùng, tạo cơ hội cho các doanh nghiệp chuyển đổi nhanh. "
        "Triển vọng trung hạn của ngành phụ thuộc vào khả năng phục hồi sức mua và chính sách kinh tế vĩ mô hỗ trợ tăng trưởng."
    )
    
    # Trend analysis (4-5 dòng phân tích sâu)
    trend_insight = f" {roe_trend}" if roe_trend else ""
    trend = (
        f"Phân tích xu hướng tài chính 5 năm cho thấy ROE{trend_insight}, phản ánh hiệu quả sử dụng vốn của công ty qua các chu kỳ kinh doanh. "
        f"EPS dao động cho thấy lợi nhuận chịu ảnh hưởng từ biến động chi phí và cạnh tranh thị trường, đòi hỏi công ty phải liên tục tối ưu hóa cơ cấu chi phí. "
        f"Tỷ số nợ/vốn chủ {debt} cho thấy đòn bẩy tài chính được kiểm soát ở mức hợp lý, tạo dư địa cho đầu tư mở rộng mà không gây áp lực thanh khoản quá lớn. "
        "Chất lượng lợi nhuận cần được đánh giá thông qua dòng tiền hoạt động và khả năng chuyển đổi lợi nhuận kế toán thành tiền mặt thực tế. "
        "Kỳ vọng tương lai phụ thuộc vào khả năng công ty duy trì tăng trưởng doanh thu và cải thiện biên lợi nhuận gộp trong bối cảnh cạnh tranh gia tăng."
    )
    
    # Risk assessment (4 rủi ro chi tiết)
    risk = (
        "• Rủi ro cạnh tranh (Cao): Áp lực giá và chiết khấu từ đối thủ có thể làm xói mòn biên lợi nhuận, đặc biệt trong phân khúc giá thấp và trung bình\n"
        "• Rủi ro chuỗi cung ứng (Trung bình): Phụ thuộc vào nhà cung cấp chính có thể dẫn đến gián đoạn nguồn hàng hoặc tăng chi phí đầu vào khi có biến động thị trường\n"
        "• Rủi ro vận hành (Trung bình): Hiệu quả quản lý tồn kho và vòng quay hàng hóa ảnh hưởng trực tiếp đến dòng tiền và khả năng thanh khoản ngắn hạn\n"
        "• Rủi ro vĩ mô (Trung bình): Biến động tỷ giá, lạm phát và chính sách tiền tệ tác động đến chi phí nhập khẩu và sức mua của người tiêu dùng"
    )
    
    # Investment recommendation (4-5 dòng chi tiết)
    recommendation = (
        f"Khuyến nghị: NẮM GIỮ. Định giá hiện tại với P/E {pe} phản ánh hợp lý triển vọng tăng trưởng và rủi ro của công ty so với mức trung bình ngành. "
        "Nhà đầu tư hiện hữu nên nắm giữ để hưởng lợi từ cổ tức (nếu có) và tiềm năng tăng trưởng dài hạn khi công ty cải thiện hiệu quả hoạt động. "
        "Điều kiện để nâng lên MUA là khi công ty công bố kết quả kinh doanh vượt kỳ vọng với biên lợi nhuận gộp mở rộng rõ rệt và doanh thu tăng trưởng bền vững. "
        "Ngược lại, cần xem xét BÁN nếu ROE giảm sâu dưới 10% hoặc tỷ số nợ/vốn chủ vượt 3 lần mà không có kế hoạch tái cấu trúc rõ ràng. "
        "Khung thời gian đầu tư khuyến nghị là trung hạn 6-12 tháng, theo dõi sát báo cáo tài chính quý để điều chỉnh danh mục kịp thời."
    )
    
    return {
        "executive": executive,
        "industry": industry_text,
        "trend": trend,
        "risk": risk,
        "recommendation": recommendation
    }

def get_ai_sections(stock_code, company_name, industry_name, key_metrics, trend_data, ask_gemini_fn):
    """
    Lấy tất cả AI sections trong 1 lần gọi (hoặc từ cache).
    
    Args:
        stock_code: Mã cổ phiếu
        company_name: Tên công ty
        industry_name: Ngành
        key_metrics: Dict các chỉ số chính
        trend_data: Dict xu hướng theo năm
        ask_gemini_fn: Function để gọi AI (ask_gemini từ ai_analyst.py)
    
    Returns:
        dict: {
            "executive": str,
            "industry": str,
            "trend": str,
            "risk": str,
            "recommendation": str
        }
    """
    # 1) Build context
    ctx = build_context_for_ai(stock_code, company_name, industry_name, key_metrics, trend_data)
    ctx_hash = _hash_context(ctx)
    
    # 2) Thử load cache
    cached, cached_hash = load_cache(stock_code)
    if cached and cached_hash == ctx_hash:
        print(f"[AI] Using cached sections for {stock_code}")
        return cached
    
    # 3) Tạo prompt
    prompt = ai_prompt_from_context(ctx)
    
    # 4) Gọi AI với backoff retry
    for i in range(3):
        try:
            print(f"[AI] Calling AI for all sections of {stock_code} (attempt {i+1}/3)...")
            raw = ask_gemini_fn(prompt, use_cache=False)  # Không dùng cache cũ của ask_gemini
            
            # Parse JSON
            data = parse_json_loose(raw)
            
            # Validate: bảo đảm đủ key
            for k in SECTIONS:
                if k not in data or not data[k]:
                    print(f"[WARN] Missing section '{k}', using fallback for this section")
                    fb = offline_fallback(ctx)
                    data[k] = fb[k]
            
            # Save cache
            save_cache(stock_code, ctx_hash, data)
            print(f"[AI] Successfully generated all sections for {stock_code}")
            return data
            
        except Exception as e:
            error_str = str(e)
            print(f"[ERROR] AI call failed: {error_str[:100]}")
            
            # Xử lý 429 - quota exceeded
            if "429" in error_str or "Too Many Requests" in error_str.lower() or "quota" in error_str.lower():
                if i < 2:  # Còn retry
                    ai_backoff_sleep(i)
                    continue
                else:
                    # Hết retry → fallback
                    print(f"[FALLBACK] API quota exceeded for {stock_code}, using offline content")
                    fb = offline_fallback(ctx)
                    save_cache(stock_code, ctx_hash, fb)
                    return fb
            else:
                # Lỗi khác → fallback ngay
                print(f"[FALLBACK] API error for {stock_code}, using offline content")
                fb = offline_fallback(ctx)
                save_cache(stock_code, ctx_hash, fb)
                return fb
    
    # 5) Hết retry → fallback
    print(f"[FALLBACK] All retries failed for {stock_code}, using offline content")
    fb = offline_fallback(ctx)
    save_cache(stock_code, ctx_hash, fb)
    return fb

def build_trend_data(fr_df):
    """
    Chuẩn bị trend data gọn cho AI từ financial ratios DataFrame.
    
    Args:
        fr_df: DataFrame chỉ số tài chính (đã convert, index = năm)
    
    Returns:
        dict: {year: {ROE, ROA, EPS, PE}}
    """
    out = {}
    for y in ["2020", "2021", "2022", "2023", "2024"]:
        if y in fr_df.index:
            r = fr_df.loc[y]
            out[y] = {
                "ROE": str(r.get("ROE (%)", "")),
                "ROA": str(r.get("ROA (%)", "")),
                "EPS": str(r.get("EPS (VND)", "")),
                "PE": str(r.get("P/E", "")),
            }
    return out

