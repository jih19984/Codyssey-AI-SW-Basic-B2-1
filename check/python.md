## __future__
다음 버전의 모듈을 미리 가져와서 쓸 수 있다.

```python
from __future__ import annotations
# 타입힌트를 문자열로 평가되게 만들어준다.
# 모든 annotation이 자동으로 지연평가된다.
```

## data_classes
데이터를 담는 용도의 클래스를 간편하게 만들어주는 표준 라이브러리

## Any
```python
from typing import Any
# 어떤 타입이든 다 허용하고 싶을 때 쓰는 특수한 타입
```

## super()
부모 클래스를 가리키는 것으로
```
super().__init__(message)는 부모 클래스의 __init__을 호출하라는 뜻이다.
```

## TypeVar
"타입 변수"륾 만드는 도구. 

## ParamSpec
함수의 파라미터 전체 시그니처를 통째로 캡처하는 도구.

## Callable
호출 가능한 객체로, 함수, 메서드, 람다처럼 ()를 붙여서 호출할 수 있는 것들을 타입으로 표현할 때 쓴다.