import json
import os
from datetime import datetime
from farm2 import AgriculturalAdvisor

def load_crop_data(filename="crop.json"):
    """
    从JSON文件加载作物数据
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"错误: 找不到文件 {filename}")
        return None
    except json.JSONDecodeError:
        print(f"错误: {filename} 文件格式不正确")
        return None

def create_sample_crop_data():
    """
    创建示例作物数据文件
    """
    sample_data = {
        "crop_type": "水稻",
        "growth_stage": "抽穗期",
        "symptoms": ["叶片出现梭形病斑", "穗部变褐"],
        "soil_moisture": 65,
        "location": "北京"
    }
    
    with open("crop_data_sample.json", 'w', encoding='utf-8') as file:
        json.dump(sample_data, file, ensure_ascii=False, indent=4)
    
    print("已创建示例文件: crop_data_sample.json")
    return sample_data

def get_user_input():
    """
    通过命令行交互获取作物数据
    """
    print("\n=== 农业智能顾问数据输入 ===")
    
    crop_type = input("请输入作物类型 (水稻/小麦/玉米): ").strip()
    growth_stage = input("请输入生长阶段 (如: 抽穗期): ").strip()
    soil_moisture = float(input("请输入土壤湿度百分比 (0-100): ").strip())
    location = input("请输入地区 (如: 北京): ").strip()
    
    print("\n请输入症状描述 (每行一个症状，输入空行结束):")
    symptoms = []
    while True:
        symptom = input().strip()
        if not symptom:
            break
        symptoms.append(symptom)
    
    return {
        "crop_type": crop_type,
        "growth_stage": growth_stage,
        "symptoms": symptoms,
        "soil_moisture": soil_moisture,
        "location": location
    }

def save_crop_data(data, filename=None):
    """
    保存作物数据到JSON文件
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crop_data_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    
    print(f"作物数据已保存到: {filename}")
    return filename

def main():
    """
    主启动函数
    """
    print("农业智能顾问启动程序")
    print("=" * 40)
    
    # 配置API密钥
    API_KEY = ""
    
    # 初始化顾问
    advisor = AgriculturalAdvisor(qweather_api_key=API_KEY)
    
    # 选择数据输入方式
    print("\n请选择数据输入方式:")
    print("1. 从JSON文件加载")
    print("2. 手动输入")
    print("3. 使用示例数据")
    
    choice = input("\n请输入选项 (1/2/3): ").strip()
    
    crop_data = None
    location = None
    
    if choice == "1":
        # 从文件加载
        filename = input("请输入JSON文件名 (默认为crop.json): ").strip()
        if not filename:
            filename = "crop.json"
        
        crop_data = load_crop_data(filename)
        if crop_data is None:
            return
        
        # 检查是否包含位置信息
        if "location" in crop_data:
            location = crop_data["location"]
            # 从数据中移除位置，因为主程序需要单独的参数
            location_from_data = crop_data.pop("location")
        else:
            location = input("请输入地区: ").strip()
    
    elif choice == "2":
        # 手动输入
        crop_data = get_user_input()
        location = crop_data.pop("location")  # 提取位置信息
        # 询问是否保存
        save = input("\n是否保存输入数据? (y/n): ").strip().lower()
        if save == 'y':
            save_filename = input("请输入保存文件名 (直接回车使用默认名称): ").strip()
            if not save_filename:
                save_crop_data(crop_data)
            else:
                save_crop_data(crop_data, save_filename)
    
    elif choice == "3":
        # 使用示例数据
        if not os.path.exists("crop_data_sample.json"):
            print("创建示例数据文件...")
            crop_data = create_sample_crop_data()
        else:
            crop_data = load_crop_data("crop_data_sample.json")
        
        if crop_data is None:
            return
        
        location = crop_data.pop("location")
        print("使用示例数据进行评估...")
    
    else:
        print("无效选项，程序退出")
        return
    
    # 生成报告
    try:
        print("\n" + "="*50)
        print("正在生成农业智能报告...")
        print("="*50)
        
        report = advisor.generate_report(crop_data, location)
        print(report)
        
        # 询问是否保存报告
        save_report = input("\n是否保存报告到文件? (y/n): ").strip().lower()
        if save_report == 'y':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"C:/Users/ww/Desktop/agricultural_report_{timestamp}.txt"

            
            with open(report_filename, 'w', encoding='utf-8') as file:
                file.write(report)
            
            print(f"报告已保存到: {report_filename}")
    
    except Exception as e:
        print(f"生成报告时发生错误: {e}")
        print("请检查API密钥和网络连接")

if __name__ == "__main__":

    main()
