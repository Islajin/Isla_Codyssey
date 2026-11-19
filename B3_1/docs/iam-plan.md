# B3_1 서울 리전 IAM 설계 및 검증

> 2026-11-20: 새 계정에서 `B3_1Learner`를 생성하고 서울 리전 배포·조회·정리를 이 비루트 IAM 사용자 자격으로 수행했습니다.

## 과제용 IAM 사용자와 허용 범위

| 주체 | 목적 | 허용할 주요 작업 |
| --- | --- | --- |
| 계정 소유자 | 가입 직후 초기 설정 | 같은 계정 안에 비루트 IAM 사용자 1명 생성 및 정책 연결에만 사용 |
| `B3_1Learner` | 실습 배포·조회·삭제 | 서울 리전의 CloudFormation 스택 작업, EC2/VPC/SG 구성, EC2 키페어 관리, Amazon Linux AMI 공용 SSM 파라미터 조회 |

실습 사용자에는 `AdministratorAccess`를 연결하지 않습니다. S3, RDS, IAM 관리 등 과제와 무관한 서비스의 권한을 부여하지 않습니다. 정책의 일부 EC2·CloudFormation 동작은 서비스 API 특성상 `Resource: "*"`를 사용하지만, 작업 종류와 `aws:RequestedRegion=ap-northeast-2` 조건으로 범위를 줄였습니다. 이를 **완전한 리소스 단위 최소 권한**으로 과장하지 않습니다. 정책 원본은 [`../infrastructure/iam/learner-permissions.json`](../infrastructure/iam/learner-permissions.json)입니다.

## 실제 검증 기록

| 확인 항목 | 결과 |
| --- | --- |
| `B3_1Learner`의 정책 조회 | 실제 인라인 정책을 [`evidence/iam-user-policy.json`](evidence/iam-user-policy.json)에 저장 |
| 루트가 아닌 IAM 사용자로 CloudFormation 배포 | `sts get-caller-identity`의 IAM 사용자 ARN 확인 후 `b3-1` 스택 생성·검증·삭제 |
| `AdministratorAccess` 미연결 | 연결된 관리형 정책 목록이 빈 배열 `[]`: [`evidence/iam-attached-policies.json`](evidence/iam-attached-policies.json) |
| 타 서비스 권한 없음 | 인라인 정책은 서울 EC2/VPC, CloudFormation, 공용 AMI 조회 및 본인 암호 변경으로 제한. S3/RDS 관리 작업 없음 |
| IAM CLI 캡처 | [`evidence/iam.png`](evidence/iam.png) |

선택적으로 CloudFormation 서비스 역할을 분리할 수도 있도록 [`../scripts/bootstrap-operator.sh`](../scripts/bootstrap-operator.sh)와 [`../scripts/bootstrap-iam.sh`](../scripts/bootstrap-iam.sh)를 남겨 두었습니다. 이 추가 역할을 실제로 생성하거나 사용하지 않았다면 제출물에서 사용했다고 주장하지 않습니다. [AWS IAM 최소 권한 원칙](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
