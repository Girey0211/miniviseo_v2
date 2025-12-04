"""
Logger 유틸리티

구조화된 로깅 시스템을 제공합니다.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "agent", log_level: str = None) -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        설정된 Logger 객체
    """
    # 로그 레벨 설정
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 이미 핸들러가 있으면 중복 방지
    if logger.handlers:
        return logger
    
    # 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def log_chain_step(logger: logging.Logger, step: int, action: str, details: dict = None):
    """
    체이닝 단계 로깅
    
    Args:
        logger: Logger 객체
        step: 단계 번호
        action: 수행 액션
        details: 추가 상세 정보
    """
    message = f"[Step {step}] {action}"
    if details:
        message += f" | {details}"
    logger.info(message)


def log_tool_call(logger: logging.Logger, tool_name: str, params: dict, result: any = None):
    """
    툴 호출 로깅
    
    Args:
        logger: Logger 객체
        tool_name: 툴 이름
        params: 파라미터
        result: 결과 (옵션)
    """
    logger.info(f"[Tool Call] {tool_name}")
    logger.debug(f"Parameters: {params}")
    if result is not None:
        logger.debug(f"Result: {result}")
