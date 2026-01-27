import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 데이터 불러오기
file_name = "all_models_24h_test_log.csv"
df = pd.read_csv(file_name)

# 데이터 전처리 (시간 형식 변환 및 수치화)
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df['Status_Value'] = df['Status'].map({'Success': 1, 'Fail': 0})

# 모델별 성공률 계산 🧮
# $성공률(\%) = \frac{성공 횟수}{전체 요청 횟수} \times 100$
success_rate = df.groupby('Model_Name')['Status_Value'].mean() * 100
success_rate = success_rate.sort_values(ascending=False).reset_index()

# 그래프 생성 모델별 성공률 순위
plt.figure(figsize=(10, 6))
sns.barplot(data=success_rate, x='Status_Value', y='Model_Name', palette='viridis')
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
