import os
import pandas as pd
import numpy as np
from collections import Counter

# 设置数据文件夹路径
data_folder = 'data'

# 存储所有城市的景点评分数据
all_scores = []
# 存储每个城市拥有最高分景点的数量
city_bs_count = {}

# 遍历所有城市文件
for city_file in os.listdir(data_folder):
    if city_file.endswith('.csv'):
        city_name = city_file[:-4]  # 去掉.csv后缀得到城市名
        file_path = os.path.join(data_folder, city_file)
        
        try:
            # 读取CSV文件，指定编码为utf-8
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 提取评分列，处理非数字值
            scores = []
            for score in df['评分']:
                try:
                    if score and score != '--':  # 检查是否为空或'--'
                        scores.append(float(score))
                except:
                    # 忽略无法转换为浮点数的值
                    pass
            
            # 添加到所有评分列表
            all_scores.extend(scores)
            
            # 记录城市信息，用于后续统计
            city_bs_count[city_name] = 0
            
        except Exception as e:
            print(f"处理文件 {city_file} 时出错: {e}")

# 计算最高评分(BS)
best_score = max(all_scores) if all_scores else 0
print(f"问题1-1: 最高评分(BS)是: {best_score}")

# 统计获得最高评分的景点数量
bs_count = all_scores.count(best_score)
print(f"问题1-2: 全国有 {bs_count} 个景点获评最高评分(BS)")

# 重新遍历所有城市文件，统计每个城市拥有最高评分景点的数量
for city_file in os.listdir(data_folder):
    if city_file.endswith('.csv'):
        city_name = city_file[:-4]
        file_path = os.path.join(data_folder, city_file)
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 统计该城市拥有最高评分的景点数量
            bs_count_city = 0
            for score in df['评分']:
                try:
                    if score and score != '--' and float(score) == best_score:
                        bs_count_city += 1
                except:
                    pass
            
            city_bs_count[city_name] = bs_count_city
            
        except Exception as e:
            print(f"处理文件 {city_file} 时出错: {e}")

# 按照拥有最高评分景点数量排序城市
sorted_cities = sorted(city_bs_count.items(), key=lambda x: x[1], reverse=True)

# 获得拥有最高评分景点最多的城市（可能有多个并列）
max_bs_count = sorted_cities[0][1]
top_cities = [city for city, count in sorted_cities if count == max_bs_count]

print(f"问题1-3: 获评最高评分(BS)景点最多的城市是: {', '.join(top_cities)}, 各有 {max_bs_count} 个最高评分景点")

# 列出前10个拥有最高评分景点数量最多的城市
print("问题1-4: 依据拥有最高评分景点数量排序，前10个城市是:")
for i, (city, count) in enumerate(sorted_cities[:10], 1):
    print(f"{i}. {city}: {count}个最高评分景点")

# 将结果输出到文件
with open('1_res.txt', 'w', encoding='utf-8') as f:
    f.write(f"问题1-1: 最高评分(BS)是: {best_score}\n")
    f.write(f"问题1-2: 全国有 {bs_count} 个景点获评最高评分(BS)\n")
    f.write(f"问题1-3: 获评最高评分(BS)景点最多的城市是: {', '.join(top_cities)}, 各有 {max_bs_count} 个最高评分景点\n")
    f.write("问题1-4: 依据拥有最高评分景点数量排序，前10个城市是:\n")
    for i, (city, count) in enumerate(sorted_cities[:10], 1):
        f.write(f"{i}. {city}: {count}个最高评分景点\n")
