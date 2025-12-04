"""
Web Search Module

웹 검색 기능을 제공합니다.
"""

import json
import requests
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from src.utils.logger import setup_logger
from src.utils.openai_client import get_openai_client
from src.prompts.templates import WEB_SEARCH_QUERY_PROMPT, format_prompt
from src.prompts.system import get_system_prompt

logger = setup_logger("web_search")


class WebSearch:
    """웹 검색 클래스"""
    
    def __init__(self):
        """초기화"""
        self.openai_client = get_openai_client()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        logger.info("Web Search 모듈 초기화 완료")
    
    def generate_query(self, user_input: str) -> Dict[str, Any]:
        """
        검색어 생성
        
        Args:
            user_input: 사용자 입력
        
        Returns:
            검색어 정보
            {
                "query": str,
                "filters": dict
            }
        """
        try:
            from datetime import datetime
            
            # 현재 날짜 및 시간
            current_date = datetime.now().strftime("%Y년 %m월 %d일 (%A)")
            
            prompt = format_prompt(
                WEB_SEARCH_QUERY_PROMPT, 
                user_input=user_input,
                current_date=current_date
            )
            result = self.openai_client.query_with_json(
                system_prompt=get_system_prompt(),
                user_message=prompt
            )
            
            if result:
                logger.info(f"검색어 생성: {result.get('query')}")
                return result
            else:
                logger.warning("검색어 생성 실패, 원본 입력 사용")
                return {"query": user_input, "filters": {}}
                
        except Exception as e:
            logger.error(f"검색어 생성 오류: {e}")
            return {"query": user_input, "filters": {}}
    
    def search(self, query: str) -> List[Dict[str, str]]:
        """
        웹 검색 실행
        
        Args:
            query: 검색어
        
        Returns:
            검색 결과 리스트
            [
                {"title": "제목", "snippet": "내용", "url": "주소"}
            ]
        """
        logger.info(f"웹 검색 실행: {query}")
        
        try:
            # DuckDuckGo HTML 검색
            url = "https://html.duckduckgo.com/html/"
            data = {'q': query}
            
            response = requests.post(url, data=data, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(response.text, 'lxml')
            
            results = []
            # 검색 결과 추출
            for result_div in soup.find_all('div', class_='result')[:5]:  # 상위 5개
                try:
                    # 제목과 링크
                    title_tag = result_div.find('a', class_='result__a')
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href', '')
                    
                    # 스니펫
                    snippet_tag = result_div.find('a', class_='result__snippet')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                    
                    if title and link:
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": link
                        })
                        
                except Exception as e:
                    logger.debug(f"결과 파싱 오류: {e}")
                    continue
            
            logger.info(f"검색 결과 {len(results)}개 발견")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"검색 요청 오류: {e}")
            # Fallback: 모의 데이터
            return self._get_fallback_results(query)
        except Exception as e:
            logger.error(f"검색 처리 오류: {e}")
            return self._get_fallback_results(query)
    
    def _get_fallback_results(self, query: str) -> List[Dict[str, str]]:
        """
        Fallback 검색 결과 (네트워크 오류 시)
        
        Args:
            query: 검색어
        
        Returns:
            모의 검색 결과
        """
        logger.warning("Fallback 검색 결과 사용")
        return [
            {
                "title": f"{query} 관련 정보",
                "snippet": f"{query}에 대한 정보를 찾을 수 없습니다. 인터넷 연결을 확인해주세요.",
                "url": "https://duckduckgo.com/?q=" + query.replace(" ", "+")
            }
        ]
    
    def summarize_results(self, results: List[Dict[str, str]], original_query: str) -> str:
        """
        검색 결과 요약 및 정보 추출
        
        Args:
            results: 검색 결과 리스트
            original_query: 원본 검색어
        
        Returns:
            요약된 텍스트
        """
        if not results:
            return "검색 결과가 없습니다."
        
        # 검색 결과를 텍스트로 변환
        results_text = ""
        for i, res in enumerate(results[:5]):
            results_text += f"{i+1}. {res['title']}\n   {res['snippet']}\n   출처: {res['url']}\n\n"
        
        # LLM을 사용하여 정보 추출 및 요약
        prompt = f"""다음 검색 결과를 바탕으로 '{original_query}'에 대한 답변을 작성해주세요.

검색 결과:
{results_text}

## 요구사항
1. 검색 결과에서 핵심 정보를 추출하세요
2. 사용자 질문에 직접 답변하세요
3. 출처를 명시하세요
4. 정보가 불충분하면 그 사실을 명시하세요

답변:"""
        
        try:
            summary = self.openai_client.simple_query(
                system_prompt="당신은 웹 검색 결과를 분석하여 필요한 정보만 추출하는 전문가입니다.",
                user_message=prompt
            )
            logger.info("검색 결과 요약 완료")
            return summary
        except Exception as e:
            logger.error(f"결과 요약 오류: {e}")
            return results_text
