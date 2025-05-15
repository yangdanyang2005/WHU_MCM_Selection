import pandas as pd
import numpy as np
import geopandas as gpd
from math import radians, cos, sin, asin, sqrt
import networkx as nx
import matplotlib.pyplot as plt
from pyproj import Transformer
import matplotlib as mpl
from matplotlib.font_manager import FontProperties
import webbrowser
import os

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# 1. 加载数据
def load_data():
    # 加载最令外国游客向往的50个城市数据
    top_cities = pd.read_csv('2.2_top_50_cities_for_foreign_tourists.csv')
    
    # 加载城市地理位置数据
    city_locations = gpd.read_file('3_地级城市驻地.geojson')
    
    # 加载省级行政区数据
    provinces = gpd.read_file('3_省级行政区.geojson')
    
    # 加载广州景点数据
    guangzhou_attractions = pd.read_csv('2.1_best_attractions/广州.csv')
    
    return top_cities, city_locations, provinces, guangzhou_attractions

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

# 4. 计算城市的吸引力得分
def calculate_city_attraction_score(city_row, top_cities_df):
    """
    计算城市的吸引力得分
    """
    city_name = city_row['name']
    
    # 检查城市是否在top_cities中
    if city_name in top_cities_df['城市'].values:
        # 假设top_cities_df中有排名信息，排名越高分数越高
        rank = top_cities_df[top_cities_df['城市'] == city_name].index[0] + 1
        # 排名越低，分数越高（反向关系）
        attraction_score = 51 - rank  # 假设共50个城市，排名第1的得分为50
    else:
        attraction_score = 0  # 不在列表中的城市吸引力为0
    
    return attraction_score

# 5. 估算每个城市的游览时间
def estimate_visit_time(city_name, top_cities_df):
    """
    估算游览一个城市所需的时间（小时）
    """
    # 根据城市在列表中的排名来确定游览时间
    if city_name in top_cities_df['城市'].values:
        rank = top_cities_df[top_cities_df['城市'] == city_name].index[0] + 1
        
        # 排名越高的城市，游览时间越长（更多景点）
        if rank <= 10:
            visit_time = 24  # 一线城市需要一整天
        elif rank <= 20:
            visit_time = 18  # 二线城市需要18小时
        elif rank <= 30:
            visit_time = 12  # 三线城市需要12小时
        else:
            visit_time = 8   # 其他城市需要8小时
    else:
        visit_time = 6  # 不在列表中的城市默认6小时
    
    return visit_time

# 6. 估算城市游览费用
def estimate_city_cost(city_name, top_cities_df):
    """
    估算游览一个城市的门票费用（元）
    """
    # 根据城市在列表中的排名来估算费用
    if city_name in top_cities_df['城市'].values:
        rank = top_cities_df[top_cities_df['城市'] == city_name].index[0] + 1
        
        # 排名越高的城市，门票费用越高
        if rank <= 10:
            city_cost = 500  # 一线城市景点门票总费用较高
        elif rank <= 20:
            city_cost = 400  # 二线城市
        elif rank <= 30:
            city_cost = 300  # 三线城市
        else:
            city_cost = 200  # 其他城市
    else:
        city_cost = 300  # 不在列表中的城市默认费用
    
    return city_cost


