## Hugging Face模型下载

安装 huggingface_hub

```
pip install -U huggingface_hub
```

配置镜像加速

```
export HF_ENDPOINT=https://hf-mirror.com
```

手动下载模型

```
hf download BAAI/bge-m3 --local-dir ~/.models/bge-m3 --exclude "*.DS_Store"
```

使用模型时，需要指定完整模型路径

MODEL=/Users/xxx/.models/bge-m3