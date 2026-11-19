# B3_1 서울 리전 리소스 정리 체크리스트

2026-11-20 08:50:53 KST에 서울 리전(`ap-northeast-2`)에서 실습 리소스 정리를 조회했습니다. [정리 결과 캡처](evidence/cleanup.png)와 [원본 요약](evidence/cleanup-audit.json)을 함께 제출합니다.

| 확인 항목 | 리소스 ID | 상태 | 조회/삭제 근거 |
| --- | --- | --- | --- |
| CloudFormation `b3-1` 스택 | `b3-1` | 삭제 완료 | `stack-delete-complete` waiter 성공 |
| EC2 인스턴스 | `i-09392c70bef4969d4` | `terminated` | `describe-instances` 실제 조회 |
| EBS 루트 볼륨 | `vol-04be68ddecff6a2fd` | 삭제 완료 | `describe-volumes`에서 NotFound |
| Elastic IP | 생성하지 않음 | 할당 0개 | 서울 `describe-addresses` 결과 빈 배열 |
| Internet Gateway | `igw-07b5061a24304467c` | 삭제 완료 | `describe-internet-gateways`에서 NotFound |
| Public Subnet | `subnet-0429c7625e75e9742` | 삭제 완료 | `describe-subnets`에서 NotFound |
| Public Route Table | `rtb-02ea675e255d2f7e7` | 삭제 완료 | `describe-route-tables`에서 NotFound |
| Security Group | `sg-08056ea441630f180` | 삭제 완료 | `describe-security-groups`에서 NotFound |
| VPC | `vpc-0a9cc056b45cbc761` | 삭제 완료 | `describe-vpcs`에서 NotFound |
| EC2 키페어 | `B3_1-20261120` | 삭제 완료 | `delete-key-pair` 성공 후 `describe-key-pairs`에서 NotFound |
| NAT Gateway | 생성하지 않음 | B3_1 태그 대상 0개 | `describe-nat-gateways` 조회 |
| ELB·ALB / RDS | 생성하지 않음 | 해당 없음 | CloudFormation 템플릿에 해당 리소스 없음 |
| IAM 실습 사용자 `B3_1Learner` | 계정 관리 리소스 | 남아 있음 | 콘솔 접근용 사용자. 사용 종료 후 계정 소유자가 액세스 키와 함께 삭제해야 함 |
| Billing Dashboard | 계정 소유자 화면 | 미확인 | 이 IAM 사용자에는 Billing 조회 권한이 없음. 청구 화면은 계정 소유자가 확인 |

정리 순서: 접속·구성 캡처 저장 → CloudFormation 스택 삭제 및 완료 대기 → EC2/EBS/EIP/IGW/VPC 조회 → 스택 밖 키페어 삭제. IAM 사용자와 액세스 키는 과금 대상 인프라가 아니지만, 실습 종료 후 계정 소유자가 삭제해야 합니다. Billing 표시에는 지연이 있을 수 있으므로 계정 소유자 화면에서 최종 확인이 필요합니다.
