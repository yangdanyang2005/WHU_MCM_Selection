import os
import pandas as pd
import numpy as np
import csv
import warnings
warnings.filterwarnings('ignore')

# 创建输出文件夹（如果不存在）
output_folder = '2.1_best_attractions'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 读取data文件夹下的所有csv文件
data_folder = 'data'
city_files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]

for city_file in city_files:
    try:
        # 读取城市CSV文件
        city_name = city_file.split('.')[0]
        file_path = os.path.join(data_folder, city_file)
        
        # 使用pandas读取CSV文件，指定编码为utf-8
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 将评分列转换为数值类型，非数值记为NaN
        df['评分'] = pd.to_numeric(df['评分'], errors='coerce')
        
        # 找出该城市的最高评分
        max_score = df['评分'].max()
        
        # 筛选出评分等于最高评分的景点
        best_attractions = df[df['评分'] == max_score]
        
        # 保存到输出文件夹中的同名CSV文件
        output_path = os.path.join(output_folder, city_file)
        best_attractions.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"已处理 {city_name}，最高评分: {max_score}，共有 {len(best_attractions)} 个最高评分景点")
    
    except Exception as e:
        print(f"处理 {city_file} 时出错: {str(e)}")

print("所有城市处理完成！")
