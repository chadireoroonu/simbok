import os
import csv
import time
from datetime import datetime, timedelta
from google import genai
from dotenv import load_dotenv

# 1. 환경 설정 및 API 키 로드
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# 테스트할 모델 리스트
MODELS_TO_TEST = [
    "models/gemini-2.5-flash", "models/gemini-2.5-pro", "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite", "models/gemini-3-pro-preview", "models/gemini-3-flash-preview",
    "models/embedding-001", "models/text-embedding-004", "models/aqa",
    "models/imagen-4.0-generate-001", "models/veo-3.0-generate-001"
]

def run_all_api_tests():
    log_file = "all_models_24h_test_log.csv"
    client = genai.Client(api_key=API_KEY)
    
    # 종료 시간 설정
    end_time = datetime.now() + timedelta(hours=24)
    
    # CSV 헤더 작성
    if not os.path.exists(log_file):
        with open(log_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Model_Name", "Status", "Error_Detail"])

    print(f"🚀 API 모니터링 시작! (종료 예정: {end_time.strftime('%Y-%m-%d %H:%M:%S')})")

    # 24시간 테스트 시작 🔄
    while datetime.now() < end_time:
        current_round_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n📢 [{current_round_time}] 테스트 라운드 시작!")

        for model_name in MODELS_TO_TEST:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "Fail"
            error_detail = ""
            
            try:
                # 1. 텍스트 생성 모델 테스트
                if any(x in model_name for x in ["flash", "pro", "exp"]):
                    response = client.models.generate_content(
                        model=model_name,
                        contents="Hi"
                    )
                    if response: status = "Success"

                # 2. 임베딩 모델 테스트
                elif "embedding" in model_name:
                    response = client.models.embed_content(
                        model=model_name,
                        contents="Test"
                    )
                    if response: status = "Success"

                # 3. 기타 모델
                else:
                    info = client.models.get(model=model_name)
                    if info: status = "Success"

                print(f"   - {model_name}: ✅ {status}")

            except Exception as e:
                status = "Fail"
                error_detail = str(e)
                print(f"   - {model_name}: ❌ {status}")

            # 실시간 파일 기록
            with open(log_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, model_name, status, error_detail])

        time.sleep(600) # 10분(600초) 대기 ⏳

    print(f"✨ 24시간 테스트 완료")

if __name__ == "__main__":
    run_all_api_tests()