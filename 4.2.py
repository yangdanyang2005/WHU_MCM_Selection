import pandas as pd
import numpy as np
import geopandas as gpd
from math import radians, cos, sin, asin, sqrt
import networkx as nx
import matplotlib.pyplot as plt
import os
import glob
import webbrowser

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# 1. 加载数据
def load_data():
    # 加载山景数据 - 从4.1_filtered_mountain_data文件夹读取所有CSV文件
    mountain_data_folder = "4.1_filtered_mountain_data"
    mountain_files = glob.glob(os.path.join(mountain_data_folder, "*.csv"))
    
    # 创建一个空的DataFrame来存储所有山景数据
    all_mountains = pd.DataFrame()
    
    # 读取每个文件并合并数据
    for file in mountain_files:
        city_name = os.path.basename(file).replace(".csv", "")
        try:
            df = pd.read_csv(file)
            # 添加城市名列
            df['城市'] = city_name
            all_mountains = pd.concat([all_mountains, df])
        except Exception as e:
            print(f"读取文件 {file} 时出错: {e}")
    
    # 加载城市地理位置数据
    city_locations = gpd.read_file('3_地级城市驻地.geojson')
    
    # 加载省级行政区数据
    provinces = gpd.read_file('3_省级行政区.geojson')
    
    return all_mountains, city_locations, provinces

# 2. 计算两个城市之间的距离
def calculate_distance(x1, y1, x2, y2):
    """
    使用Haversine公式计算两个坐标点之间的距离（单位：公里）
    """
    # 将经纬度转换为弧度
    lon1, lat1, lon2, lat2 = map(radians, [x1, y1, x2, y2])
    
    # Haversine公式
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # 地球平均半径，单位为公里
    
    return c * r

# 3. 估算高铁交通时间和费用
def estimate_travel_time_and_cost(distance):
    """
    根据距离估算高铁交通时间（小时）和费用（元）
    """
    # 假设高铁平均速度为250km/h 
    travel_time = distance / 250
    
    # 高铁票价估算公式: 基础票价 + 每公里费率 
    base_fare = 20
    rate_per_km = 0.45
    travel_cost = base_fare + distance * rate_per_km
    
    return travel_time, travel_cost

# 4. 估算每个城市山景的游览时间
def estimate_visit_time(mountain_score):
    """
    根据山的评分估算游览时间（小时）
    """
    # 评分越高，游览时间越长
    if mountain_score >= 4.5:
        return 8  # 一整天
    elif mountain_score >= 4.0:
        return 6  # 大半天
    elif mountain_score >= 3.5:
        return 4  # 半天
    else:
        return 3  # 小半天

# 5. 估算门票价格
def estimate_ticket_price(mountain_score):
    """
    根据山的评分估算门票价格（元）
    """
    # 评分越高，门票越贵
    if mountain_score >= 4.5:
        return 150
    elif mountain_score >= 4.0:
        return 120
    elif mountain_score >= 3.5:
        return 100
    else:
        return 80

