# fasapi-template

fastapi service layer

원칙

- router는 비즈니스 로직을 포함하지 않는다.
- router는 단순히 요청을 받아 서비스 계층으로 전달하는 역할만 한다.
- 서비스 계층은 비즈니스 로직을 포함한다.
- 서비스 계층은 예외를 발생시킨다.
- router는 서비스 계층에서 발생한 예외를 처리한다.
- 모델은 데이터베이스 테이블을 정의한다.
- 반드시 모델은 XxxModel 처럼 Model 로 끝나야 한다.
