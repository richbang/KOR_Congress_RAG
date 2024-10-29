from config import QueryConfig
from query_engine import QueryEngine

def main():
    config = QueryConfig()
    engine = QueryEngine(config)
    
    # 예시 질문들
    questions = [
        "태풍피해에 대한 국가적인 대비책은 어떻게 마련되어야 할까요?",
        # 추가 질문들...
    ]
    
    engine.benchmark(questions)

if __name__ == "__main__":
    main()