# 6. 规划最佳旅游路线
def plan_optimal_route(mountain_data, city_locations, start_city=None, max_hours=144):
    """
    规划最佳旅游路线
    """
    # 筛选有山的城市
    cities_with_mountains = mountain_data['城市'].unique()
    
    # 筛选出在地理位置数据中的城市
    valid_cities = []
    for city in cities_with_mountains:
        if city in city_locations['name'].values:
            valid_cities.append(city)
    
    # 如果没有指定起始城市，选择一个有国际机场且有山的城市作为起点
    major_airports = ["北京", "上海", "广州", "成都", "昆明", "西安", "重庆", "杭州", "南京", "厦门", "武汉"]
    if start_city is None:
        for city in major_airports:
            if city in valid_cities:
                start_city = city
                break
        
        # 如果主要机场城市都没有山，则选择第一个有山的城市
        if start_city is None and valid_cities:
            start_city = valid_cities[0]
    
    if start_city is None:
        raise ValueError("无法确定起始城市")
    
    if start_city not in valid_cities:
        print(f"警告: 起始城市 {start_city} 没有山景数据")
        if valid_cities:
            start_city = valid_cities[0]
            print(f"已自动选择 {start_city} 作为起始城市")
        else:
            raise ValueError("没有有效的城市数据")
    
    # 创建城市图
    G = nx.Graph()
    
    # 添加节点（所有有山的城市）
    for city in valid_cities:
        # 获取城市的地理位置
        city_geo = city_locations[city_locations['name'] == city]
        if city_geo.empty:
            continue
        
        # 获取该城市最高评分的山
        city_mountains = mountain_data[mountain_data['城市'] == city]
        if city_mountains.empty:
            continue
        
        # 确保评分列是数值类型
        city_mountains['评分'] = pd.to_numeric(city_mountains['评分'], errors='coerce')
        
        # 获取最高评分
        max_score = city_mountains['评分'].max()
        best_mountain = city_mountains[city_mountains['评分'] == max_score].iloc[0]
        
        # 估算游览时间和门票价格
        visit_time = estimate_visit_time(max_score)
        ticket_price = estimate_ticket_price(max_score)
        
        # 添加节点
        G.add_node(city, 
                  x=city_geo.iloc[0].geometry.x, 
                  y=city_geo.iloc[0].geometry.y,
                  mountain_name=best_mountain['名字'],
                  mountain_score=max_score,
                  visit_time=visit_time,
                  ticket_price=ticket_price)
    
    # 添加边（城市之间的连接）
    for i, city1 in enumerate(valid_cities):
        if city1 not in G.nodes:
            continue
        for j in range(i+1, len(valid_cities)):
            city2 = valid_cities[j]
            if city2 not in G.nodes:
                continue
            
            # 计算距离
            x1, y1 = G.nodes[city1]['x'], G.nodes[city1]['y']
            x2, y2 = G.nodes[city2]['x'], G.nodes[city2]['y']
            distance = calculate_distance(x1, y1, x2, y2)
            
            # 估算交通时间和费用
            travel_time, travel_cost = estimate_travel_time_and_cost(distance)
            
            # 添加边
            G.add_edge(city1, city2, distance=distance, travel_time=travel_time, travel_cost=travel_cost)
    
    # 寻找最佳路线
    # 使用贪婪算法: 从起始城市开始，每次选择能够最大化体验/费用比的下一个城市
    current_city = start_city
    route = [current_city]
    total_time = G.nodes[current_city]['visit_time']  # 初始城市游览时间
    total_travel_cost = 0  # 交通费用
    total_ticket_cost = G.nodes[current_city]['ticket_price']  # 门票费用
    
    # 已访问城市集合
    visited = {current_city}
    
    while total_time < max_hours:
        best_next_city = None
        best_score = -1
        
        # 遍历所有相邻城市
        for neighbor in valid_cities:
            if neighbor in visited or neighbor not in G.nodes:
                continue
                
            # 计算到达该城市的交通时间和费用
            if not G.has_edge(current_city, neighbor):
                continue
                
            travel_time = G[current_city][neighbor]['travel_time']
            travel_cost = G[current_city][neighbor]['travel_cost']
            
            # 游览该城市所需时间
            visit_time = G.nodes[neighbor]['visit_time']
            
            # 检查是否超出总时间限制
            if total_time + travel_time + visit_time > max_hours:
                continue
                
            # 计算性价比得分 (评分/总费用)
            mountain_score = G.nodes[neighbor]['mountain_score']
            ticket_price = G.nodes[neighbor]['ticket_price']
            
            # 优先选择性价比高的城市
            cost_efficiency = mountain_score / (travel_cost + ticket_price)
            
            if cost_efficiency > best_score:
                best_score = cost_efficiency
                best_next_city = neighbor
        
        # 如果没有找到下一个城市，结束路线规划
        if best_next_city is None:
            break
            
        # 更新路线和总时间、费用
        route.append(best_next_city)
        visited.add(best_next_city)
        
        travel_time = G[current_city][best_next_city]['travel_time']
        travel_cost = G[current_city][best_next_city]['travel_cost']
        visit_time = G.nodes[best_next_city]['visit_time']
        ticket_price = G.nodes[best_next_city]['ticket_price']
        
        total_time += travel_time + visit_time
        total_travel_cost += travel_cost
        total_ticket_cost += ticket_price
        
        current_city = best_next_city
    
    # 计算返回起始城市的交通时间和费用
    if len(route) > 1 and route[-1] != start_city:
        if G.has_edge(route[-1], start_city):
            return_travel_time = G[route[-1]][start_city]['travel_time']
            return_travel_cost = G[route[-1]][start_city]['travel_cost']
            
            # 检查是否有足够时间返回
            if total_time + return_travel_time <= max_hours:
                total_time += return_travel_time
                total_travel_cost += return_travel_cost
                route.append(start_city)
    
    # 计算总费用
    total_cost = total_travel_cost + total_ticket_cost
    
    return route, total_time, total_travel_cost, total_ticket_cost, total_cost, G

