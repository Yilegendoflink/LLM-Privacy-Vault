# LLM-Privacy-Vault (AI 隐私保护网关)

`LLM-Privacy-Vault` 是一个兼容 OpenAI API 格式的轻量级隐私保护网关。它作为反向代理运行，自动拦截并替换发送给大模型（如 OpenAI, DeepSeek, Anthropic）的 Prompt 中的敏感信息（PII），并在收到响应后自动还原，从而解决企业使用公共大模型时面临的数据泄露风险。

## 核心特性
- **无缝集成**：完全兼容 OpenAI API 格式，现有应用只需修改 `Base URL` 即可接入，**零业务代码修改**。
- **多模型支持**：底层集成 LiteLLM，支持路由到 100+ 种不同的大模型。
- **流式响应支持**：完美支持 `stream=True` 的打字机效果，并能正确还原被截断的敏感信息占位符。
- **多语言脱敏**：内置中英文双语敏感信息识别（基于 Microsoft Presidio）, 可自行修改拓展对应语言。

---

## 1. 环境准备与本地运行

### 1.1 安装依赖
确保你的系统已安装 Python 3.10+。
```bash
# 创建虚拟环境 (推荐)
python -m venv venv
# source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 下载 Presidio 依赖的 NLP 模型 (中英文)
python -m spacy download en_core_web_lg
python -m spacy download zh_core_web_sm
```

### 1.2 配置环境变量
项目使用 LiteLLM 进行模型路由，你需要配置目标大模型的 API Key。
在项目根目录创建 `.env` 文件，并根据你使用的模型提供商设置相应的环境变量。

**示例：配置 DeepSeek API Key**
如果你想使用 DeepSeek 模型，请在 `.env` 文件中添加以下内容：
```env
# DeepSeek API Key
DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# 切换中英文识别模式 (可选，默认为 en)
# 支持的值: en (英文), zh (中文)
DEFAULT_LANGUAGE=zh
```

**示例：配置 OpenAI API Key**
```env
# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key
```
*更多模型支持及环境变量配置，请参考 [LiteLLM 官方文档](https://docs.litellm.ai/docs/providers)。*

### 1.3 启动服务
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
服务启动后，API 网关将运行在 `http://localhost:8000`。

---

## 2. 测试指南

### 2.1 运行单元测试
项目包含针对脱敏引擎和还原引擎的单元测试。
```bash
pytest tests/ -v
```

### 2.2 API 接口集成测试 (非流式)
你可以使用 `curl` 或 Postman 模拟客户端请求。注意在 prompt 中加入敏感信息（如姓名、电话）。

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {"role": "user", "content": "My name is John Doe and my phone number is 123-456-7890. Please remember my name and phone number and repeat them back to me."}
    ],
    "stream": false
  }'
```
**预期结果**：
1. 网关终端日志会显示拦截到了请求，并打印出实际发送给 LLM 的脱敏后 Payload。
2. 实际发送给 LLM 的请求中，"John Doe" 会被替换为 `<PERSON_1>`，电话会被替换为 `<PHONE_NUMBER_1>`。
3. LLM 返回包含占位符的响应。
4. 网关将占位符还原，你最终收到的 JSON 响应中包含真实的 "John Doe" 和 "123-456-7890"。

### 2.3 API 接口集成测试 (流式)
测试流式响应是否能正确缓冲并还原被截断的占位符。

```bash
curl -N -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek/deepseek-chat",
    "messages": [
      {"role": "user", "content": "My name is Alice Smith. Write a short poem about me."}
    ],
    "stream": true
  }'
```
**预期结果**：
终端会以 SSE (Server-Sent Events) 格式逐字打印响应，且响应内容中包含 "Alice Smith" 而不是 `<PERSON_1>`。

---

## 3. Docker 容器化部署

如果你希望在服务器上快速部署：

```bash
# 构建镜像
docker build -t llm-privacy-vault .

