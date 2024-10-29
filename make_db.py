import json
import os
from typing import List, Dict, Any
from tqdm import tqdm
from dataclasses import dataclass
from pathlib import Path
import logging

from langchain_community.llms import Ollama
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from chromadb import Client
client = Client()  

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class VectorStoreConfig:
    """벡터 저장소 설정을 위한 데이터 클래스"""
    chunk_size: int = 500
    chunk_overlap: int = 50
    batch_size: int = 10000
    model_name: str = 'BAAI/bge-m3'
    vectorstore_path: str = 'vectorDB'
    device: str = 'cuda'

class DocumentProcessor:
    """문서 처리 및 벡터 저장소 생성 담당 클래스"""
    
    def __init__(self, config: VectorStoreConfig):
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.model_name,
            model_kwargs={'device': config.device},
            encode_kwargs={'normalize_embeddings': True}
        )
        
    def create_document_content(self, data: Dict[str, Any]) -> str:
        """문서 본문 생성: 주요 정보만 포함하여 간소화"""
        content_parts = [
            f"Agenda: {data.get('agenda', '')}",
            f"Context: {data.get('context', '')}",
            f"Summary (Question): {data.get('context_summary', {}).get('summary_q', '')}",
            f"Summary (Answer): {data.get('context_summary', {}).get('summary_a', '')}"
        ]
        return '\n'.join(content_parts)

    def create_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """전체 메타데이터 반환"""
        return {
            "date": data.get('date', ''),
            "meeting_name": data.get('meeting_name', ''),
            "committee_name": data.get('committee_name', ''),
            "meeting_number": data.get('meeting_number', ''),
            "session_number": data.get('session_number', ''),
            "agenda": data.get('agenda', ''),
            "law": data.get('law', ''),
            "questioner_name": data.get('questioner_name', ''),
            "questioner_position": data.get('questioner_position', ''),
            "question_comment": data.get('question', {}).get('comment', ''),
            "question_keyword": data.get('question', {}).get('keyword', ''),
            "answerer_name": data.get('answerer_name', ''),
            "answerer_affiliation": data.get('answerer_affiliation', ''),
            "answerer_position": data.get('answerer_position', ''),
            "answer_comment": data.get('answer', {}).get('comment', ''),
            "answer_keyword": data.get('answer', {}).get('keyword', '')
        }

    def process_json_files(self, directory: str) -> List[Document]:
        """JSON 파일을 처리하여 Document 리스트로 반환"""
        documents = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"디렉토리를 찾을 수 없습니다: {directory}")
        
        json_files = list(directory_path.glob('*.json'))
        if not json_files:
            logger.warning(f"처리할 JSON 파일이 없습니다: {directory}")
            return documents

        for json_file in tqdm(json_files, desc="JSON 파일 처리 중"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON 파일 파싱 오류 ({json_file}): {str(e)}")
                        continue
                    
                    try:
                        content = self.create_document_content(data)
                        metadata = self.create_metadata(data)
                        documents.append(Document(page_content=content, metadata=metadata))
                    except KeyError as e:
                        logger.error(f"필수 데이터 필드 누락 ({json_file}): {str(e)}")
                        continue
                    except Exception as e:
                        logger.error(f"문서 처리 중 오류 발생 ({json_file}): {str(e)}")
                        continue
                    
            except PermissionError:
                logger.error(f"파일 접근 권한이 없습니다: {json_file}")
                continue
            except FileNotFoundError:
                logger.error(f"파일을 찾을 수 없습니다: {json_file}")
                continue
            except Exception as e:
                logger.error(f"예상치 못한 오류 발생 ({json_file}): {str(e)}")
                continue

        if not documents:
            logger.warning("처리된 문서가 없습니다.")
        else:
            logger.info(f"총 {len(documents)}개의 문서가 처리되었습니다.")

        return documents

    def create_vector_store(self, documents: List[Document]):
        """문서를 벡터 저장소에 배치 단위로 추가"""
        docs = self.text_splitter.split_documents(documents)
        
        # Ensure vector store directory exists
        os.makedirs(self.config.vectorstore_path, exist_ok=True)
        
        total_batches = (len(docs) + self.config.batch_size - 1) // self.config.batch_size
        
        # Process in batches with progress bar
        with tqdm(total=total_batches, desc="벡터 저장소 생성 중") as pbar:
            for i in range(0, len(docs), self.config.batch_size):
                batch = docs[i:i + self.config.batch_size]
                
                try:
                    vectorstore = Chroma.from_documents(
                        batch,
                        self.embeddings,
                        persist_directory=self.config.vectorstore_path
                    )
                    
                    # Update progress bar
                    pbar.update(1)
                    pbar.set_postfix({
                        "현재 배치": f"{i//self.config.batch_size + 1}/{total_batches}",
                        "처리된 문서": f"{min(i + self.config.batch_size, len(docs))}/{len(docs)}"
                    })
                    
                except Exception as e:
                    logger.error(f"배치 처리 중 오류 발생 (배치 {i//self.config.batch_size + 1}): {str(e)}")
                    continue

def main():
    """Main 실행 함수"""
    # Initialize LLM
    llm = Ollama(model="llama3.1:70b")
    
    # Configure vector store settings
    config = VectorStoreConfig()
    
    # Initialize processor
    processor = DocumentProcessor(config)
    
    try:
        # Process documents
        logger.info("문서 처리를 시작합니다...")
        documents = processor.process_json_files('./dataset/processed/')
        
        # Create vector store
        logger.info("벡터 저장소를 생성합니다...")
        processor.create_vector_store(documents)
        
        logger.info("벡터 저장소 생성이 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"오류가 발생했습니다: {e}")
        raise

if __name__ == "__main__":
    main()
