import requests
import random
from datetime import datetime, timedelta

class AgriculturalAdvisor:
    def __init__(self, qweather_api_key=None):
        # 初始化病虫害数据库
        self.pest_database = {
            "水稻": [
                {"name": "稻瘟病", "symptoms": ["叶片出现梭形病斑", "穗部变褐", "茎秆腐烂"], "treatment": "使用三环唑或稻瘟灵喷雾", "weather_risk": ["高湿", "多雨"]},
                {"name": "稻飞虱", "symptoms": ["叶片黄化", "植株矮小", "蜜露分泌物"], "treatment": "使用吡虫啉或噻虫嗪喷雾", "weather_risk": ["温暖", "潮湿"]}
            ],
            "小麦": [
                {"name": "白粉病", "symptoms": ["叶片白色粉状物", "叶片卷曲", "生长受阻"], "treatment": "使用戊唑醇或醚菌酯喷雾", "weather_risk": ["高湿", "阴天"]},
                {"name": "蚜虫", "symptoms": ["叶片卷曲", "蜜露分泌物", "植株生长不良"], "treatment": "使用吡虫啉或高效氯氟氰菊酯喷雾", "weather_risk": ["干燥", "温暖"]}
            ],
            "玉米": [
                {"name": "玉米螟", "symptoms": ["茎秆蛀孔", "穗部受损", "叶片被啃食"], "treatment": "使用氯虫苯甲酰胺或高效氯氟氰菊酯", "weather_risk": ["温暖", "少雨"]},
                {"name": "大斑病", "symptoms": ["叶片出现大型病斑", "病斑呈灰褐色", "叶片早衰"], "treatment": "使用苯醚甲环唑或嘧菌酯喷雾", "weather_risk": ["高湿", "多雨"]}
            ]
        }
        
        # 作物灌溉需求
        self.water_requirements = {
            "水稻": {"min_moisture": 80, "optimal_moisture": 90, "critical_stage": "抽穗期"},
            "小麦": {"min_moisture": 60, "optimal_moisture": 75, "critical_stage": "拔节期"},
            "玉米": {"min_moisture": 65, "optimal_moisture": 80, "critical_stage": "抽雄期"}
        }
        
        # 和风天气API密钥
        self.api_key = qweather_api_key
        self.weather_base_url = "https://devapi.qweather.com/v7"
    
    def get_location_id(self, city_name):
        """获取城市的位置ID"""
        if not self.api_key:
            return {"error": "未配置和风天气API密钥"}
        
        try:
            url = f"https://geoapi.qweather.com/v2/city/lookup?location={city_name}&key={self.api_key}"
            response = requests.get(url)
            data = response.json()
            
            if data['code'] != '200':
                return {"error": f"获取位置信息失败: {data.get('message', '未知错误')}"}
            
            if not data['location']:
                return {"error": f"未找到城市: {city_name}"}
            
            return data['location'][0]['id']
            
        except Exception as e:
            return {"error": f"获取位置ID时发生错误: {str(e)}"}
    
    def get_weather_data(self, city_name):
        """获取实时天气数据"""
        if not self.api_key:
            return {"error": "未配置和风天气API密钥"}
        
        try:
            # 获取位置ID
            location_id = self.get_location_id(city_name)
            if isinstance(location_id, dict) and 'error' in location_id:
                return location_id
            
            # 获取当前天气
            current_url = f"{self.weather_base_url}/weather/now?location={location_id}&key={self.api_key}"
            response = requests.get(current_url)
            current_data = response.json()
            
            if current_data['code'] != '200':
                return {"error": f"获取天气数据失败: {current_data.get('message', '未知错误')}"}
            
            # 获取3天天气预报
            forecast_url = f"{self.weather_base_url}/weather/3d?location={location_id}&key={self.api_key}"
            forecast_response = requests.get(forecast_url)
            forecast_data = forecast_response.json()
            
            if forecast_data['code'] != '200':
                return {"error": f"获取天气预报失败: {forecast_data.get('message', '未知错误')}"}
            
            # 获取小时预报
            hourly_url = f"{self.weather_base_url}/weather/24h?location={location_id}&key={self.api_key}"
            hourly_response = requests.get(hourly_url)
            hourly_data = hourly_response.json()
            
            weather_info = {
                "location": f"{city_name}, 中国",
                "temperature": float(current_data['now']['temp']),
                "humidity": float(current_data['now']['humidity']),
                "description": current_data['now']['text'],
                "wind_speed": float(current_data['now']['windSpeed']),
                "rain_next_3h": 0,  # 和风天气API不直接提供未来3小时降雨量
                "forecast": self._parse_forecast(forecast_data, hourly_data)
            }
            
            return weather_info
            
        except Exception as e:
            return {"error": f"获取天气数据时发生错误: {str(e)}"}
    
    def _parse_forecast(self, forecast_data, hourly_data):
        """解析天气预报数据"""
        forecast = []
        
        # 处理24小时预报
        for i, item in enumerate(hourly_data.get('hourly', [])[:8]):  # 获取未来24小时预报（每3小时一次）
            forecast.append({
                "datetime": item['fxTime'][5:16].replace('T', ' '),
                "temp": float(item['temp']),
                "humidity": float(item['humidity']),
                "description": item['text'],
                "pop": float(item.get('pop', 0)),  # 降水概率百分比
                "rain": float(item.get('precip', 0))  # 降水量，毫米
            })
        
        return forecast
    
    def get_weather_forecast_summary(self, weather_data):
        """生成天气预报摘要"""
        if 'error' in weather_data:
            return weather_data['error']
        
        summary = []
        summary.append(f"当前位置: {weather_data['location']}")
        summary.append(f"当前天气: {weather_data['description']}, 温度: {weather_data['temperature']}°C, 湿度: {weather_data['humidity']}%")
        
        # 分析未来24小时天气趋势
        tomorrow_rain = sum(item['rain'] for item in weather_data['forecast'])
        max_pop = max(item['pop'] for item in weather_data['forecast'])
        
        if tomorrow_rain > 5:
            summary.append("⚠️ 未来24小时有显著降雨，建议推迟灌溉")
        elif max_pop > 60:
            summary.append("🌧️ 未来24小时有较高降雨概率，请关注天气变化")
        else:
            summary.append("☀️ 未来24小时天气较好，适合进行农田作业")
        
        return "\n".join(summary)
    
    def identify_pest(self, crop_type, symptoms, weather_data=None):
        """识别病虫害（考虑天气因素）"""
        if crop_type not in self.pest_database:
            return "抱歉，目前没有该作物的病虫害数据库。"
        
        possible_pests = []
        for pest in self.pest_database[crop_type]:
            # 计算症状匹配度
            match_count = sum(1 for symptom in symptoms if symptom in pest["symptoms"])
            if match_count > 0:
                confidence = min(100, int((match_count / len(pest["symptoms"])) * 100))
                
                # 考虑天气风险因素
                weather_risk = ""
                if weather_data and 'error' not in weather_data:
                    current_humidity = weather_data['humidity']
                    current_temp = weather_data['temperature']
                    
                    if "高湿" in pest["weather_risk"] and current_humidity > 80:
                        weather_risk = "⚠️ 当前高湿环境可能加剧病害发展"
                    elif "多雨" in pest["weather_risk"] and weather_data['rain_next_3h'] > 2:
                        weather_risk = "⚠️ 降雨天气可能促进病害传播"
                
                possible_pests.append({
                    "name": pest["name"],
                    "confidence": confidence,
                    "treatment": pest["treatment"],
                    "weather_risk": weather_risk
                })
        
        if not possible_pests:
            return "未识别到匹配的病虫害。请提供更详细的症状描述或咨询当地农业专家。"
        
        # 按置信度排序
        possible_pests.sort(key=lambda x: x["confidence"], reverse=True)
        return possible_pests
    
    def irrigation_advice(self, crop_type, growth_stage, soil_moisture, weather_data):
        """提供灌溉建议（考虑实时天气）"""
        if crop_type not in self.water_requirements:
            return "抱歉，目前没有该作物的灌溉指导数据。"
        
        if 'error' in weather_data:
            return [f"无法获取天气数据: {weather_data['error']}"]
        
        requirements = self.water_requirements[crop_type]
        advice = []
        
        # 检查土壤湿度
        if soil_moisture < requirements["min_moisture"]:
            advice.append(f"紧急: 土壤湿度({soil_moisture}%)低于最低要求({requirements['min_moisture']}%)，需要立即灌溉。")
        elif soil_moisture < requirements["optimal_moisture"]:
            advice.append(f"提示: 土壤湿度({soil_moisture}%)略低于理想水平({requirements['optimal_moisture']}%)，建议近期灌溉。")
        else:
            advice.append(f"良好: 土壤湿度({soil_moisture}%)适宜，无需立即灌溉。")
        
        # 考虑生长阶段
        if growth_stage == requirements["critical_stage"]:
            advice.append(f"重要: 作物正处于关键生长期({growth_stage})，需确保水分充足。")
        
        # 基于天气数据的建议
        current_humidity = weather_data['humidity']
        current_temp = weather_data['temperature']
        next_rain = sum(item['rain'] for item in weather_data['forecast'][:2])  # 未来6小时降雨量
        
        if next_rain > 3:
            advice.append(f"天气预报: 未来6小时预计有{next_rain:.1f}mm降雨，可推迟灌溉")
        elif current_temp > 30 and current_humidity < 50:
            advice.append("天气预警: 高温低湿天气，蒸发量大，建议增加灌溉频率")
        elif current_humidity > 85:
            advice.append("环境提示: 当前湿度较高，灌溉时注意避免病害发生")
        
        return advice
    
    def generate_report(self, crop_data, location):
        """生成综合报告"""
        report = []
        report.append("=== 农业智能顾问报告 ===")
        report.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"分析地区: {location}")
        report.append(f"作物类型: {crop_data['crop_type']}")
        report.append(f"生长阶段: {crop_data['growth_stage']}")
        report.append("")
        
        # 获取天气数据
        weather_data = self.get_weather_data(location)
        report.append("--- 天气概况 ---")
        report.append(self.get_weather_forecast_summary(weather_data))
        report.append("")
        
        # 病虫害识别
        report.append("--- 病虫害诊断 ---")
        pests = self.identify_pest(crop_data['crop_type'], crop_data['symptoms'], weather_data)
        if isinstance(pests, str):
            report.append(pests)
        else:
            for pest in pests:
                report.append(f"🔍 疑似病害: {pest['name']} (置信度: {pest['confidence']}%)")
                report.append(f"💊 防治建议: {pest['treatment']}")
                if pest['weather_risk']:
                    report.append(f"🌤️ {pest['weather_risk']}")
                report.append("")
        
        # 灌溉建议
        report.append("--- 灌溉建议 ---")
        irrigation = self.irrigation_advice(
            crop_data['crop_type'],
            crop_data['growth_stage'],
            crop_data['soil_moisture'],
            weather_data
        )
        for advice in irrigation:
            report.append(f"• {advice}")
        
        report.append("")
        report.append("注: 本建议仅供参考，请结合当地实际情况和专家指导做出决策。")
        
        return "\n".join(report)

# 示例
if __name__ == "__main__":
    API_KEY = ""
    
    advisor = AgriculturalAdvisor(qweather_api_key=API_KEY)
    
    sample_crop_data = {
        "crop_type": "水稻",
        "growth_stage": "抽穗期",
        "symptoms": ["叶片出现梭形病斑", "穗部变褐"],
        "soil_moisture": 65
    }
    
    try:
        report = advisor.generate_report(sample_crop_data, "北京")
        print(report)
    except Exception as e:
        print(f"生成报告时发生错误: {e}")

        print("请检查API密钥和网络连接")
