import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 데이터 불러오기
file_name = "all_models_24h_test_log.csv"
df = pd.read_csv(file_name)

# 데이터 전처리 (시간 형식 변환 및 수치화)
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df['Status_Value'] = df['Status'].map({'Success': 1, 'Fail': 0})

# 모델별 성공률 계산
# 성공률(\%) = \frac{성공 횟수}{전체 요청 횟수} \times 100
success_rate = df.groupby('Model_Name')['Status_Value'].mean() * 100
success_rate = success_rate.sort_values(ascending=False).reset_index()

# 그래프 생성 모델별 성공률 순위
plt.figure(figsize=(10, 6))
sns.barplot(data=success_rate, x='Status_Value', y='Model_Name', hue='Model_Name', palette='viridis', legend=False)
plt.xlim(0, 100) # 막대가 오른쪽에 닿도록 수정
plt.title('Gemini API Success Rate by Model (%)', fontsize=15)
plt.xlabel('Success Rate (%)', fontsize=12)
plt.ylabel('Model Name', fontsize=12)
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('api_success_rate.png')

# 그래프 생성 시간대별 히트맵
pivot_df = df.pivot_table(index='Model_Name', columns='Timestamp', values='Status_Value')
plt.figure(figsize=(12, 8))
# cmap='RdYlGn' (빨강: 실패, 노랑: 중간, 초록: 성공)
sns.heatmap(pivot_df, cmap='RdYlGn', cbar_kws={'label': '0: Fail, 1: Success'})
plt.title('API Status Timeline Heatmap', fontsize=15)
plt.xlabel('Time', fontsize=12)
plt.ylabel('Model Name', fontsize=12)
plt.tight_layout()
plt.savefig('api_timeline_heatmap.png')

# 요약 보고서
# 데이터 로드 및 전처리
df = pd.read_csv("all_models_24h_test_log.csv")
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df['Hour'] = df['Timestamp'].dt.hour
df['Success_Flag'] = df['Status'].apply(lambda x: 1 if x == 'Success' else 0)

# 시각화 설정
plt.style.use('seaborn-v0_8-whitegrid')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))
fig.suptitle('Gemini API 24H Monitoring Report', fontsize=20, fontweight='bold')

# 모델별 성공률 랭킹
success_rate = df.groupby('Model_Name')['Success_Flag'].mean().sort_values(ascending=True) * 100
colors = ['#ff9999' if x < 50 else '#66b3ff' for x in success_rate] # 성공률 낮으면 빨간색

success_rate.plot(kind='barh', ax=ax1, color=colors)
ax1.set_title('Model Success Rate (%)', fontsize=15)
ax1.set_xlabel('Success Rate (%)')
ax1.set_xlim(0, 100)

for i, v in enumerate(success_rate): # 바 숫자 표시 추가
    ax1.text(v + 1, i, f"{v:.1f}%", color='black', va='center', fontweight='bold')

# 시간대별 에러 발생 추이
error_df = df[df['Status'] == 'Fail']
error_trend = error_df.groupby('Hour').size()

sns.lineplot(x=error_trend.index, y=error_trend.values, ax=ax2, marker='o', color='#e74c3c', linewidth=2)
ax2.fill_between(error_trend.index, error_trend.values, color='#e74c3c', alpha=0.2)
ax2.set_title('Hourly Error Distribution (Peak Time Check)', fontsize=15)
ax2.set_xlabel('Hour (0-23)')
ax2.set_ylabel('Error Count')
ax2.set_xticks(range(0, 24))

plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# 이미지 저장
report_name = "api_summary_report.png"
plt.savefig(report_name, dpi=300)