# 7. 可视化路线
def visualize_route(route, G, provinces):
    """
    使用matplotlib直接可视化旅游路线，并添加省级行政区背景
    """
    # 创建图形
    fig, ax = plt.subplots(figsize=(15, 12))
    
    # 绘制省级行政区背景
    provinces.boundary.plot(ax=ax, linewidth=0.8, color='gray', alpha=0.5)
    
    # 为省份添加名称标签
    for idx, province in provinces.iterrows():
        if 'NAME' in province:
            # 获取省份的中心点坐标
            x, y = province.geometry.centroid.x, province.geometry.centroid.y
            ax.text(x, y, province['NAME'], fontsize=8, ha='center', color='gray', alpha=0.7)
    
    # 绘制路线中的城市
    route_x = []
    route_y = []
    for city in route:
        if city in G.nodes:
            route_x.append(G.nodes[city]['x'])
            route_y.append(G.nodes[city]['y'])
    
    ax.scatter(route_x, route_y, color='red', s=50, alpha=0.6)
    
    # 绘制路线
    for i in range(len(route)-1):
        city1 = route[i]
        city2 = route[i+1]
        
        if city1 in G.nodes and city2 in G.nodes:
            x1, y1 = G.nodes[city1]['x'], G.nodes[city1]['y']
            x2, y2 = G.nodes[city2]['x'], G.nodes[city2]['y']
            ax.plot([x1, x2], [y1, y2], 'b-', linewidth=2)
    
    # 添加城市和山名标签
    for city in route:
        if city in G.nodes:
            x = G.nodes[city]['x']
            y = G.nodes[city]['y']
            mountain_name = G.nodes[city]['mountain_name']
            ax.annotate(f"{city}\n({mountain_name})", (x, y), xytext=(5, 5), 
                       textcoords='offset points', fontsize=10)
    
    # 设置标题和坐标轴标签
    ax.set_title('最佳山景旅游路线', fontsize=16)
    
    # 保存图像
    plt.savefig('4.2_mountain_route.png', dpi=300, bbox_inches='tight')
    plt.close()

