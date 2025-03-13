import os
from datetime import datetime
from enum import Enum
import json
import requests
from typing import List, Optional, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError


class WeatherTools(str, Enum):
    GET_24H_WEATHER = "get_24h_weather"
    """获取未来24小时天气"""


def get_city_info(
    key: str,
    location: str,
    adm: Optional[str] = None, 
    range: Optional[str] = None, 
    number: Optional[int] = None,
    lang: Optional[str] = None
) -> List[dict]:
    """
    获取城市信息
    
    Args:
        key (str): 和风天气API Key
        location (str): 需要查询地区的名称，支持文字、以英文逗号分隔的经度,纬度坐标（十进制，最多支持小数点后两位）、LocationID或Adcode（仅限中国城市）。例如 location=北京 或 location=116.41,39.92
                        注意：模糊搜索：当location传递的为文字时，支持模糊搜索，即用户可以只输入城市名称一部分进行搜索，最少一个汉字或2个字符，
                        结果将按照相关性和Rank值进行排列，便于开发或用户进行选择他们需要查看哪个城市的天气。例如location=bei，
                        将返回与bei相关性最强的若干结果，包括黎巴嫩的贝鲁特和中国的北京市
                        重名：当location传递的为文字时，可能会出现重名的城市，例如陕西省西安市、吉林省辽源市下辖的西安区和黑龙江省牡丹江
                        市下辖的西安区，此时会根据Rank值排序返回所有结果。在这种情况下，可以通过adm参数的方式进一步确定需要查询的城市或地区，
                        例如location=西安&adm=黑龙江
                        
        adm (Optional[str]): 城市的上级行政区划，可设定只在某个行政区划范围内进行搜索，用于排除重名城市或对结果进行过滤。例如 adm=beijing
        range (Optional[str]): 搜索范围，可设定只在某个国家或地区范围内进行搜索，国家和地区名称需使用ISO 3166 所定义的国家代码。如果不设置此参数，搜索范围将在所有城市。例如 range=cn
        number (Optional[int]): 返回结果的数量，取值范围1-20，默认返回10个结果。
        lang (Optional[str]): 多语言设置，请阅读多语言文档，了解我们的多语言是如何工作、如何设置以及数据是否支持多语言。
    Returns:
        List[dict]: 包含城市信息的字典,包括:
            - location.name 地区/城市名称
            - location.id 地区/城市ID
            - location.lat 地区/城市纬度
            - location.lon 地区/城市经度
            - location.adm2 地区/城市的上级行政区划名称
            - location.adm1 地区/城市所属一级行政区域
            - location.country 地区/城市所属国家名称
            - location.tz 地区/城市所在时区
            - location.utcOffset 地区/城市目前与UTC时间偏移的小时数，参考详细说明
            - location.isDst 地区/城市是否当前处于夏令时。1 表示当前处于夏令时，0 表示当前不是夏令时。
            - location.type 地区/城市的属性
            - location.rank 地区评分
            - location.fxLink 该地区的天气预报网页链接，便于嵌入你的网站或应用
            - refer.sources 原始数据来源，或数据源说明，可能为空
            - refer.license 数据许可或版权声明，可能为空
    """
    base_url = 'https://geoapi.qweather.com/v2/city/lookup?'
    params = {
        'key': key,
        'location': location,
    }
    if adm:
        params['adm'] = adm
    if range:
        params['range'] = range
    if number:
        params['number'] = number
    if lang:
        params['lang'] = lang
    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise McpError(f"Failed to get city info: {response.status_code} {response.text}")
    resp_data = response.json()
    # 根据状态码处理不同情况
    code = resp_data.get('code')
    if resp_data.get('code') != '200':
        raise McpError(f"Failed to get city info: {resp_data.get('code')}")
    data = resp_data.get('location')
    return data


def get_24h_weather(key, location_id: str, place: str):
    """
    获取指定城市24小时天气预报

    Args:
        key (str): 和风天气API key
        location_id (str): 城市ID
        place (str): 地区名称, 用于显示

    Returns:
        str: 格式化后的天气预报信息,包括:
            - 预报时间: 相对时间(今天/明天/后天) + 具体时间
            - 距离现在: 1小时后/X小时/X天
            - 温度: 摄氏度
            - 天气: 天气状况文字描述
            - 风向: 风向信息
            - 风速: 风速等级
            - 湿度: 相对湿度百分比
            - 降水概率: 百分比
    """
    url = "https://devapi.qweather.com/v7/weather/24h?"
    params = {
        'key': key,
        'location': location_id,
    }
    response = requests.get(url, params=params)
    data = response.json()
    return format_weather_data(data, place)


