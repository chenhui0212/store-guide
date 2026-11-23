import json
from pathlib import Path

from langchain_core.documents import Document


def save_chunks(chunks: list[Document], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            record = {
                "page_content": chunk.page_content,
                "metadata": chunk.metadata,
            }
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_chunks(path: Path) -> list[Document]:
    with path.open(encoding="utf-8") as file:
        return [
            Document(**json.loads(line))
            for line in file
            if line.strip()
        ]
