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
    df['Model_Name'] = df['Model_Name'].str.replace('models/', '', regex=False) # 모델 이름에서 models/ 제거

    # 공통 스타일 설정
    plt.style.use('seaborn-v0_8-whitegrid')

    # 모델별 성공률 계산
    stats = df.groupby('Model_Name')['Status_Value'].agg(['mean', 'sum', 'count']).reset_index()
    stats.columns = ['Model_Name', 'Success_Rate_Mean', 'Success_Count', 'Total_Count']
    stats['Success_Rate'] = stats['Success_Rate_Mean'] * 100
    success_rate_desc = stats.sort_values(ascending=False, by='Success_Rate')

    # 그래프 1: 모델별 성공률 차트
    # mean, sum, count를 한 번에 계산하도록 집계 로직 통합
    model_stats = df.groupby('Model_Name')['Status_Value'].agg(['mean', 'sum', 'count']).reset_index()
    model_stats.columns = ['Model_Name', 'Success_Rate_Mean', 'Success_Count', 'Total_Count']
    model_stats['Success_Rate'] = model_stats['Success_Rate_Mean'] * 100
    model_stats = model_stats.sort_values(ascending=False, by='Success_Rate')

    plt.figure(figsize=(12, 7))
    ax1 = sns.barplot(data=model_stats, x='Success_Rate', y='Model_Name', hue='Model_Name', palette='viridis', legend=False)
    
    for _, row in model_stats.iterrows():
        v, s, t = row['Success_Rate'], int(row['Success_Count']), int(row['Total_Count'])
        combined_text = f"{v:.1f}%\n{s} / {t}"
        
        # 조건에 따른 텍스트 위치 및 색상 설정
        is_inside = v >= 20
        plt.text(v - 2 if is_inside else v + 2, row['Model_Name'], combined_text, 
                 va='center', ha='right' if is_inside else 'left', 
                 fontsize=10, fontweight='bold', color='white' if is_inside else 'black',
                 multialignment='center')
    
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
    sns.heatmap(pivot_df, cmap='RdYlGn', cbar=False) # 범례 삭제
    plt.title(f'API Status Timeline Heatmap ({title_info})', fontsize=15)
    plt.xlabel('Time', fontsize=12)
    plt.ylabel('Model Name', fontsize=12)
    plt.tight_layout()
    plt.savefig(f"{save_info}_api_timeline_heatmap.png")
    plt.close()

    # 그래프 3: 시간대별 에러 분석 리포트
    hourly_stats = df.groupby('Hour')['Status_Value'].agg(['count', 'sum']).reindex(range(24), fill_value=0)
    hourly_stats['errors'] = hourly_stats['count'] - hourly_stats['sum']
    hourly_stats['error_rate'] = (hourly_stats['errors'] / hourly_stats['count'] * 100).fillna(0)

    plt.figure(figsize=(14, 7))
    sns.lineplot(x=hourly_stats.index, y=hourly_stats['errors'], marker='o', color='#e74c3c', linewidth=2)
    plt.fill_between(hourly_stats.index, hourly_stats['errors'], color='#e74c3c', alpha=0.1)

    for h, row in hourly_stats.iterrows():
        e, c, r = int(row['errors']), int(row['count']), row['error_rate']
        plt.text(h, e + 0.7, f"{r:.1f}%\n{e} / {c}", ha='center', va='bottom', 
                 fontsize=9, fontweight='bold', color='#c0392b', multialignment='center')

    plt.title(f'Hourly API Error Analysis & Volume ({title_info})', fontsize=16, fontweight='bold')
    plt.xlabel('Hour of Day (0-23)', fontsize=12)
    plt.ylabel('Error Count', fontsize=12)
    plt.xticks(range(0, 24))
    plt.xlim(0, 23) # 양 끝 빈 공간 제거
    
    # 레이블 공간 확보용 y축 상단 여백 조정
    plt.ylim(0, hourly_stats['errors'].max() * 1.3 if hourly_stats['errors'].max() > 0 else 5)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(f'{save_info}_api_error_analysis.png', dpi=300)
    plt.close()