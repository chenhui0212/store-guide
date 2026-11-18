"""图节点执行日志回调
"""
import logging
import time
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)


class NodeLoggingCallback(BaseCallbackHandler):
    """拦截每个节点的执行，记录开始/结束/耗时"""

    def __init__(self) -> None:
        self._start_times: dict[Any, float] = {}

    def on_chain_start(
            self,
            serialized: dict[str, Any] | None,
            inputs: Any,
            *,
            run_id: Any,
            metadata: dict[str, Any] | None = None,
            **kwargs: Any,
    ) -> None:
        node_name = (metadata or {}).get("langgraph_node")
        if not node_name:
            return  # 跳过 graph 层的回调
        self._start_times[run_id] = time.perf_counter()
        logger.info("节点开始: %s", node_name)

    def on_chain_end(
            self,
            outputs: Any,
            *,
            run_id: Any,
            **kwargs: Any,
    ) -> None:
        if run_id not in self._start_times:
            return
        elapsed = time.perf_counter() - self._start_times.pop(run_id)
        logger.info("节点结束，耗时: %.2f 秒", elapsed)

    def on_chain_error(
            self,
            error: BaseException,
            *,
            run_id: Any,
            **kwargs: Any,
    ) -> None:
        # 异常交由全局异常处理器统一记录，这里只清理计时状态
        self._start_times.pop(run_id, None)
