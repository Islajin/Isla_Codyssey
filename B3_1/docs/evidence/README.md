# 외부 접속 증빙

AWS CLI 인증 후 서울 리전 호출이 계정의 서비스 제어 정책(SCP)에서 거부됨을 확인했습니다. 실제 배포 전이라 접속 스크린샷은 생성되지 않았습니다. 이 폴더에 제출용 가짜 이미지를 넣지 않습니다.

배포 후 `./scripts/verify.sh b3-lab /path/to/key.pem`으로 실제 명령 결과를 확인하고, 브라우저에서 `http://<PUBLIC_IP>/health`를 연 화면 또는 외부 컴퓨터의 `curl -i` 결과를 캡처해 `external-access.png`로 저장하세요. URL/IP와 캡처 일시를 `README.md`의 배포 결과 표에 기록하세요.
