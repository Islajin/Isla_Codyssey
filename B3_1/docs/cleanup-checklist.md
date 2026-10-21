# B3_1 리소스 정리 체크리스트

**현재 상태 (2026-10-21): AWS 계정은 있지만 이 프로젝트의 리소스를 아직 생성하지 않았습니다. 따라서 실습 후 삭제 완료라고 표시하지 않습니다.**

실제 배포 후 증빙을 저장하고 실습을 마칠 때 `./scripts/cleanup.sh b3-lab`을 실행합니다. 그 다음 서울 리전에서 아래를 확인하고 날짜, 리소스 ID, 확인 명령 또는 화면을 기록합니다.

| 확인 항목 | 상태 | 확인 근거 |
| --- | --- | --- |
| CloudFormation `b3-1` 스택 | 미생성 | 배포 후 삭제 시 `DELETE_COMPLETE` 또는 스택 없음 확인 |
| EC2 인스턴스 | 미생성 | `Terminated` 또는 목록에서 제거 확인 |
| EBS 루트 볼륨과 미사용 볼륨 | 미생성 | 인스턴스의 볼륨 ID가 삭제됐는지 확인 |
| 퍼블릭 IPv4 / Elastic IP | 미생성 | 자동 공인 IP 해제, 할당한 EIP가 있다면 `Release` 확인 |
| Internet Gateway | 미생성 | VPC에서 분리 및 삭제 확인 |
| Public Subnet / Route Table / Security Group | 미생성 | 스택 삭제 후 잔존 리소스 확인 |
| VPC | 미생성 | 프로젝트 VPC 삭제 확인 |
| NAT Gateway / ELB·ALB / RDS | 사용하지 않음 | 프로젝트에서는 생성하지 않음. 계정에서 별도 생성 여부 확인 |
| Billing Dashboard | 미확인 | 실습 후 사용량·청구 항목 확인 |

CloudFormation 삭제가 실패하면 `describe-stack-events`로 어떤 리소스가 남았는지 확인하고, 종속 리소스를 해결한 뒤 다시 삭제합니다. 체크리스트에 실제 확인 결과를 남길 때까지 완료로 표시하지 않습니다.
