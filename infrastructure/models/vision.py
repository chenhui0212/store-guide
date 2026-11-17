from langchain_openai import ChatOpenAI

import core.config as config

vlm = ChatOpenAI(
    model=config.DASHSCOPE_VLM_MODEL,
    api_key=config.DASHSCOPE_API_KEY,
    base_url=config.DASHSCOPE_API_BASE or None,
    temperature=0,
)
