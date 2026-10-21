# B3_1 리소스 정리 체크리스트

**실습 날짜:** 2026-10-21, 시드니 리전(`ap-southeast-2`). 외부 접속 증빙을 저장한 뒤 `./scripts/cleanup.sh b3-operator`로 CloudFormation 스택을 삭제했습니다. 아래 조회는 삭제 명령 완료 후 수행했습니다.

| 확인 항목 | 상태 | 실제 확인 근거 |
| --- | --- | --- |
| CloudFormation `b3-1` 스택 | 삭제 완료 | `describe-stacks` → `Stack with id b3-1 does not exist` |
| EC2 `i-06ec8cc985b2829f4` | 종료 완료 | `describe-instances` → `terminated` |
| 루트 EBS `vol-008ac4ec2e5550c68` | 삭제 완료 | `describe-volumes` → `InvalidVolume.NotFound` |
| 자동 공인 IPv4 `15.134.214.202` | 인스턴스 종료로 해제 | EC2 `terminated`; 별도 Elastic IP를 할당하지 않음 |
| Elastic IP | 사용하지 않음 | 프로젝트 태그 `B3_1`의 `describe-addresses` 결과 `[]` |
| IGW `igw-09a9a4f5ecbf01e2f` | 삭제 완료 | `describe-internet-gateways` → `InvalidInternetGatewayID.NotFound` |
| Subnet `subnet-0927e2efc6d750f46` | 삭제 완료 | `describe-subnets` → `InvalidSubnetID.NotFound` |
| Route Table `rtb-0eaa52e51d8191361` | 삭제 완료 | `describe-route-tables` → `InvalidRouteTableID.NotFound` |
| SG `sg-04bda3f717d5c8265` | 삭제 완료 | `describe-security-groups` → `InvalidGroup.NotFound` |
| VPC `vpc-0f1a61c468d16a152` | 삭제 완료 | `describe-vpcs` → `InvalidVpcID.NotFound` |
| EC2 키페어 `B3_1-20261021` | 삭제 완료 | `delete-key-pair` → `Return: true`, 재조회 → `InvalidKeyPair.NotFound`; 로컬 `.pem`도 삭제 |
| IAM 실습 역할 2개 | 삭제 완료 | `B3_1OperatorRole`·`B3_1CloudFormationRole` 재조회 → `NoSuchEntity` |
| NAT Gateway / ELB·ALB / RDS | 생성하지 않음 | CloudFormation 템플릿과 스택 리소스 목록에 없음 |
| Billing Dashboard | 청구 확정 전 | AWS 사용량·청구 정보에는 반영 지연이 있을 수 있음. 무료 플랜과 잔여 크레딧은 배포 전에 확인함. |

이 표는 **B3_1 실습으로 만든 리소스**를 추적합니다. 계정의 다른 프로젝트가 만든 리소스는 삭제하지 않았습니다. 스크린샷의 과거 URL은 정리 후 더 이상 활성 서비스가 아닙니다.
