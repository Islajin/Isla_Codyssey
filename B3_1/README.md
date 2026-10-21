# B3_1 · 내 웹사이트를 AWS EC2에 배포하기

`B1_1` 포트폴리오(순수 HTML/CSS/JavaScript)를 서울 리전의 독립 VPC, Public Subnet, EC2, Nginx에 배포하는 실습 프로젝트입니다. 네트워크, 보안 그룹, 검증, 리소스 정리를 CloudFormation과 스크립트로 재현할 수 있게 만들었습니다.

> **진행 상태 — 2026-10-21:** AWS 계정은 생성되었으나 **이 프로젝트의 AWS 리소스는 아직 생성하지 않았고 외부 접속을 검증하지 않았습니다.** 따라서 실배포, 접속 스크린샷, IAM 역할 적용, 리소스 삭제 완료는 현재 충족되지 않았습니다. 코드·다이어그램·실행 절차를 준비한 상태입니다.

## 산출물

| 파일 | 내용 | 상태 |
| --- | --- | --- |
| [`docs/architecture.png`](docs/architecture.png) | VPC → Public Subnet → EC2와 외부 HTTP·SSH 흐름 | 작성 완료, 실제 구성과 비교 전 |
| [`infrastructure/cloudformation.yaml`](infrastructure/cloudformation.yaml) | 서울 리전용 VPC·서브넷·IGW·라우트·SG·EC2 구성 | 작성 완료, AWS 검증 전 |
| [`infrastructure/iam/`](infrastructure/iam/) | CloudFormation 서비스 역할의 신뢰·권한 정책 | 작성 완료, AWS 적용 전 |
| [`site/`](site/) | `B1_1` 웹사이트 파일 복사본 | 로컬 준비 완료 |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | 실제 계정 접근 장애와 현장 오류 기록란 | 접근 장애 기록, 클라우드 오류 해결은 미검증 |
| [`docs/cleanup-checklist.md`](docs/cleanup-checklist.md) | 과금 리소스 정리 항목 | 미생성 상태, 배포 후 확인 필요 |
| `docs/evidence/external-access.png` | 외부 `GET /health` 스크린샷 | **미생성** |

## 선택한 외부 검증 방식

**방식 B:** 외부에서 `GET http://<EC2_PUBLIC_IP>/health` 요청이 HTTP 200과 `OK`를 반환하는지 확인합니다. 포트폴리오 페이지는 `http://<EC2_PUBLIC_IP>/`로 확인합니다.

| 실제 접속 정보 | 현재 값 |
| --- | --- |
| 리전 | `ap-northeast-2` (서울) |
| 공개 IP / URL | 미배포, 없음 |
| HTTP 200 / OK | 미검증 |
| 증빙 스크린샷 | 미생성 |

배포 후 실제 IP, UTC/한국 시각, 접속 결과를 이 표에 기록하고 스크린샷을 `docs/evidence/external-access.png`로 저장해야 제출 요건을 충족합니다.

## 계정과 비용 사전 확인

1. 학습자 본인 명의의 AWS 계정을 사용합니다. 다른 사람의 키를 받거나 루트 계정으로 실습하지 않습니다.
2. 계정 유형·생성일에 따른 Free Tier 또는 크레딧 상태를 **Billing 콘솔에서 직접** 확인합니다. 신규 계정의 무료 혜택과 대상 인스턴스는 계정 조건에 따라 다릅니다. [AWS EC2 Free Tier 안내](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html)
3. 공개 IPv4는 사용 시간에 따른 비용이 생길 수 있습니다. Free Tier 포함 여부도 계정에서 확인합니다. [AWS VPC 퍼블릭 IPv4 안내](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-ip-addressing.html)
4. 실습용 IAM 접근과 **제한된 CloudFormation 실행 역할**을 준비합니다. 계정 관리자는 `./scripts/bootstrap-iam.sh <관리자-프로필>`로 전용 역할을 만들 수 있습니다. [`docs/iam-plan.md`](docs/iam-plan.md)의 권한 범위와 남은 검증 항목을 확인합니다. `AdministratorAccess`는 실습 사용자에게 붙이지 않습니다.
5. 서울 리전에서 EC2 키페어를 만들고 개인 키 `.pem`을 로컬의 안전한 위치에 보관합니다. Git에 올리지 않습니다. 본인 인터넷의 **현재 공인 IPv4/32**를 확인합니다.
6. AWS CLI v2, SSH, curl을 설치하고 CLI에 임시 자격 증명 프로필을 설정합니다. 이 작업 Mac에는 AWS CLI v2를 설치했습니다. [AWS CLI 인증 방법](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-authentication.html)

