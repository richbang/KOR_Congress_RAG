from dataclasses import dataclass

@dataclass
class QueryConfig:
    model_name: str = 'BAAI/bge-m3'
    device: str = 'cuda'
    vectorstore_path: str = '../vectorDB'
    num_ctx: str = '10000'
    retriever_k: int = 2