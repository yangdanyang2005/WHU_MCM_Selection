import os
import pandas as pd
import glob
import re

def extract_hours(time_str):
    """Extract hours from the suggested visiting time string"""
    if pd.isna(time_str):
        return 24  # Default to 24 hours if no time is specified
    
    time_str = str(time_str).lower()
    
    # Handle different time formats
    if '小时' in time_str:
        # Extract numeric values
        numbers = re.findall(r'\d+\.?\d*', time_str)
        if numbers:
            if '-' in time_str:  # Range like "0.5小时 - 1小时"
                return (float(numbers[0]) + float(numbers[1])) / 2
            else:  # Single value like "2小时"
                return float(numbers[0])
    
    elif '天' in time_str:
        numbers = re.findall(r'\d+\.?\d*', time_str)
        if numbers:
            if '-' in time_str:  # Range like "1天 - 3天"
                return (float(numbers[0]) + float(numbers[1])) / 2 * 24
            else:  # Single value like "3天"
                return float(numbers[0]) * 24
    
    return 24  # Default value if parsing fails

def get_best_attractions():
    """Read all CSV files in the best_attractions folder and process them"""
    csv_files = glob.glob('2.1_best_attractions/*.csv')
    city_best_attractions = []
    
    for file_path in csv_files:
        city_name = os.path.basename(file_path).replace('.csv', '')
        
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                continue
            
            # Calculate the number of best attractions for this city
            best_attractions_count = len(df)
            
            # Get the first attraction (we'll process all and calculate a weighted score)
            attraction_info = df.iloc[0].to_dict()
            
            # Extract and process suggested visiting time
            suggested_time = extract_hours(attraction_info.get('建议游玩时间', 24))
            
            # Normalize the visiting time score (shorter time is better)
            time_score = 1 / (1 + suggested_time)  # Add 1 to avoid division by zero
            
            # Calculate a weighted score (rating 60%, count 30%, time 10%)
            rating = float(attraction_info.get('评分', 0))
            weighted_score = 0.6 * rating + 0.3 * best_attractions_count + 0.1 * time_score * 10
            
            # Add additional information
            attraction_info['城市'] = city_name
            attraction_info['最佳景点数量'] = best_attractions_count
            attraction_info['建议游玩小时数'] = suggested_time
            attraction_info['加权评分'] = weighted_score
            
            # Ensure rating is float
            attraction_info['评分'] = float(attraction_info.get('评分', 0))
            
            city_best_attractions.append(attraction_info)
            
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
    
    return city_best_attractions

def main():
    # Get all city attractions with processed information
    city_attractions = get_best_attractions()
    
    # Create DataFrame
    df = pd.DataFrame(city_attractions)
    
    # Sort by weighted score (descending), then by rating (descending), then by count (descending)
    df_sorted = df.sort_values(
        by=['加权评分', '评分', '最佳景点数量'], 
        ascending=[False, False, False]
    )
    
    # Select top 50 cities
    top_50_cities = df_sorted.head(50)
    
    # Output results
    print("最令外国游客向往的50个城市：")
    for i, (index, row) in enumerate(top_50_cities.iterrows(), 1):
        print(f"{i}. {row['城市']} - 最佳景点: {row['名字']}, 评分: {row['评分']:.1f}, "
              f"最佳景点数量: {row['最佳景点数量']}, 建议游玩小时数: {row['建议游玩小时数']:.1f}")
    
    # Save results
    top_50_cities.to_csv('2.2_top_50_cities_for_foreign_tourists.csv', index=False)
    print("结果已保存到 2.2_top_50_cities_for_foreign_tourists.csv")

if __name__ == "__main__":
    main()