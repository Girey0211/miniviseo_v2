"""
Memory Storage

메모리 데이터를 저장하고 관리합니다.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class MemoryStorage:
    """메모리 저장소 클래스"""
    
    def __init__(self, storage_path: str = None):
        """
        초기화
        
        Args:
            storage_path: 저장 파일 경로
        """
        if storage_path is None:
            storage_path = os.getenv("MEMORY_FILE", "data/memory.json")
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 파일이 없으면 초기화
        if not self.storage_path.exists():
            self._initialize_storage()
    
    def _initialize_storage(self):
        """저장소 초기화"""
        initial_data = {
            "session_memory": [],
            "long_term_memory": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        }
        self._save(initial_data)
    
    def _load(self) -> Dict[str, Any]:
        """저장소에서 데이터 로드"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"메모리 로드 오류: {e}")
            return {}
    
    def _save(self, data: Dict[str, Any]):
        """저장소에 데이터 저장"""
        try:
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"메모리 저장 오류: {e}")
    
    def get_session_memory(self) -> list:
        """세션 메모리 가져오기"""
        data = self._load()
        return data.get("session_memory", [])
    
    def add_session_memory(self, message: Dict[str, Any]):
        """세션 메모리에 메시지 추가"""
        data = self._load()
        if "session_memory" not in data:
            data["session_memory"] = []
        data["session_memory"].append(message)
        self._save(data)
    
    def clear_session_memory(self):
        """세션 메모리 초기화"""
        data = self._load()
        data["session_memory"] = []
        self._save(data)
    
    def get_long_term_memory(self, key: str = None) -> Any:
        """
        장기 메모리 가져오기
        
        Args:
            key: 특정 키 (None이면 전체 반환)
        
        Returns:
            메모리 값
        """
        data = self._load()
        long_term = data.get("long_term_memory", {})
        
        if key is None:
            return long_term
        return long_term.get(key)
    
    def set_long_term_memory(self, key: str, value: Any):
        """
        장기 메모리 설정
        
        Args:
            key: 키
            value: 값
        """
        data = self._load()
        if "long_term_memory" not in data:
            data["long_term_memory"] = {}
        data["long_term_memory"][key] = value
        self._save(data)
    
    def remove_long_term_memory(self, key: str):
        """
        장기 메모리 삭제
        
        Args:
            key: 삭제할 키
        """
        data = self._load()
        if "long_term_memory" in data and key in data["long_term_memory"]:
            del data["long_term_memory"][key]
            self._save(data)
