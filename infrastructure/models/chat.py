from langchain_deepseek import ChatDeepSeek

import core.config as config

chat_llm = ChatDeepSeek(
    model=config.CHAT_MODEL,
    temperature=0,
    extra_body={"thinking": {"type": "disabled"}},
)