# 运行容器 (记得传入 API Key)
docker run -d -p 8000:8000 -e OPENAI_API_KEY="sk-xxx" -e DEFAULT_LANGUAGE="en"  --name privacy-vault llm-privacy-vault
```

---

## 4. 如何在其他项目中应用 (集成指南)

`LLM-Privacy-Vault` 的核心设计是**完全兼容 OpenAI API 格式**。这意味着在任何现有的 AI 应用中，你只需要修改 `Base URL`，即可无缝接入隐私保护功能，**无需修改任何业务代码**。

### 示例：在 LangChain 中集成
```python
from langchain_openai import ChatOpenAI

# 将 base_url 指向你的 LLM-Privacy-Vault 服务地址
llm = ChatOpenAI(
    openai_api_base="http://localhost:8000/v1",
    openai_api_key="dummy-key", # 实际的 key 配置在 Vault 服务端即可
    model_name="deepseek/deepseek-chat"
)

response = llm.invoke("My credit card is 4111-1111-1111-1111, is it safe?")
print(response.content)
```

### 示例：在 OpenAI Python SDK 中集成
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy-key"
)

response = client.chat.completions.create(
    model="deepseek/deepseek-chat",
    messages=[
        {"role": "user", "content": "Contact me at test@example.com"}
    ]
)
print(response.choices[0].message.content)
```

### 架构扩展建议
1. **持久化存储**：当前映射表存储在内存 Dict 中。如果在多实例/K8s环境下部署，请修改 `src/core/state.py`，接入 Redis 以实现分布式状态共享。
2. **自定义 PII 实体**：在 `src/core/anonymizer.py` 中，你可以通过 Presidio 的 `PatternRecognizer` 添加公司特有的敏感词正则（如内部项目代号）。
3. **多语言支持**：目前已内置英文 (`en`) 和中文 (`zh`) 支持，可通过 `.env` 文件中的 `DEFAULT_LANGUAGE` 环境变量进行切换。如需支持更多语言，可在 `src/core/anonymizer.py` 的 `nlp_configuration` 中添加相应的 spaCy 模型。

---

## 5. 高级配置：添加自定义敏感信息过滤 (Custom PII Entities)

默认情况下，网关会拦截姓名、电话、邮箱、信用卡号等通用实体。如果你需要拦截特定格式的内部数据（例如：**中国大陆身份证号**、**内部员工工号**、**车牌号**），你可以通过正则表达式向 Presidio 引擎注册自定义识别器。

### 示例：添加“中国大陆身份证号”过滤

请修改 `src/core/anonymizer.py` 文件：

1. **引入必要的类**：
   在文件顶部添加 `Pattern` 和 `PatternRecognizer` 的导入：
   ```python
   from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
   ```

2. **修改 `_initialize` 方法**：
   在 `self.analyzer = AnalyzerEngine(...)` 初始化之后，添加以下代码：

   ```python
   # 1. 定义正则表达式模式 (中国大陆身份证号 18位)
   id_card_pattern = Pattern(
       name="id_card_pattern",
       regex=r"[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]",
       score=0.85 # 置信度分数 (0.0 - 1.0)
   )

   # 2. 创建自定义识别器
   id_card_recognizer = PatternRecognizer(
       supported_entity="CN_ID_CARD",
       patterns=[id_card_pattern],
       supported_language="zh" # 针对中文模式生效
   )

   # 3. 将识别器注册到 AnalyzerEngine
   self.analyzer.registry.add_recognizer(id_card_recognizer)
   ```

3. **更新 `self.entities` 列表**：
   将你自定义的实体名称 `"CN_ID_CARD"` 加入到需要拦截的列表中：
   ```python
   self.entities = [
       "PERSON",
       "PHONE_NUMBER",
       "EMAIL_ADDRESS",
       # ... 其他默认实体 ...
       "CN_ID_CARD" # <--- 添加你的自定义实体
   ]
   ```

重启服务后，当用户输入包含身份证号的文本时，网关就会自动将其替换为 `<CN_ID_CARD_1>` 进行保护。
