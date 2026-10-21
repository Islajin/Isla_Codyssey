# 외부 접속 증빙

2026-10-21 시드니 리전(`ap-southeast-2`)에서 실제 배포하고, AWS CloudShell에서 `curl -i --max-time 10 http://15.134.214.202/health`를 실행해 `HTTP/1.1 200 OK`와 본문 `OK`를 확인했습니다. 실제 화면은 [`external-access.png`](external-access.png), 로컬 검증 스크립트의 출력은 [`verification.txt`](verification.txt)입니다.

검증 뒤 과제의 정리 조건에 따라 EC2와 VPC를 삭제했습니다. 이 URL은 실습 당시의 접속 정보이며 현재 활성 웹사이트가 아닙니다. 과제에 명시된 서울 리전과 다르므로 제출 전 담당자의 허용 여부를 확인해야 합니다.
