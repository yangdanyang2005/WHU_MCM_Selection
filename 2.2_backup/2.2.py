import os
import pandas as pd
import glob

# 读取best_attractions文件夹下的所有csv文件
def get_best_attractions():
    # 获取所有csv文件路径
    csv_files = glob.glob('2.1_best_attractions/*.csv')
    
    # 存储每个城市的最佳景点信息
    city_best_attractions = []
    
    for file_path in csv_files:
        # 提取城市名（从文件名）
        city_name = os.path.basename(file_path).replace('.csv', '')
        
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 如果文件为空或没有数据，跳过
            if df.empty:
                continue
            
            # 计算该城市最佳景点的数量
            best_attractions_count = len(df)
                
            # 获取景点信息
            attraction_info = df.iloc[0].to_dict()  # 取第一个景点（如果有多个评分相同的，取第一个）
            
            # 添加城市名
            attraction_info['城市'] = city_name
            
            # 添加该城市最佳景点的数量
            attraction_info['最佳景点数量'] = best_attractions_count
            
            # 将评分转换为数值类型
            if '评分' in attraction_info:
                try:
                    attraction_info['评分'] = float(attraction_info['评分'])
                except (ValueError, TypeError):
                    # 如果评分无法转换为浮点数，设为0
                    attraction_info['评分'] = 0.0
            else:
                attraction_info['评分'] = 0.0
                
            city_best_attractions.append(attraction_info)
            
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
    
    return city_best_attractions

# 主函数
def main():
    # 获取所有城市的最佳景点
    city_attractions = get_best_attractions()
    
    # 创建DataFrame
    df = pd.DataFrame(city_attractions)
    
    # 先按评分降序排序，然后按最佳景点数量降序排序
    df_sorted = df.sort_values(by=['评分', '最佳景点数量'], ascending=[False, False])
    
    # 选择前50个城市
    top_50_cities = df_sorted.head(50)
    
    # 输出结果
    print(f"最令外国游客向往的50个城市：")
    for i, (index, row) in enumerate(top_50_cities.iterrows(), 1):
        print(f"{i}. {row['城市']} - 最佳景点: {row['名字']}, 评分: {row['评分']}, 最佳景点数量: {row['最佳景点数量']}")
    
    # 将结果保存到CSV文件
    top_50_cities.to_csv('2.2_top_50_cities_for_foreign_tourists.csv', index=False)
    print("结果已保存到 2.2_top_50_cities_for_foreign_tourists.csv")

if __name__ == "__main__":
    main()