## 설계

```text
Internet user ─ HTTP :80 ─ Internet Gateway
                                  │
                        Public route table
                        0.0.0.0/0 → IGW
                                  │
VPC 10.0.0.0/16 ─ Public Subnet 10.0.1.0/24
                                  │
                    Security Group: HTTP any / SSH my IP
                                  │
                    EC2 (Nginx + B1_1 portfolio)
```

CloudFormation은 VPC 1개, Public Subnet 1개, IGW 1개, `0.0.0.0/0` 라우트와 연관, EC2 1대를 만듭니다. EC2에는 공인 IPv4를 할당합니다. 보안 그룹 인바운드는 HTTP 80을 전체 인터넷에, SSH 22를 학습자 IP `/32`에만 허용합니다. 전체 포트 개방 규칙은 없습니다. EBS 루트 볼륨은 암호화한 8GiB gp3이며 인스턴스 삭제 시 함께 삭제하도록 설정합니다. Elastic IP, NAT Gateway, Load Balancer, RDS는 생성하지 않습니다.

## 배포 및 검증

아래 명령은 **AWS 계정과 제한된 IAM 역할을 준비한 후** `B3_1` 디렉터리에서 실행합니다. `ROLE_ARN`은 관리자가 만든 전용 CloudFormation 실행 역할입니다. `MY_IP/32`에는 현재 본인 공인 IP를 넣습니다.

```bash
./scripts/deploy.sh \
  --profile b3-lab \
  --key-name B3_1-key \
  --key-file /안전한/경로/B3_1-key.pem \
  --ssh-cidr MY_IP/32 \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/B3_1CloudFormationRole

./scripts/verify.sh b3-lab /안전한/경로/B3_1-key.pem
```

배포 스크립트는 루트 자격 증명을 거절합니다. CloudFormation으로 인프라를 만든 뒤 SSH로 `site/`의 정적 파일을 Nginx 문서 루트에 복사합니다. `/health`가 `OK`인지 확인합니다. 검증 스크립트는 외부 `/health`, 인스턴스 내부 `localhost`, 외부 HTTPS 아웃바운드 결과를 `docs/evidence/verification.txt`에 저장합니다. **실제 외부 접속 스크린샷은 별도로 캡처해야 합니다.**

## 실습 종료 후 정리

접속 증빙을 확보하고 실습을 종료할 때 아래를 실행합니다. 스택 삭제 후 [`docs/cleanup-checklist.md`](docs/cleanup-checklist.md)에 실제 리소스 ID와 확인 결과를 적습니다.

```bash
./scripts/cleanup.sh b3-lab
```

CloudFormation 스택이 삭제되면 인스턴스와 포함된 네트워크 리소스도 함께 삭제되도록 설계했습니다. 삭제 실패 시 스택 Events에서 원인을 확인해야 합니다. 삭제 후 포트폴리오의 EC2 URL은 더 이상 접속할 수 없습니다. 계속 공개할 사이트가 필요하면 별도의 상시 호스팅과 비용 계획이 필요합니다.

## 로컬에서 확인한 것

- CloudFormation YAML 구문 파싱
- `bash -n`으로 스크립트 구문 확인
- `dot`으로 아키텍처 PNG 생성 및 육안 확인
- 복사한 `site/`의 HTML/CSS/JS 파일 존재 확인

이 검사는 AWS에 실제로 생성되는지, IAM 권한이 충분한지, 인터넷에서 접속되는지를 증명하지 않습니다. 그 항목은 계정 준비 후 배포·검증해야 합니다.
