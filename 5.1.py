import os
import pandas as pd
import numpy as np

# 创建输出文件夹（如果不存在）
output_folder = "5.1_filtered_mountain_data"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 获取data文件夹下的所有csv文件
data_folder = "data"
csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]

# 处理每个城市的csv文件
for csv_file in csv_files:
    file_path = os.path.join(data_folder, csv_file)
    
    try:
        # 读取CSV文件
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        # 如果UTF-8解码失败，尝试其他编码
        try:
            df = pd.read_csv(file_path, encoding='gbk')
        except:
            df = pd.read_csv(file_path, encoding='gb18030', errors='replace')
    
    # 筛选名字中含有"山"的行
    mountain_df = df[df['名字'].str.contains('山', na=False)]
    
    if not mountain_df.empty:
        # 将评分列转换为数值类型
        mountain_df['评分'] = pd.to_numeric(mountain_df['评分'], errors='coerce')
        
        # 找出最高评分
        max_score = mountain_df['评分'].max()
        
        # 筛选出评分最高的行
        best_mountain_df = mountain_df[mountain_df['评分'] == max_score]
        
        # 将结果写入输出文件夹，保持原文件名
        output_path = os.path.join(output_folder, csv_file)
        best_mountain_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"已处理 {csv_file}，找到 {len(best_mountain_df)} 条含'山'且评分最高的记录")
    else:
        print(f"{csv_file} 中没有名字含'山'的记录")

print("处理完成！")