# 8. 生成HTML内容
def generate_html_report(route, total_time, total_travel_cost, total_ticket_cost, total_cost, G):
    """
    生成HTML报告并在浏览器中打开
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>中国山景旅游路线规划</title>
        <style>
            body {
                font-family: 'Microsoft YaHei', sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #1a73e8;
                text-align: center;
                margin-bottom: 30px;
            }
            h2 {
                color: #34a853;
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
                margin-top: 30px;
            }
            .route-item {
                margin: 15px 0;
                padding: 15px;
                background-color: #f9f9f9;
                border-left: 4px solid #4285f4;
                border-radius: 4px;
            }
            .summary {
                margin-top: 30px;
                padding: 20px;
                background-color: #e8f0fe;
                border-radius: 8px;
            }
            .route-map {
                text-align: center;
                margin: 30px 0;
            }
            .route-map img {
                max-width: 100%;
                border-radius: 8px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
            }
            .highlight {
                font-weight: bold;
                color: #ea4335;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>中国山景旅游路线规划</h1>
            
            <div class="route-map">
                <img src="4.2_mountain_route.png" alt="山景旅游路线地图">
            </div>
            
            <h2>路线详情</h2>
    """
    
    # 添加路线详情
    for i, city in enumerate(route):
        mountain_name = G.nodes[city]['mountain_name']
        mountain_score = G.nodes[city]['mountain_score']
        visit_time = G.nodes[city]['visit_time']
        ticket_price = G.nodes[city]['ticket_price']
        
        html_content += f'<div class="route-item">'
        
        if i > 0:  # 不是起始城市
            prev_city = route[i-1]
            travel_time = G[prev_city][city]['travel_time']
            travel_cost = G[prev_city][city]['travel_cost']
            html_content += f"""
            <p><span class="highlight">{i+1}. {city} - {mountain_name}</span> (评分: {mountain_score:.1f})</p>
            <p>从{prev_city}乘坐高铁约{travel_time:.1f}小时，费用{travel_cost:.0f}元</p>
            <p>游览时间: {visit_time}小时，门票: {ticket_price}元</p>
            """
        else:  # 起始城市
            html_content += f"""
            <p><span class="highlight">{i+1}. {city} - {mountain_name}</span> (评分: {mountain_score:.1f})</p>
            <p>入境城市，游览时间: {visit_time}小时，门票: {ticket_price}元</p>
            """
        
        html_content += '</div>'
    
    # 添加总结信息
    html_content += f"""
            <div class="summary">
                <h2>行程总结</h2>
                <p>总游玩时间: <span class="highlight">{total_time:.2f} 小时</span></p>
                <p>总交通费用: <span class="highlight">{total_travel_cost:.2f} 元</span></p>
                <p>总门票费用: <span class="highlight">{total_ticket_cost:.2f} 元</span></p>
                <p>总费用: <span class="highlight">{total_cost:.2f} 元</span></p>
                <p>可游玩山景数量: <span class="highlight">{len(route)}</span></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 保存HTML文件
    html_file = "4.2_mountain_route_report.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # 获取文件的绝对路径
    abs_path = os.path.abspath(html_file)
    
    return abs_path

# 9. 主函数
def main():
    # 加载数据
    mountain_data, city_locations, provinces = load_data()
    
    # 选择合适的入境城市
    # 优先选择有国际机场的城市
    start_city = None
    for city in ["北京", "上海", "广州", "成都", "昆明", "西安"]:
        if city in mountain_data['城市'].values:
            start_city = city
            break
    
    # 规划最佳路线
    route, total_time, total_travel_cost, total_ticket_cost, total_cost, G = plan_optimal_route(
        mountain_data, city_locations, start_city=start_city, max_hours=144
    )
    
    # 打印结果
    print("最佳山景旅游路线:")
    for i, city in enumerate(route):
        mountain_name = G.nodes[city]['mountain_name']
        mountain_score = G.nodes[city]['mountain_score']
        visit_time = G.nodes[city]['visit_time']
        ticket_price = G.nodes[city]['ticket_price']
        
        if i > 0:  # 不是起始城市
            prev_city = route[i-1]
            travel_time = G[prev_city][city]['travel_time']
            travel_cost = G[prev_city][city]['travel_cost']
            print(f"{i+1}. {city} - {mountain_name} (评分: {mountain_score:.1f})")
            print(f"   从{prev_city}乘坐高铁约{travel_time:.1f}小时，费用{travel_cost:.0f}元")
            print(f"   游览时间: {visit_time}小时，门票: {ticket_price}元")
        else:  # 起始城市
            print(f"{i+1}. {city} - {mountain_name} (评分: {mountain_score:.1f})")
            print(f"   入境城市，游览时间: {visit_time}小时，门票: {ticket_price}元")
    
    print(f"\n总游玩时间: {total_time:.2f} 小时")
    print(f"总交通费用: {total_travel_cost:.2f} 元")
    print(f"总门票费用: {total_ticket_cost:.2f} 元")
    print(f"总费用: {total_cost:.2f} 元")
    print(f"可游玩山景数量: {len(route)}")
    
    # 可视化路线
    visualize_route(route, G, provinces)
    
    # 生成HTML报告并获取文件路径
    html_file_path = generate_html_report(route, total_time, total_travel_cost, total_ticket_cost, total_cost, G)
    
    # 在浏览器中打开HTML文件
    print(f"\n正在浏览器中打开报告: {html_file_path}")
    webbrowser.open('file://' + html_file_path)


if __name__ == "__main__":
    main()
