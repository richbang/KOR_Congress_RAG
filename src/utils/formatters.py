def format_docs(docs):
    formatted_docs = []
    for doc in docs:
        metadata = doc.metadata
        
        # 키워드 처리
        question_keywords = metadata.get('question_keyword', '').split(',') if metadata.get('question_keyword') else []
        answer_keywords = metadata.get('answer_keyword', '').split(',') if metadata.get('answer_keyword') else []
        
        formatted_doc = {
            '회의 정보': {
                '날짜': metadata.get('date', 'N/A'),
                '회의 이름': metadata.get('meeting_name', 'N/A'),
                '위원회': metadata.get('committee_name', 'N/A'),
                '회의 번호': metadata.get('meeting_number', 'N/A'),
                '세션 번호': metadata.get('session_number', 'N/A'),
                '안건': metadata.get('agenda', 'N/A'),
                '법안': metadata.get('law', 'N/A')
            },
            '논의 정보': {
                'Context': doc.page_content,
                '요약': {
                    'Summary (Question)': metadata.get('context_summary', {}).get('summary_q', 'N/A'),
                    'Summary (Answer)': metadata.get('context_summary', {}).get('summary_a', 'N/A')
                },
                '질문 상세': {
                    '질의자': metadata.get('questioner_name', 'N/A'),
                    '직위': metadata.get('questioner_position', 'N/A'),
                    '내용': metadata.get('question_comment', 'N/A'),
                    '키워드': question_keywords
                },
                '응답 상세': {
                    '응답자': metadata.get('answerer_name', 'N/A'),
                    '직위': metadata.get('answerer_position', 'N/A'),
                    '소속': metadata.get('answerer_affiliation', 'N/A'),
                    '내용': metadata.get('answer_comment', 'N/A'),
                    '키워드': answer_keywords
                }
            }
        }
        formatted_docs.append(formatted_doc)
    return formatted_docs