def format_weather_data(data, place):
    hourly_forecast = data['hourly']
    formatted_data = f"\n 这是查询到的关于{place}未来24小时的天气信息: \n"
    for forecast in hourly_forecast:
        # 将预报时间转换为datetime对象
        forecast_time = datetime.strptime(forecast['fxTime'], '%Y-%m-%dT%H:%M%z')
        # 获取预报时间的时区
        forecast_tz = forecast_time.tzinfo
        # 获取当前时间（使用预报时间的时区）
        now = datetime.now(forecast_tz)
        # 计算预报日期与当前日期的差值
        days_diff = (forecast_time.date() - now.date()).days
        if days_diff == 0:
            forecast_date_str = '今天'
        elif days_diff == 1:
            forecast_date_str = '明天'
        elif days_diff == 2:
            forecast_date_str = '后天'
        else:
            forecast_date_str = str(days_diff) + '天后'
        forecast_time_str = forecast_date_str + ' ' + forecast_time.strftime('%H:%M')
        # 计算预报时间与当前时间的差值
        time_diff = forecast_time - now
        # 将差值转换为小时
        hours_diff = time_diff.total_seconds() // 3600
        if hours_diff < 1:
            hours_diff_str = '1小时后'
        elif hours_diff >= 24:
            # 如果超过24小时，转换为天数
            days_diff = hours_diff // 24
            hours_diff_str = str(int(days_diff)) + '天'
        else:
            hours_diff_str = str(int(hours_diff)) + '小时'
        # 将预报时间和当前时间的差值添加到输出中
        formatted_data += '预报时间: ' + forecast_time_str + '  距离现在有: ' + hours_diff_str + '\n'
        formatted_data += '温度: ' + forecast['temp'] + '°C\n'
        formatted_data += '天气: ' + forecast['text'] + '\n'
        formatted_data += '风向: ' + forecast['windDir'] + '\n'
        formatted_data += '风速: ' + forecast['windSpeed'] + '级\n'
        formatted_data += '湿度: ' + forecast['humidity'] + '%\n'
        formatted_data += '降水概率: ' + forecast['pop'] + '%\n'
        # formatted_data += '降水量: ' + forecast['precip'] + 'mm\n'
        formatted_data += '\n'
    return formatted_data


def split_query(query):
    parts = query.split()
    adm = parts[0]
    if len(parts) == 1:
        return adm, adm
    location = parts[1] if parts[1] != 'None' else adm
    return location, adm


class WeatherService:
    
    def __init__(self, key: Optional[str] = None):
        self.key = key
        if not self.key:
            self.key = os.getenv("QWEATHER_API_KEY")
    
    def weather(self, query: str):
        location, adm = split_query(query)
        if self.key == "":
            return "和风天气API Key 未设置"
        try:
            locations = get_city_info(key=self.key, location=location, adm=adm)
            location_id = locations[0]['id']
            place = adm + "市" + location + "区"

            weather_data = get_24h_weather(key=self.key, location_id=location_id, place=place)
            return weather_data + "以上是查询到的天气信息，请你查收\n"
        except KeyError:
            try:
                locations = get_city_info(location=adm, adm=adm, key=self.key)
                location_id = locations[0]['id']
                place = adm + "市"
                weather_data = get_24h_weather(key=self.key, location_id=location_id, place=place)
                return weather_data + "重要提醒：用户提供的市和区中，区的信息不存在，或者出现错别字，因此该信息是关于市的天气，请你查收\n"
            except KeyError:
                return "输入的地区不存在，无法提供天气预报"
        
 
async def serve(local_timezone: str | None = None) -> None:
    server = Server("mcp-weather")
    
    weather_service = WeatherService()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """工具列表"""
        return [
            Tool(
                name=WeatherTools.GET_NOW_WEATHER.value,
                description="Get current weather in a specific location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": f"Location, eg: 广州",
                        }
                    },
                    "required": ["location"],
                },
            )
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Handle tool calls for time queries."""
        try:
            match name:
                case WeatherTools.GET_24H_WEATHER.value:
                    location = arguments.get("location")
                    if not location:
                        raise ValueError("Missing required argument: location")

                    result = weather_service.weather(location)
                case _:
                    raise ValueError(f"Unknown tool: {name}")

            return [
                TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
            ]

        except Exception as e:
            raise ValueError(f"Error processing mcp-server-weather query: {str(e)}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)


if __name__ == "__main__":
    weather_service = WeatherService()
    print(weather_service.weather("广州 天河"))