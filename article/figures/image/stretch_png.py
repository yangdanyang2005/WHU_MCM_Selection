import os
from PIL import Image

def stretch_images(folder_path):
    """
    将指定文件夹中的所有PNG图片横向拉伸至原来的1.5倍，纵向不变，并覆盖原图
    
    参数:
        folder_path: 包含PNG图片的文件夹路径
    """
    # 确保文件夹路径存在
    if not os.path.exists(folder_path):
        print(f"文件夹 '{folder_path}' 不存在！")
        return
    
    # 获取文件夹中的所有文件
    files = os.listdir(folder_path)
    
    # 筛选出所有PNG文件
    png_files = [f for f in files if f.lower().endswith('.png')]
    
    if not png_files:
        print(f"文件夹 '{folder_path}' 中没有找到PNG文件！")
        return
    
    # 处理每个PNG文件
    for png_file in png_files:
        file_path = os.path.join(folder_path, png_file)
        try:
            # 打开图像
            img = Image.open(file_path)
            
            # 获取原始尺寸
            width, height = img.size
            
            # 计算新的尺寸（宽度*1.5，高度不变）
            new_width = int(width * 1.5)
            
            # 调整图像大小
            resized_img = img.resize((new_width, height), Image.Resampling.LANCZOS)
            
            # 保存并覆盖原图
            resized_img.save(file_path)
            
            print(f"成功处理: {png_file} - 从 {width}x{height} 调整为 {new_width}x{height}")
            
        except Exception as e:
            print(f"处理 {png_file} 时出错: {e}")
    
    print("所有PNG图片处理完成！")

# 使用示例
stretch_images('figures\image')
