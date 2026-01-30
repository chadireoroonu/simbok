import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib

# 데이터 로드 및 통합 전처리
file_name = "all_models_24h_test_log"
if not os.path.exists(file_name):
    print(f"❌ 에러: '{file_name}' 파일이 없습니다.")
else:
    df = pd.read_csv(file_name)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Status_Value'] = df['Status'].map({'Success': 1, 'Fail': 0})
    df['Hour'] = df['Timestamp'].dt.hour

    # 모델별 성공률 계산
    success_rate_desc = df.groupby('Model_Name')['Status_Value'].mean().sort_values(ascending=False).reset_index()
    success_rate_desc['Success_Rate'] = success_rate_desc['Status_Value'] * 100

    # 그래프 1: 모델별 성공률 순위
    plt.figure(figsize=(10, 6))
    sns.barplot(data=success_rate_desc, x='Success_Rate', y='Model_Name', hue='Model_Name', palette='viridis', legend=False)
    plt.xlim(0, 100)
    plt.title('Gemini API Success Rate by Model (%)', fontsize=15)
    plt.xlabel('Success Rate (%)', fontsize=12)
    plt.ylabel('Model Name', fontsize=12)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('api_success_rate.png')
    plt.close()

    # 그래프 2: 시간대별 히트맵
    pivot_df = df.pivot_table(index='Model_Name', columns='Timestamp', values='Status_Value')
    plt.figure(figsize=(12, 8))
    sns.heatmap(pivot_df, cmap='RdYlGn', cbar_kws={'label': '0: Fail, 1: Success'})
    plt.title('API Status Timeline Heatmap', fontsize=15)
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('Model Name', fontsize=12)
    plt.tight_layout()
    plt.savefig('api_timeline_heatmap.png')
    plt.close()

    # 그래프 3: 요약 보고서
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 14))
    fig.suptitle('Gemini API 24H Monitoring Report', fontsize=20, fontweight='bold')

    success_rate_asc = df.groupby('Model_Name')['Status_Value'].mean().sort_values(ascending=True) * 100
    colors = ['#ff9999' if x < 50 else '#66b3ff' for x in success_rate_asc]
    success_rate_asc.plot(kind='barh', ax=ax1, color=colors)
    ax1.set_title('Model Success Rate (%)', fontsize=15)
    ax1.set_xlim(0, 100)
    for i, v in enumerate(success_rate_asc):
        ax1.text(v + 1, i, f"{v:.1f}%", color='black', va='center', fontweight='bold')

    error_trend = df[df['Status'] == 'Fail'].groupby('Hour').size().reindex(range(24), fill_value=0)
    sns.lineplot(x=error_trend.index, y=error_trend.values, ax=ax2, marker='o', color='#e74c3c', linewidth=2)
    ax2.fill_between(error_trend.index, error_trend.values, color='#e74c3c', alpha=0.2)
    ax2.set_title('Hourly Error Distribution', fontsize=15)
    ax2.set_xlabel('Hour (0-23)')
    ax2.set_ylabel('Error Count')
    ax2.set_xticks(range(0, 24))

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('api_summary_report.png', dpi=300)
    plt.close()