# B3_1 IAM 권한 적용과 실습 기록

**2026-10-21 시드니 실습:** 계정 기본 `AccountFullAccessRole`로 전용 역할 두 개를 생성하고 EC2 키페어를 준비했습니다. 실제 CloudFormation 배포·검증·스택 삭제는 **`B3_1OperatorRole`**의 임시 세션으로 실행했습니다. 루트 계정을 사용하지 않았고 실습 역할에는 `AdministratorAccess`를 연결하지 않았습니다. 실습 종료 후 전용 역할 두 개와 키페어를 삭제했습니다.

## 역할 분리

1. **계정 기본 접근 역할:** `AccountFullAccessRole`은 실습 역할과 SSH 키를 준비할 때만 사용했습니다. CloudFormation 배포 명령에는 사용하지 않았습니다.
2. **실습 작업 역할:** `B3_1OperatorRole`은 `scripts/bootstrap-operator.sh`가 생성합니다. 시드니 리전의 CloudFormation 배포·조회·삭제, EC2/VPC 조회, 특정 `B3_1CloudFormationRole`을 CloudFormation에 전달하는 `iam:PassRole`만 허용합니다. S3·RDS·Lambda·IAM 관리 권한은 없습니다.
3. **CloudFormation 실행 역할:** `B3_1CloudFormationRole`은 CloudFormation 서비스만 맡을 수 있습니다. 정책은 시드니 리전의 EC2/VPC 구성 작업과 Amazon Linux 공용 AMI 파라미터 조회만 허용합니다. `scripts/bootstrap-iam.sh`와 `infrastructure/iam/`에 정의했습니다.

AWS는 CloudFormation 서비스 역할을 사용하면 실습자에게 EC2 리소스 생성 권한을 직접 줄 필요가 없고, 특정 역할에만 `iam:PassRole`을 허용할 수 있다고 안내합니다. [AWS CloudFormation 최소 권한 가이드](https://docs.aws.amazon.com/prescriptive-guidance/latest/least-privilege-cloudformation/service-roles-for-cloudformation.html)

## 관리자에게 전달할 점검 목록

- 리전 조건: `ap-southeast-2`만 허용. 과제의 서울 리전 조건은 별개로 미충족.
- CloudFormation API 작업은 필요한 동사로 제한했지만 리소스는 `*`입니다. 새 스택 ARN이 배포 전에 없고 change set ARN도 실행 중 생성되므로 완전한 스택 단위 제한은 아직 적용하지 않았습니다.
- `iam:PassRole` 대상: `B3_1CloudFormationRole` 하나만 허용. 전달 대상 서비스는 CloudFormation으로 제한.
- 실행 역할 서비스 권한: 템플릿에 등장하는 VPC, Subnet, Internet Gateway, Route Table, Security Group, EC2 Instance의 생성·설명·태그·삭제 작업. IAM/S3/RDS 관리 권한은 없음.
- EC2 인스턴스 크기: 계정 혜택을 확인한 뒤 `t3.micro` 또는 실제 무료 대상 micro로 제한.
- EC2 보안 그룹: HTTP 80 공개, SSH 22는 사용자 공인 IP `/32`만.
- 배포 전 IAM Policy Simulator 또는 제한된 테스트 스택으로 동작 확인. 실패한 API 동작만 추가하고 작업 후 불필요한 권한 제거.

두 실습 역할은 실제 시드니 배포와 삭제에 사용할 수 있음을 확인했습니다. 다만 CloudFormation 작업 역할과 EC2 실행 역할 정책의 일부 `Resource`가 `*`여서 **완전한 리소스 단위 최소권한이라고 주장하지 않습니다.** 역할에는 AdministratorAccess를 붙이지 않았고 서비스·API·리전·PassRole 대상을 좁혔습니다. 재실습한다면 생성 단계와 삭제 단계의 정책을 나누고, 가능한 ARN·태그 조건을 추가로 제한할 수 있습니다.

CloudFormation 실행 역할은 스택에 연결된 뒤 다른 작업자도 그 역할로 스택을 조작할 수 있으므로, 실행 역할 권한 자체를 좁게 두는 것이 중요합니다. [AWS CloudFormation 서비스 역할 주의사항](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html)