# 7. 规划最佳旅游路线
def plan_optimal_route(top_cities, city_locations, guangzhou_attractions=None, start_city="广州", max_hours=144):
    """
    规划最佳旅游路线 - 优化城市数量与费用
    """
    # 检查广州是否在城市位置数据中
    if start_city not in city_locations['name'].values:
        raise ValueError(f"起始城市 {start_city} 不在地理位置数据中")
    
    # 为广州添加一个较高的吸引力分数，确保它被包含在路线中
    if start_city not in top_cities['城市'].values:
        print(f"警告: 起始城市 {start_city} 不在最令外国游客向往的50个城市列表中")
    
    # 创建城市图
    G = nx.Graph()
    
    # 添加节点（所有在top_cities中的城市以及起始城市）
    valid_cities = []
    for idx, city in city_locations.iterrows():
        city_name = city['name']
        
        # 如果是起始城市或在top_cities中，则添加到图中
        if city_name == start_city or city_name in top_cities['城市'].values:
            # 计算吸引力得分和游览时间
            attraction_score = calculate_city_attraction_score(city, top_cities)
            visit_time = estimate_visit_time(city_name, top_cities)
            
            # 添加节点
            G.add_node(city_name, 
                      x=city.geometry.x, 
                      y=city.geometry.y, 
                      attraction_score=attraction_score,
                      visit_time=visit_time)
            valid_cities.append(city_name)
    
    # 添加边（城市之间的连接）
    for i in range(len(valid_cities)):
        for j in range(i+1, len(valid_cities)):
            city1 = valid_cities[i]
            city2 = valid_cities[j]
            
            # 计算距离
            x1, y1 = G.nodes[city1]['x'], G.nodes[city1]['y']
            x2, y2 = G.nodes[city2]['x'], G.nodes[city2]['y']
            distance = calculate_distance(x1, y1, x2, y2)
            
            # 估算交通时间和费用
            travel_time, travel_cost = estimate_travel_time_and_cost(distance)
            
            # 添加边
            G.add_edge(city1, city2, distance=distance, travel_time=travel_time, travel_cost=travel_cost)
    
    # 寻找最佳路线
    # 使用贪心算法: 从起始城市开始，每次选择能够最大化城市数量/费用比的下一个城市
    current_city = start_city
    route = [current_city]
    total_time = G.nodes[current_city]['visit_time']  # 初始城市游览时间
    
    # 获取门票价格
    if current_city == "广州" and guangzhou_attractions is not None:
        ticket_price = calculate_guangzhou_ticket_price(guangzhou_attractions)
    else:
        ticket_price = get_city_ticket_price(current_city, top_cities)
        
    total_cost = ticket_price  # 初始城市费用包含门票
    
    # 计算可游览景点数量
    if current_city == "广州" and guangzhou_attractions is not None:
        total_attractions = len(guangzhou_attractions)
    else:
        total_attractions = estimate_attractions_per_city(current_city, top_cities)
    
    # 已访问城市集合
    visited = {current_city}
    
    while total_time < max_hours:
        best_next_city = None
        best_score = -1
        
        # 遍历所有相邻城市
        for neighbor in valid_cities:
            if neighbor in visited:
                continue
                
            # 计算到达该城市的交通时间和费用
            travel_time = G[current_city][neighbor]['travel_time']
            travel_cost = G[current_city][neighbor]['travel_cost']
            
            # 游览该城市所需时间
            visit_time = G.nodes[neighbor]['visit_time']
            
            # 获取门票价格
            if neighbor == "广州" and guangzhou_attractions is not None:
                visit_cost = calculate_guangzhou_ticket_price(guangzhou_attractions)
            else:
                visit_cost = get_city_ticket_price(neighbor, top_cities)
            
            # 检查是否超出总时间限制
            if total_time + travel_time + visit_time > max_hours:
                continue
                
            # 计算费用效益得分 - 优先选择费用低的城市
            cost_efficiency = 1 / (travel_cost + visit_cost)
            
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
        
        # 获取门票价格
        if best_next_city == "广州" and guangzhou_attractions is not None:
            visit_cost = calculate_guangzhou_ticket_price(guangzhou_attractions)
            attractions_count = len(guangzhou_attractions)
        else:
            visit_cost = get_city_ticket_price(best_next_city, top_cities)
            attractions_count = estimate_attractions_per_city(best_next_city, top_cities)
        
        total_time += travel_time + visit_time
        total_cost += travel_cost + visit_cost
        total_attractions += attractions_count
        
        current_city = best_next_city
    
    # 计算返回起始城市的交通时间和费用
    if len(route) > 1 and route[-1] != start_city:
        return_travel_time = G[route[-1]][start_city]['travel_time']
        return_travel_cost = G[route[-1]][start_city]['travel_cost']
        
        # 检查是否有足够时间返回
        if total_time + return_travel_time <= max_hours:
            total_time += return_travel_time
            total_cost += return_travel_cost
            route.append(start_city)
    
    return route, total_time, total_cost, total_attractions, G


