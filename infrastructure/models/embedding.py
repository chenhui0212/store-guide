from pymilvus.model.hybrid import BGEM3EmbeddingFunction

import core.config as config

embed_func = BGEM3EmbeddingFunction(
    model_name=config.EMBEDDING_MODEL,
    batch_size=config.EMBEDDING_BATCH_SIZE,
    device=config.EMBEDDING_DEVICE,
    use_fp16=config.EMBEDDING_USE_FP16,
)
