IMAGE_SUMMARY_PROMPT = """\
请结合图片视觉内容和文档上下文，用中文简要总结图片的主要内容，生成一个精准的中文标题（不要包含额外描述）。
如果图片没有明显的主要内容，上下文亦无有效信息，可以考虑为无意义的标识图片。

图片所在章节：{section_heading}
图片前的文档内容：{context_before_image}
图片后的文档内容：{context_after_image}
"""
