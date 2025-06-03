import os
import google.generativeai as genai
from dotenv import load_dotenv

# Hàm hỏi Gemini AI với bất kỳ câu hỏi nào
def ask_gemini(prompt):
    # Load biến môi trường
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("API Key chưa được đặt. Vui lòng kiểm tra file .env")

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

    # Tạo model
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=generation_config,
        safety_settings=safety_settings,
        system_instruction="Bạn là một chuyên gia phân tích tài chính chuyên về cổ phiếu."
    )

    try:
        response = model.generate_content(prompt)
        return response.text.strip().replace("*", "")
    except Exception as e:
        return f"Lỗi khi gọi Gemini API: {str(e)}"
