import os
import re
import asyncio
from pathlib import Path
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Please pip install google-genai")
    exit(1)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

TARGET_DIR = Path("storage/files/thiet-bi-chan-doan-hinh-anh/chung")

PROMPT_TEMPLATE = """Bạn là chuyên gia thiết bị y tế.
Tôi có một thư mục lưu hồ sơ tài liệu của một loại máy, thư mục này bị mất tên.
Dưới đây là danh sách các File bên trong thư mục đó:

{file_list}

Dựa vào tên các File này, hãy đoán xem thư mục này chứa tài liệu của thiết bị / hệ thống y tế tên là gì?
Vui lòng trả lời NGẮN GỌN chỉ bằng tên thiết bị dạng kebab-case chuẩn (ví dụ: he-thong-ct-dem-photon, arietta-50). KHÔNG viết giải thích.
Nếu không thể đoán ra thiết bị cụ thể nào, hãy trả về 'unknown-device'.
"""

def get_kebab_name(folder_path: Path) -> str:
    files = []
    # Collect all file names recursively
    for root, _, fs in os.walk(folder_path):
        for f in fs:
            files.append(f)
            
    if not files:
        return "empty-folder"
        
    prompt = PROMPT_TEMPLATE.format(file_list="\n".join([f"- {name}" for name in files[:30]])) # Max 30 files
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return response.text.strip().lower()
    except Exception as e:
        print(f"Lỗi Gemini: {e}")
        return "error-device"

def main():
    if not TARGET_DIR.exists():
        print(f"Not found: {TARGET_DIR}")
        return
        
    random_id_pattern = re.compile(r'^[0-9a-z]{20}$')
    renamed_count = 0
    
    for entry in TARGET_DIR.iterdir():
        if not entry.is_dir():
            continue
            
        if random_id_pattern.match(entry.name):
            print(f"Phân tích folder: {entry.name} ...")
            new_name = get_kebab_name(entry)
            print(f"  -> Đề xuất: {new_name}")
            
            if new_name not in ("unknown-device", "empty-folder", "error-device"):
                # Check exist
                new_path = TARGET_DIR / new_name
                # If target exists, maybe we merge or append counter
                if new_path.exists():
                    new_path = TARGET_DIR / f"{new_name}-1"
                    
                entry.rename(new_path)
                renamed_count += 1
                
    print(f"Hoàn tất phục hồi {renamed_count} thư mục!")

if __name__ == "__main__":
    main()
