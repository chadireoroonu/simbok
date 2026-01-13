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
    keyword = st.text_input("키워드", value="삼성라이온즈")
    max_pages = st.number_input("수집 페이지 수", min_value=1, max_value=10, value=3)
    st.divider()
    st.info("Gemini API 키를 넣으면 요약 기능을 쓸 수 있어요! (업데이트 예정)")

# 크롤링
def crawl_news(keyword, pages):
    article_list = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    for page in range(1, pages + 1):
        # 정확도순/기간 옵션 추가하자
        url = f"https://search.daum.net/search?w=news&q={keyword}&p={page}"
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status() # 에러 발생 시 예외 처리
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_items = soup.find_all('li', {'data-docid': True}) or soup.select("ul.c-list-basic > li")
            
            if not news_items:
                news_items = soup.select("div.item-bundle-news")

            for item in news_items:
                # 제목 추출
                title_tag = item.select_one("div.item-title strong.tit-g a") or item.select_one("a.el-title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                
                # 언론사 추출
                press_tag = item.select_one("span.txt_info") or item.select_one("span.el-info")
                press = press_tag.get_text(strip=True) if press_tag else "언론사"
                
                # 요약 추출
                summary_tag = item.select_one("p.conts-desc") or item.select_one("div.el-desc")
                summary = summary_tag.get_text(strip=True) if summary_tag else "요약 없음"
                
                if title: # 제목이 있는 것만 저장
                    article_list.append({"title": title, "press": press, "summary": summary})
            
            time.sleep(0.5) # 서버 부하 방지
        except Exception as e:
            st.error(f"페이지 {page} 수집 중 오류: {e}")
            continue
            
    return article_list

# 실행 버튼
if st.button("뉴스 수집 시작! 🚀"):
    with st.spinner('뉴스를 긁어오는 중... 잠시만요! ☕'):
        data = crawl_news(keyword, max_pages)
        
        if data:
            df = pd.DataFrame(data)
            # 제목 기준 중복 제거
            df = df.drop_duplicates(subset=['title'])
            st.success(f"총 {len(df)}개의 고유 뉴스를 찾았습니다! 🎉")
            
            # 결과 출력
            for idx, row in df.iterrows():
                with st.expander(f"[{row['press']}] {row['title']}"):
                    st.write(row['summary'])
        else:
            st.error("데이터를 가져오지 못했어요. 😢")