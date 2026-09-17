"""python -m budget_app 진입점."""
from __future__ import annotations

import sys

from budget_app.cli import main

# 겉보기에는 sys.exit(0) 한 줄 이지만,
# 먼저 build_parser(), parse_args(), dispatch(args)까지 다 실행되고, 그 결과로 정수를 리턴
if __name__ == "__main__":
    sys.exit(main())
