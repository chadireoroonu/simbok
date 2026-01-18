import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
import re
import google.generativeai as genai

st.set_page_config(page_title="뉴스 정리봇", page_icon="🛠️")

# AI 가공 함수
def generate_narration(api_key, text):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash-8b')
        
        # 향후 프롬프트 수정하기
        prompt = f"""
        당신은 실시간 뉴스를 아주 재미있고 귀에 쏙쏙 들어오게 전달하는 전문 뉴스 나레이터입니다.
        아래 뉴스 본문의 내용을 바탕으로, 시청자에게 직접 이야기하는 듯한 구어체 스타일로 정리해 주세요.
        너무 길지 않게 핵심만 짚어서 3문장 정도로 가공해 주세요.
        
        뉴스 본문:
        {text}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 가공 중 에러 발생: {e}"

# UI
st.title("뉴스 요약기")
st.write("실시간 뉴스를 수집해서 AI가 깔끔하게 정리해 드립니다!")

# 사이드바
with st.sidebar:
    st.header("🔍 검색 설정")
    keyword = st.text_input("키워드", value="키워드")
    max_pages = st.number_input("수집 페이지 수", min_value=1, max_value=20, value=5)
    
    st.divider()
    st.subheader("🔑 AI 설정")
    google_api_key = st.text_input("Google API Key", type="password", placeholder="API 키를 입력하세요 🗝️")
    st.caption("발급처: [Google AI Studio](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    st.subheader("📅 조회 기간 설정")
    today = datetime.now()
    seven_days_ago = today - timedelta(days=7)
    date_range = st.date_input("조회 시작일 - 종료일", value=(seven_days_ago, today), max_value=today)

# 뉴스 크롤링
def crawl_news(keyword, pages):
    article_list = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    
    for page in range(1, pages + 1):
        url = f"https://search.daum.net/search?w=news&q={keyword}&p={page}&f=sort&sort=rec"
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            news_items = soup.find_all('li', {'data-docid': True}) or soup.select("ul.c-list-basic > li")

            for item in news_items:
                title_tag = item.select_one("div.item-title strong.tit-g a") or item.select_one("a.el-title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                link = title_tag['href'] if title_tag else ""
                press_tag = item.select_one("span.txt_info") or item.select_one("span.el-info")
                press = press_tag.get_text(strip=True) if press_tag else "언론사"
                summary_tag = item.select_one("p.conts-desc") or item.select_one("div.el-desc")
                summary = summary_tag.get_text(strip=True) if summary_tag else "요약 없음"
                date_text_tag = item.select_one("span.gem-subinfo span.txt_info")
                date_text = date_text_tag.get_text(strip=True) if date_text_tag else "날짜불명"
                
                date_obj = None
                if date_text != "날짜불명":
                    now = datetime.now()
                    if re.match(r'\d{4}\.\d{2}\.\d{2}', date_text):
                        date_obj = datetime.strptime(date_text[:10], '%Y.%m.%d')
                    else:
                        try:
                            if "분전" in date_text:
                                minutes = int(re.search(r'(\d+)', date_text).group(1))
                                date_obj = now - timedelta(minutes=minutes)
                            elif "시간전" in date_text:
                                hours = int(re.search(r'(\d+)', date_text).group(1))
                                date_obj = now - timedelta(hours=hours)
                            elif "어제" in date_text:
                                date_obj = now - timedelta(days=1)
                        except: date_obj = None
                
                final_date = date_obj.strftime('%Y.%m.%d') if date_obj else "날짜불명"
                article_list.append({"title": title, "press": press, "summary": summary, "link": link, "date": final_date, "date_obj": date_obj})
        except Exception as e:
            st.error(f"페이지 {page} 수집 중 오류: {e}")
            continue
    return article_list

def get_full_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        content_area = soup.select_one('section[dmcf-sid]') or soup.select_one('.article_view') or soup.select_one('#harmonyContainer') or soup.select_one('article')
        if content_area:
            paragraphs = content_area.find_all(['p', 'br'])
            text_lines = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
            return "\n\n".join(text_lines)
        return "본문 영역찾기에 실패했어요 🔗"
    except Exception as e:
        return f"본문 불러오기 중 에러 발생: {e}"

# --- 메인 로직 ---
if 'filtered_df' not in st.session_state:
    st.session_state['filtered_df'] = None
if 'expanded_idx' not in st.session_state:
    st.session_state['expanded_idx'] = None

if st.button("뉴스 수집 시작! 🚀"):
    if len(date_range) != 2:
        st.warning("시작일과 종료일을 선택해 주세요!")
    else:
        start_date, end_date = date_range
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        with st.spinner('뉴스를 긁어오는 중...'):
            all_data = crawl_news(keyword, max_pages)
            if all_data:
                filtered_data = [a for a in all_data if a['date_obj'] and start_dt <= a['date_obj'] <= end_dt]
                if filtered_data:
                    st.session_state['filtered_df'] = pd.DataFrame(filtered_data).drop_duplicates(subset=['title'])
                else:
                    st.warning("해당 범위에 뉴스가 없어요 😢")
            else:
                st.error("데이터 수집 실패!")

# --- 결과 출력 로직 ---
if st.session_state['filtered_df'] is not None:
    df = st.session_state['filtered_df']
    st.success(f"총 {len(df)}개의 고유 기사를 찾았습니다! 🎉")
    
    for idx, row in df.iterrows():
        is_expanded = (st.session_state['expanded_idx'] == idx)
        
        with st.expander(f"[{row['date']}] [{row['press']}] - {row['title']}", expanded=is_expanded):
            st.write(row['summary'])
            st.write(f"🔗 [원문 링크 바로가기]({row['link']})")
               
            # 버튼 1: 본문 긁어오기
            if st.button("상세 내용 전체 보기 📖", key=f"btn_{idx}"):
                st.session_state['expanded_idx'] = idx
                with st.spinner('본문을 가져오는 중...'):
                    st.session_state[f'content_{idx}'] = get_full_content(row['link'])
                st.rerun()

            # 본문 내용 표시
            if f'content_{idx}' in st.session_state and is_expanded:
                st.markdown("---")
                st.info(st.session_state[f'content_{idx}'])
                
                # 버튼 2: AI 나레이션 가공
                st.subheader("🎙️ AI 나레이션 가공")
                if st.button("AI 나레이션 생성 시작! ✨", key=f"ai_{idx}"):
                    if not google_api_key:
                        st.warning("사이드바에 API 키를 넣어주세요! 🔑")
                    else:
                        with st.spinner('Gemini AI가 가공하는 중...'):
                            narration = generate_narration(google_api_key, st.session_state[f'content_{idx}'])
                            st.session_state[f'narration_{idx}'] = narration
                        st.rerun()

                # AI 결과 표시
                if f'narration_{idx}' in st.session_state:
                    st.write(st.session_state[f'narration_{idx}'])