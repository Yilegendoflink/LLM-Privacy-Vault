from langchain_openai import ChatOpenAI

# 将 base_url 指向你的 LLM-Privacy-Vault 服务地址
llm = ChatOpenAI(
    openai_api_base="http://localhost:8000/v1",
    openai_api_key="dummy-key", # 实际的 key 配置在 Vault 服务端即可
    model_name="deepseek/deepseek-chat"
)

response = llm.invoke("My name is Luke Stratry and my credit card is 4111-1111-1111-1111, now tell me my name and credit card number")
print(response.content)