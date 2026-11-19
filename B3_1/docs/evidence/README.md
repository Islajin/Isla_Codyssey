# B3_1 서울 리전 증빙

실제 서울(`ap-northeast-2`) 배포·조회·정리 결과를 저장했습니다. JSON은 AWS API 조회에서 뽑은 주요 값과 민감 정보 마스킹 결과이며, PNG는 해당 기록을 읽기 좋게 표시한 캡처입니다. 외부 응답의 원문은 `verification.txt`입니다.

| 파일 | 반드시 보여줄 내용 |
| --- | --- |
| `external-access.png` | 외부에서 실제 퍼블릭 IP의 `/health` 호출, HTTP 200과 본문 `OK` |
| `site.png` | 실제 퍼블릭 IP로 열린 포트폴리오 전체 페이지. 스크롤 진입 전 애니메이션 때문에 일부 구간은 공백으로 보일 수 있음 |
| `network.png` | VPC, Public Subnet, IGW 연결과 `0.0.0.0/0 → IGW` 경로 |
| `instance-and-server.png` | EC2 `running`, 퍼블릭 IP, 8 GiB 암호화 EBS |
| `server-verification.png` | 외부 `/health`, 내부 `localhost` 200, 인터넷 아웃바운드 200 |
| `security-group.png` | HTTP 80 `0.0.0.0/0`, SSH 22 학습자 IPv4 `/32`, 전체 포트 공개 없음 |
| `iam.png` | 실습 IAM 사용자의 인라인 정책. 관리형 정책 미연결은 `iam-attached-policies.json`에 기록 |
| `cleanup.png` | 스택과 과금 가능 리소스의 삭제/해제 조회 결과 |
| `verification.txt` | 검증 명령의 원문 출력과 UTC 시각 |
| `cleanup-audit.json` | 스택 삭제 완료 대기와 EC2·EBS·네트워크 리소스 재조회 요약 |

AWS 계정 ID, 개인 SSH IP, 키 파일은 공개 저장소에 올리지 않았습니다. IAM 사용자 이름은 실습 식별자로 문서에 표기했습니다.
