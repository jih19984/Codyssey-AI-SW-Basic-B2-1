from __future__ import annotations

import sys
import time
import logging
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from budget_app.exceptions import BudgetAppError

P = ParamSpec("P")
R = TypeVar("R")

# 기록장 하나 만들기
logger = logging.getLogger("budget_app")

# 기록장의 규칙 설정
logging.basicConfig(level=logging.INFO, format="%(message)s")

# 3개의 데코레이터 정의 (전처리 -> 진짜 함수 호출 -> 후처리)

def log_calls(func: Callable[P, R]) -> Callable[P, R]:
    """함수 호출과 종료를 로그로 남긴다."""

    # @wraps(func)는 포장지를 씌워도 wrapper.__name__ 같은 게 원본 함수 이름을 그대로 유지하게 해주는 도구
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        logger.info("[CALL] %s(args=%s, kwargs=%s)", func.__name__, args, kwargs)
        result = func(*args, **kwargs)
        logger.info("[DONE] %s", func.__name__)
        return result

    return wrapper


def measure_time(func: Callable[P, R]) -> Callable[P, R]:
    """함수 실행 시간을 측정해 로그로 남긴다."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info("[TIME] %s: %.4f초", func.__name__, elapsed)
        return result

    return wrapper


def handle_errors(func: Callable[P, R]) -> Callable[P, R]:
    """알려진 예외는 원인+힌트만 출력하고, 종료 코드를 0이 아니게 만든다."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except BudgetAppError as e:
            print(f"[오류] {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"[알 수 없는 오류] {e}", file=sys.stderr)
            sys.exit(1)

    return wrapper

