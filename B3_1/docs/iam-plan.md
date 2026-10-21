# B3_1 IAM 최소 권한 적용 계획

**현재 상태:** AWS 계정은 생성됐지만 이 실습용 IAM Role을 아직 만들거나 권한을 적용하지 못했습니다. 신뢰·권한 정책은 `infrastructure/iam/`에 준비했고, 실제 적용과 권한 검증은 남아 있습니다.

## 역할 분리

1. **실습자 접근 주체:** IAM Identity Center 사용자 또는 전용 IAM 사용자 `b3-lab-user`. 루트 계정으로 실습하지 않습니다. `AdministratorAccess`를 연결하지 않습니다.
2. **CloudFormation 실행 역할:** `B3_1CloudFormationRole`. 신뢰 정책의 Principal은 `cloudformation.amazonaws.com`만 허용합니다. 역할 권한은 이 템플릿에 있는 EC2/VPC 작업과 서울 리전으로 제한합니다. 정책 파일은 `infrastructure/iam/cloudformation-*.json`이며 관리자가 `scripts/bootstrap-iam.sh`로 적용할 수 있습니다.
3. **실습자 권한:** `b3-1` 스택의 CloudFormation 생성·조회·업데이트·삭제, 해당 실행 역할에 대한 `iam:PassRole`, EC2/VPC 구성 조회에 필요한 권한만 허용합니다. S3·RDS·Lambda와 같은 실습 외 서비스 권한은 부여하지 않습니다. 키페어 생성은 별도 관리자가 수행합니다.

AWS는 CloudFormation 서비스 역할을 사용하면 실습자에게 EC2 리소스 생성 권한을 직접 줄 필요가 없고, 특정 역할에만 `iam:PassRole`을 허용할 수 있다고 안내합니다. [AWS CloudFormation 최소 권한 가이드](https://docs.aws.amazon.com/prescriptive-guidance/latest/least-privilege-cloudformation/service-roles-for-cloudformation.html)

## 관리자에게 전달할 점검 목록

- 리전 조건: `ap-northeast-2`만 허용.
- CloudFormation 스택 범위: `b3-1` 스택 및 이 스택의 change set만 허용.
- `iam:PassRole` 대상: `B3_1CloudFormationRole` 하나만 허용. 전달 대상 서비스는 CloudFormation으로 제한.
- 실행 역할 서비스 권한: 템플릿에 등장하는 VPC, Subnet, Internet Gateway, Route Table, Security Group, EC2 Instance의 생성·설명·태그·삭제 작업. IAM/S3/RDS 관리 권한은 없음.
- EC2 인스턴스 크기: 계정 혜택을 확인한 뒤 `t3.micro` 또는 실제 무료 대상 micro로 제한.
- EC2 보안 그룹: HTTP 80 공개, SSH 22는 사용자 공인 IP `/32`만.
- 배포 전 IAM Policy Simulator 또는 제한된 테스트 스택으로 동작 확인. 실패한 API 동작만 추가하고 작업 후 불필요한 권한 제거.

현재 실행 역할 정책의 EC2 작업은 필요한 API 동사와 서울 리전으로 제한했지만, 일부 EC2 생성 API의 리소스가 `*`로 남아 있습니다. 실제 IAM 평가 및 CloudFormation 테스트 뒤 가능한 ARN·태그 조건을 추가로 좁혀야 합니다. **이 파일만으로 최소 권한 적용 완료라고 주장하지 않습니다.**

CloudFormation 실행 역할은 스택에 연결된 뒤 다른 작업자도 그 역할로 스택을 조작할 수 있으므로, 실행 역할 권한 자체를 좁게 두는 것이 중요합니다. [AWS CloudFormation 서비스 역할 주의사항](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html)
