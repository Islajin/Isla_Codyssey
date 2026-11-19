# B3_1 서울 리전 트러블슈팅

## 실제 배포 사례: Nginx 준비 전 reload 실패

| 항목 | 서울 실습 기록 |
| --- | --- |
| 증상 | CloudFormation 스택 생성 직후 `scripts/deploy.sh`의 `systemctl reload nginx`가 실패했다. |
| 원인 가설 | EC2 사용자 데이터의 Nginx 설치·시작이 끝나기 전에 배포 스크립트가 reload를 호출했다. |
| 검증 | SSH로 EC2에 접속해 `journalctl`을 확인했다. `Unit cannot be reloaded because it is inactive`가 기록됐고, 그 직후 Nginx가 시작됐다. 이 순서가 준비 완료 전 reload라는 가설과 일치했다. |
| 조치 | `scripts/deploy.sh`가 `systemctl is-active --quiet nginx`와 `/usr/share/nginx/html/health` 파일 존재를 모두 확인한 뒤 배포를 계속하도록 준비 조건을 수정했다. |
| 결과 | 수정한 스크립트를 재실행해 배포 성공. 외부 `GET /health`에서 HTTP 200과 `OK`, 인스턴스 내부 `curl http://localhost`에서 HTTP 200을 확인했다. [검증 원문](evidence/verification.txt)과 [외부 응답 캡처](evidence/external-access.png)에 남겼다. |
| 재발 방지 | 비동기 초기 설정 뒤에는 고정 대기 시간에 의존하지 않고 서비스 활성 상태와 필수 파일 존재를 확인한다. 실패 시 `journalctl`과 cloud-init 로그를 먼저 조회한다. |

이 오류는 네트워크나 IAM 권한 문제가 아니라 배포 순서 문제였다.
