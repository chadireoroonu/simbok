import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib

# 데이터 로드 및 통합 전처리
file_name = "72h_test_log_20260129.csv"
if not os.path.exists(file_name):
    print(f"❌ 에러: '{file_name}' 파일이 없습니다.")
else:
    # 파일명 정보 추출
    name_parts = file_name.replace('.csv', '').split('_')
    title_info = f"{name_parts[0]} {name_parts[-1]}"
    save_info = f"{name_parts[0]}_{name_parts[-1]}"

    df = pd.read_csv(file_name)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Clean_Timestamp'] = df['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S') # 나노초 삭제
    df['Status_Value'] = df['Status'].map({'Success': 1, 'Fail': 0})
    df['Hour'] = df['Timestamp'].dt.hour

    # 모델 이름에서 models/ 제거
    df['Model_Name'] = df['Model_Name'].str.replace('models/', '', regex=False)

    # 모델별 성공률 계산
    # success_rate_desc = df.groupby('Model_Name')['Status_Value'].mean().sort_values(ascending=False).reset_index()
    # success_rate_desc['Success_Rate'] = success_rate_desc['Status_Value'] * 100

    stats = df.groupby('Model_Name')['Status_Value'].agg(['mean', 'sum', 'count']).reset_index()
    stats.columns = ['Model_Name', 'Success_Rate_Mean', 'Success_Count', 'Total_Count']
    stats['Success_Rate'] = stats['Success_Rate_Mean'] * 100
    success_rate_desc = stats.sort_values(ascending=False, by='Success_Rate')

    # 그래프 1: 모델별 성공률 순위
    plt.figure(figsize=(12, 7))
    ax = sns.barplot(data=success_rate_desc, x='Success_Rate', y='Model_Name', 
                    hue='Model_Name', palette='viridis', legend=False)
    
    for _, row in success_rate_desc.iterrows():
        model_name = row['Model_Name']
        v = row['Success_Rate']
        success_count = int(row['Success_Count'])
        total_count = int(row['Total_Count'])
        combined_text = f"{v:.1f}%\n{success_count} / {total_count}"
        
        if v >= 20: # 성공률 20% 이상
            x_pos = v - 2
            ha = 'right'
            color = 'white'
        else: # 성공률 20% 미만
            x_pos = v + 2
            ha = 'left'
            color = 'black'
            
        ax.text(x_pos, model_name, combined_text, 
                va='center', ha=ha, fontsize=10, fontweight='bold', color=color)
    
    plt.xlim(0, 100)
    plt.title(f'Gemini API Success Rate by Model ({title_info})', fontsize=15)
    plt.xlabel('Success Rate (%)', fontsize=12)
    plt.ylabel('Model Name', fontsize=12)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(f'{save_info}_api_success_rate.png')
    plt.close()

    # 그래프 2: 시간대별 히트맵
    pivot_df = df.pivot_table(index='Model_Name', columns='Clean_Timestamp', values='Status_Value')
    plt.figure(figsize=(12, 8))
    # sns.heatmap(pivot_df, cmap='RdYlGn', cbar_kws={'label': '0: Fail, 1: Success'})
    sns.heatmap(pivot_df, cmap='RdYlGn', cbar=False) # 범례 삭제
    plt.title(f'API Status Timeline Heatmap ({title_info})', fontsize=15)
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('Model Name', fontsize=12)
    plt.tight_layout()
    plt.savefig(f"{save_info}_api_timeline_heatmap.png")
    plt.close()

    # 그래프 3: 요약 보고서
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 14))
    fig.suptitle(f'Gemini API 24H Monitoring Report ({title_info})', fontsize=20)

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
    plt.savefig(f'{save_info}_api_summary_report.png', dpi=300)
    plt.close()