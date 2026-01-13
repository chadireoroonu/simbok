import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="뉴스 정리봇", page_icon="🛠️")

# 제목
st.title(" 뉴스 요약기")
st.write("실시간 뉴스를 수집해서 깔끔하게 정리해 드립니다!")

# 사이드바
with st.sidebar:
    st.header("🔍 검색 설정")
    keyword = st.text_input("키워드", value="키워드")
    max_pages = st.number_input("수집 페이지 수", min_value=1, max_value=10, value=3)
    st.divider()
    st.subheader("📅 조회 기간 설정")
    # 사용자가 달력에서 날짜 범위를 선택하게 합니다.
    today = datetime.now()
    seven_days_ago = today - timedelta(days=7)
    date_range = st.date_input(
        "조회 시작일 - 종료일",
        value=(seven_days_ago, today),
        max_value=today
    )
    st.info("선택한 날짜 내의 기사만 표시됩니다. 🕒")


# 크롤링
def crawl_news(keyword, pages):
    article_list = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    for page in range(1, pages + 1):
        # 정확도순/기간 옵션 추가하자
        url = f"https://search.daum.net/search?w=news&q={keyword}&p={page}&f=sort&sort=rec"
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status() # 에러 발생 시 예외 처리
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_items = soup.find_all('li', {'data-docid': True}) or soup.select("ul.c-list-basic > li")
            
            # if not news_items:
            #     news_items = soup.select("div.item-bundle-news")

            for item in news_items:
                # 제목 추출
                title_tag = item.select_one("div.item-title strong.tit-g a") or item.select_one("a.el-title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                
                # 링크 추출
                link = title_tag['href']
                
                # 언론사 추출
                press_tag = item.select_one("span.txt_info") or item.select_one("span.el-info")
                press = press_tag.get_text(strip=True) if press_tag else "언론사"
                
                # 요약 추출
                summary_tag = item.select_one("p.conts-desc") or item.select_one("div.el-desc")
                summary = summary_tag.get_text(strip=True) if summary_tag else "요약 없음"

                # 날짜 처리
                date_text_tag = item.select_one("span.gem-subinfo span.txt_info")
                date_text = date_text_tag.get_text(strip=True) if date_text_tag else "날짜불명"
                
                date_obj = None # datetime 객체 변환 후 비교
                
                if date_text != "날짜불명":
                    now = datetime.now()
                    if re.match(r'\d{4}\.\d{2}\.\d{2}', date_text):
                        # '2024.05.20' 형식을 datetime 객체로 변환
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
                        except:
                            date_obj = None
                
                # 날짜 문자열 저장
                final_date = date_obj.strftime('%Y.%m.%d') if date_obj else "날짜불명"
                
                article_list.append({
                    "title": title, 
                    "press": press,
                    "summary": summary,
                    "link": link,
                    "date": final_date,
                    "date_obj": date_obj # 필터링용
                })
            # time.sleep(0.1) # 서버 부하 방지
        except Exception as e:
            st.error(f"페이지 {page} 수집 중 오류: {e}")
            continue
            
    return article_list

# 실행 버튼
if st.button("뉴스 수집 시작! 🚀"):
    if len(date_range) != 2:
        st.warning("시작일과 종료일을 모두 선택해 주세요! 📅")
    else:
        start_date, end_date = date_range
        # 선택한 날짜를 비교 가능하게 변환 (시간 정보 제거)
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        with st.spinner('뉴스를 긁어오는 중... 잠시만요! ☕'):
            all_data = crawl_news(keyword, max_pages)
            
            if all_data:
                # 날짜 범위 내 필터링
                filtered_data = [
                    a for a in all_data 
                    if a['date_obj'] and start_dt <= a['date_obj'] <= end_dt
                ]
                
                df = pd.DataFrame(filtered_data).drop_duplicates(subset=['title'])
                
                if not df.empty:
                    st.success(f"📅 {start_date} ~ {end_date} 사이에 총 {len(df)}개의 기사를 찾았습니다!")
                    for idx, row in df.iterrows():
                        with st.expander(f"[{row['date']}] [{row['press']}] - {row['title']}"):
                            st.write(row['summary'])
                            st.write(f"🔗 [원문 링크 바로가기]({row['link']})")
                else:
                    st.warning("해당 날짜 범위에 뉴스 기사가 없어요. 😢")
            else:
                st.error("데이터 수집 실패! 다시 시도해 주세요.")