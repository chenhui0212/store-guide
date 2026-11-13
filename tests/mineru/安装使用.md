## MinerU

[快速入门](https://opendatalab.github.io/MinerU/zh/quick_start/)

激活环境，安装 4.x 基础包，额外参考[扩展模块安装](https://opendatalab.github.io/MinerU/zh/quick_start/extension_modules/)

```
pip install -U "mineru>=4.0,<5"
```

手动下载模型

```
mineru-models-download -s modelscope --tier standard
```

无状态解析文档

```
mineru-kit parse document.pdf -o document.md --tier standard
```

[Python SDK](https://opendatalab.github.io/MinerU/zh/usage/sdk_api/)

本地解析

```
from pathlib import Path
from mineru.parser import parse

result = parse("document.pdf", tier="standard")
Path("document.md").write_text(result.markdown(), encoding="utf-8")
```
