from langchain_community.llms import Ollama
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnableMap, RunnablePassthrough

from config import QueryConfig
from utils.prompt_template import get_prompt_template
from utils.formatters import format_docs

class QueryEngine:
    def __init__(self, config: QueryConfig):
        self.config = config
        self.llm = Ollama(model="llama3.1:70b", num_ctx=config.num_ctx)
        self.vectorstore = self._load_vectorstore()
        self.rag_chain = self._create_rag_chain()

    def _load_vectorstore(self):
        embeddings = HuggingFaceEmbeddings(
            model_name=self.config.model_name,
            model_kwargs={'device': self.config.device},
            encode_kwargs={'normalize_embeddings': True}
        )
        return Chroma(
            persist_directory=self.config.vectorstore_path,
            embedding_function=embeddings
        )

    def _create_rag_chain(self):
        retriever = self.vectorstore.as_retriever(
            search_kwargs={'k': self.config.retriever_k}
        )
        prompt = get_prompt_template()
        
        return (
            RunnableMap({
                "context": retriever | format_docs,
                "question": RunnablePassthrough()
            })
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def query(self, question: str) -> str:
        return self.rag_chain.invoke(question)

    def benchmark(self, questions: list, output_file: str = "benchmark_results.txt"):
        results = []
        for query in questions:
            answer = self.query(query)
            results.append((query, answer))
            print(f"Query: {query}")
            print("---Answer---")
            print(answer)
            print("-" * 50)
            print('\n')

        with open(output_file, "w", encoding="utf-8") as f:
            for query, answer in results:
                f.write(f"Query: {query}\nAnswer: {answer}\n{'-'*50}\n")

        print(f"벤치마킹이 완료되었습니다. 결과가 '{output_file}'에 저장되었습니다.")