# 8. 可视化路线（添加省级行政区背景）
def visualize_route(route, city_locations, G, provinces):
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
    
    # 获取所有城市的坐标
    x_coords = []
    y_coords = []
    for city in city_locations['name']:
        if city in G.nodes:
            x_coords.append(G.nodes[city]['x'])
            y_coords.append(G.nodes[city]['y'])
    
    # 绘制所有城市
    ax.scatter(x_coords, y_coords, color='gray', s=5)
    
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
    
    # 添加城市标签
    for city in route:
        if city in G.nodes:
            x = G.nodes[city]['x']
            y = G.nodes[city]['y']
            ax.annotate(city, (x, y), xytext=(5, 5), textcoords='offset points', fontsize=10)
    
    # 设置标题和坐标轴标签
    ax.set_title('最佳旅游路线（优化城市数量与费用）', fontsize=16)
    
    # 保存图像（使用高DPI以确保清晰度）
    plt.savefig('4_optimal_route.png', dpi=300, bbox_inches='tight')
    plt.close()

# 9. 计算每个城市的景点数量
def estimate_attractions_per_city(city_name, top_cities, guangzhou_attractions=None):
    """
    估算每个城市的景点数量，广州使用实际数据
    """
    if city_name == "广州" and guangzhou_attractions is not None:
        return len(guangzhou_attractions)
    elif city_name in top_cities['城市'].values:
        rank = top_cities[top_cities['城市'] == city_name].index[0] + 1
        # 根据城市排名估算景点数量 
        if rank <= 10:
            return 15
        elif rank <= 20:
            return 12
        elif rank <= 30:
            return 10
        else:
            return 8
    else:
        return 8  # 其他城市默认景点数

