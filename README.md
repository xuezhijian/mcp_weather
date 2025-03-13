# Weather MCP Server

一个提供天气预报和城市信息查询功能的Model Context Protocol服务器。该服务器允许LLMs获取未来24小时的天气信息，并支持通过城市名称、经纬度等方式查询城市信息。

### 可用工具

- `get_24h_weather` - 获取未来24小时的天气预报。
  - 必需参数：
    - `location` (string): 城市名称或经纬度（例如，北京或116.41,39.92）

## 安装

### 使用uv（推荐）

使用[`uv`](https://docs.astral.sh/uv/)时无需特定安装。我们将使用[`uvx`](https://docs.astral.sh/uv/guides/tools/)直接运行*mcp-server-weather*。

### 使用PIP

或者，你可以通过pip安装`mcp-server-weather`：

```bash
pip install mcp-server-weather
```

安装后，你可以使用以下命令作为脚本运行：

```bash
python -m mcp_server_weather
```

## 配置

### 配置Claude.app

在Claude设置中添加：

<details>
<summary>使用uvx</summary>

```json
"mcpServers": {
  "weather": {
    "command": "uvx",
    "args": ["mcp-server-weather"]
  }
}
```
</details>

<details>
<summary>使用docker</summary>

```json
"mcpServers": {
  "weather": {
    "command": "docker",
    "args": ["run", "-i", "--rm", "mcp/weather"]
  }
}
```
</details>

<details>
<summary>使用pip安装</summary>

```json
"mcpServers": {
  "weather": {
    "command": "python",
    "args": ["-m", "mcp_server_weather"]
  }
}
```
</details>

### 配置Zed

在Zed的settings.json中添加：

<details>
<summary>使用uvx</summary>

```json
"context_servers": [
  "mcp-server-weather": {
    "command": "uvx",
    "args": ["mcp-server-weather"]
  }
],
```
</details>

<details>
<summary>使用pip安装</summary>

```json
"context_servers": {
  "mcp-server-weather": {
    "command": "python",
    "args": ["-m", "mcp_server_weather"]
  }
},
```
</details>

## 示例交互

1. 获取未来24小时天气：
```json
{
  "name": "get_24h_weather",
  "arguments": {
    "location": "广州 天河"
  }
}
```
响应：
```json
{
  "location": "广州 天河",
  "forecast": "未来24小时的天气信息..."
}
```

## 调试

你可以使用MCP inspector来调试服务器。对于uvx安装：

```bash
npx @modelcontextprotocol/inspector uvx mcp-server-weather
```

或者如果你在特定目录中安装了包或正在开发：

```bash
cd path/to/servers/src/weather
npx @modelcontextprotocol/inspector uv run mcp-server-weather
```

## 构建

Docker 构建:

```bash
docker build -t mcp/weather .
```

## 贡献

我们鼓励对mcp-server-weather的贡献，以帮助扩展和改进其功能。无论是添加新的天气相关工具、增强现有功能，还是改进文档，你的输入都很有价值。

有关其他MCP服务器和实现模式的示例，请参见：
https://github.com/modelcontextprotocol/servers

欢迎提交拉取请求！随时贡献新想法、错误修复或增强功能，以使mcp-server-weather更加强大和实用。

## 许可证

mcp-server-weather根据MIT许可证授权。这意味着你可以自由使用、修改和分发软件，但需遵守MIT许可证的条款和条件。有关详细信息，请参阅项目存储库中的LICENSE文件。
