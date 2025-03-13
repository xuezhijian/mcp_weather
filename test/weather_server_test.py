import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from zoneinfo import ZoneInfo

from mcp.shared.exceptions import McpError
from mcp_server_weather.server import (
    WeatherService,
    get_city_info,
    get_24h_weather,
    split_query,
    format_weather_data
)

@pytest.fixture
def weather_service():
    return WeatherService()

@pytest.mark.parametrize(
    "mock_response,location,expected",
    [
        # 正常情况
        (
            {
                "code": "200",
                "location": [{
                    "name": "广州",
                    "id": "101280101",
                    "lat": "23.12517",
                    "lon": "113.28064",
                    "adm2": "广州",
                    "adm1": "广东省",
                    "country": "中国",
                }]
            },
            "广州",
            {
                "name": "广州",
                "id": "101280101",
            }
        ),
        # 多个结果的情况
        (
            {
                "code": "200",
                "location": [
                    {
                        "name": "天河",
                        "id": "101280106",
                        "adm2": "广州",
                        "adm1": "广东省",
                    },
                    {
                        "name": "天河",
                        "id": "101280107",
                        "adm2": "深圳",
                        "adm1": "广东省",
                    }
                ]
            },
            "天河",
            {
                "name": "天河",
                "id": "101280106",
            }
        ),
    ]
)
def test_get_city_info(mock_response, location, expected):
    with patch('mcp_server_weather.server.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp

        result = get_city_info(key="test_key", location=location)
        assert result[0]["name"] == expected["name"]
        assert result[0]["id"] == expected["id"]

@pytest.mark.parametrize(
    "mock_response,location,place,expected_contains",
    [
        (
            {
                "code": "200",
                "hourly": [{
                    "fxTime": "2024-03-20T12:00+08:00",
                    "temp": "25",
                    "text": "晴",
                    "windDir": "东南风",
                    "windSpeed": "3",
                    "humidity": "65",
                    "pop": "10"
                }]
            },
            "101280101",
            "广州市天河区",
            [
                "广州市天河区",
                "温度: 25°C",
                "天气: 晴",
                "风向: 东南风",
                "风速: 3级",
                "湿度: 65%",
                "降水概率: 10%"
            ]
        ),
        (
            {
                "code": "200",
                "hourly": [{
                    "fxTime": "2024-03-20T12:00+08:00",
                    "temp": "20",
                    "text": "多云",
                    "windDir": "北风",
                    "windSpeed": "5",
                    "humidity": "75",
                    "pop": "30"
                }]
            },
            "101280101",
            "广州市",
            [
                "广州市",
                "温度: 20°C",
                "天气: 多云",
                "风向: 北风",
                "风速: 5级",
                "湿度: 75%",
                "降水概率: 30%"
            ]
        )
    ]
)
def test_get_24h_weather(mock_response, location, place, expected_contains):
    with patch('mcp_server_weather.server.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp

        result = get_24h_weather(key="test_key", location=location, place=place)
        for expected in expected_contains:
            assert expected in result

@pytest.mark.parametrize(
    "query,expected_location,expected_adm",
    [
        ("广州", "广州", "广州"),
        ("广州 天河", "天河", "广州"),
        ("广州 None", "广州", "广州"),
        ("深圳 南山", "南山", "深圳"),
    ]
)
def test_split_query(query, expected_location, expected_adm):
    location, adm = split_query(query)
    assert location == expected_location
    assert adm == expected_adm

@pytest.mark.parametrize(
    "test_data,place,expected_contains",
    [
        (
            {
                "hourly": [{
                    "fxTime": datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%dT%H:%M+08:00"),
                    "temp": "26",
                    "text": "多云",
                    "windDir": "东风",
                    "windSpeed": "4",
                    "humidity": "70",
                    "pop": "20"
                }]
            },
            "广州市天河区",
            [
                "广州市天河区",
                "温度: 26°C",
                "天气: 多云",
                "风向: 东风",
                "风速: 4级",
                "湿度: 70%",
                "降水概率: 20%"
            ]
        )
    ]
)
def test_format_weather_data(test_data, place, expected_contains):
    result = format_weather_data(test_data, place)
    for expected in expected_contains:
        assert expected in result

def test_weather_service_no_api_key():
    service = WeatherService("")
    result = service.weather("广州 天河")
    assert result == "和风天气API Key 未设置"

@pytest.mark.parametrize(
    "mock_city_info,mock_weather_data,query,expected_contains",
    [
        (
            [{"name": "广州", "id": "101280101"}],
            "模拟的天气信息",
            "广州 天河",
            ["模拟的天气信息", "以上是查询到的天气信息"]
        )
    ]
)
def test_weather_service_success(weather_service, mock_city_info, mock_weather_data, query, expected_contains):
    with patch('mcp_server_weather.server.get_city_info') as mock_get_city:
        with patch('mcp_server_weather.server.get_24h_weather') as mock_get_weather:
            mock_get_city.return_value = mock_city_info
            mock_get_weather.return_value = mock_weather_data
            print(query)
            result = weather_service.weather(query)
            for expected in expected_contains:
                assert expected in result

def test_weather_service_invalid_location(weather_service):
    with patch('mcp_server_weather.server.get_city_info') as mock_get_city:
        mock_get_city.side_effect = KeyError()
        result = weather_service.weather("不存在的地方")
        assert result == "输入的地区不存在，无法提供天气预报"

@pytest.mark.parametrize(
    "status_code,response_code,expected_error",
    [
        (404, "404", "Failed to get city info: 404"),
        (200, "404", "Failed to get city info: 404"),
        (500, "500", "Failed to get city info: 500"),
    ]
)
def test_get_city_info_error_cases(status_code, response_code, expected_error):
    with patch('mcp_server_weather.server.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = {"code": response_code}
        mock_get.return_value = mock_resp

        with pytest.raises(McpError, match=expected_error):
            get_city_info(key="test_key", location="invalid_location") 
            