# 10. 生成HTML内容
def generate_html_report(route, total_time, total_cost, total_attractions, G, top_cities, guangzhou_attractions=None):
    """
    生成HTML报告并在浏览器中打开
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>最佳旅游路线规划（优化城市数量与费用）</title>
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
            <h1>最佳旅游路线规划（优化城市数量与费用）</h1>
            
            <div class="route-map">
                <img src="4_optimal_route.png" alt="旅游路线地图">
            </div>
            
            <h2>路线详情</h2>
    """
    
    # 添加路线详情
    for i, city in enumerate(route):
        if city == "广州" and guangzhou_attractions is not None:
            attractions = len(guangzhou_attractions)
            city_cost = calculate_guangzhou_ticket_price(guangzhou_attractions)
        else:
            attractions = estimate_attractions_per_city(city, top_cities)
            city_cost = get_city_ticket_price(city, top_cities)
            
        html_content += f'<div class="route-item">'
        
        if i > 0:  # 不是起始城市
            prev_city = route[i-1]
            travel_time = G[prev_city][city]['travel_time']
            travel_cost = G[prev_city][city]['travel_cost']
            html_content += f"""
            <p><span class="highlight">{i+1}. {city}</span> 
            (从{prev_city}乘坐高铁约{travel_time:.1f}小时，交通费用{travel_cost:.0f}元，门票费用约{city_cost:.0f}元，可游览{attractions}个景点)</p>
            """
        else:  # 起始城市
            html_content += f"""
            <p><span class="highlight">{i+1}. {city}</span> (起点，门票费用约{city_cost:.0f}元，可游览{attractions}个景点)</p>
            """
        
        html_content += '</div>'
    
    # 添加总结信息
    html_content += f"""
            <div class="summary">
                <h2>行程总结</h2>
                <p>总游玩时间: <span class="highlight">{total_time:.2f} 小时</span></p>
                <p>总费用(含门票和交通): <span class="highlight">{total_cost:.2f} 元</span></p>
                <p>可游玩景点数量: <span class="highlight">{total_attractions}</span></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 保存HTML文件
    html_file = "4_travel_route_report.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # 获取文件的绝对路径
    abs_path = os.path.abspath(html_file)
    
    return abs_path



# 11. 解析门票价格
def parse_ticket_price(price_str, top_cities_df, city_name):
    """
    解析门票价格字符串，返回数值
    """
    if pd.isna(price_str):
        return estimate_city_cost(city_name, top_cities_df)
    
    # 尝试提取数字
    import re
    numbers = re.findall(r'\d+', str(price_str))
    if numbers:
        return float(numbers[0])
    
    # 处理特殊情况
    if '免费' in str(price_str):
        return 0
    
    # 对于其他情况（如"具体收费情况以现场公示为主"），使用估算
    return estimate_city_cost(city_name, top_cities_df)

# 12. 获取城市门票费用
def get_city_ticket_price(city_name, top_cities_df, guangzhou_attractions=None):
    """
    获取城市门票费用，优先使用CSV中的数据，缺失时使用估算
    """
    if city_name == "广州" and guangzhou_attractions is not None:
        return calculate_guangzhou_ticket_price(guangzhou_attractions)
    elif city_name in top_cities_df['城市'].values:
        price_str = top_cities_df[top_cities_df['城市'] == city_name]['门票'].values[0]
        return parse_ticket_price(price_str, top_cities_df, city_name)
    else:
        return estimate_city_cost(city_name, top_cities_df)
    
    
# 13. 计算广州景点门票总价
def calculate_guangzhou_ticket_price(guangzhou_attractions):
    """
    计算广州景点的总门票价格
    """
    total_price = 0
    
    # 检查是否有门票列
    if '门票' in guangzhou_attractions.columns:
        # 遍历每个景点的门票价格
        for _, attraction in guangzhou_attractions.iterrows():
            price_str = attraction['门票']
            # 使用与其他城市相同的价格解析方法
            if pd.isna(price_str):
                continue
            
            # 尝试提取数字
            import re
            numbers = re.findall(r'\d+', str(price_str))
            if numbers:
                total_price += float(numbers[0])
            # 处理特殊情况
            elif '免费' in str(price_str).lower():
                total_price += 0
            else:
                # 对于无法解析的价格，使用默认值
                total_price += 50  # 假设平均每个景点50元
    else:
        # 如果没有门票列，使用默认值
        total_price = 300
    
    return total_price

# 14. 主函数
def main():
    # 加载数据
    top_cities, city_locations, provinces, guangzhou_attractions = load_data()
    
    # 规划最佳路线
    route, total_time, total_cost, total_attractions, G = plan_optimal_route(
        top_cities, city_locations, guangzhou_attractions, start_city="广州", max_hours=144
    )
    
    # 打印结果
    print("最佳旅游路线（优化城市数量与费用）:")
    for i, city in enumerate(route):
        if city == "广州":
            attractions = len(guangzhou_attractions)
            city_cost = calculate_guangzhou_ticket_price(guangzhou_attractions)
        else:
            attractions = estimate_attractions_per_city(city, top_cities)
            city_cost = get_city_ticket_price(city, top_cities)
            
        if i > 0:  # 不是起始城市
            prev_city = route[i-1]
            travel_time = G[prev_city][city]['travel_time']
            travel_cost = G[prev_city][city]['travel_cost']
            print(f"{i+1}. {city} (从{prev_city}乘坐高铁约{travel_time:.1f}小时，交通费用{travel_cost:.0f}元，门票费用约{city_cost:.0f}元，可游览{attractions}个景点)")
        else:  # 起始城市
            print(f"{i+1}. {city} (起点，门票费用约{city_cost:.0f}元，可游览{attractions}个景点)")
    
    # 计算实际游玩的城市数量（如果路线是环形的，则需要减去重复计算的起点/终点）
    city_count = len(route) - (2 if route[0] == route[-1] else 1)
    
    print(f"\n总游玩时间: {total_time:.2f} 小时")
    print(f"总费用(含门票和交通): {total_cost:.2f} 元")
    print(f"可游玩景点数量: {total_attractions}")
    
    # 可视化路线
    visualize_route(route, city_locations, G, provinces)
    
    # 生成HTML报告并获取文件路径
    html_file_path = generate_html_report(route, total_time, total_cost, total_attractions, G, top_cities, guangzhou_attractions)
    
    # 在浏览器中打开HTML文件
    print(f"\n正在浏览器中打开报告: {html_file_path}")
    webbrowser.open('file://' + html_file_path)


if __name__ == "__main__":
    main()
