# B3_1 · 내 웹사이트를 AWS EC2에 배포하기

`B1_1` 포트폴리오(순수 HTML/CSS/JavaScript)를 AWS의 독립 VPC, Public Subnet, EC2, Nginx에 배포하는 실습 프로젝트입니다. 네트워크, 보안 그룹, 검증, 리소스 정리를 CloudFormation과 스크립트로 재현할 수 있게 만들었습니다.

> **실습 결과 — 2026-10-21:** 학습자 요청에 따라 **시드니 리전(`ap-southeast-2`)**에서 실제 배포했습니다. EC2의 Nginx와 포트폴리오, 외부 `/health` HTTP 200/`OK`, 내부 `localhost` HTTP 200, 인터넷 아웃바운드 HTTPS 200을 확인했습니다. 과제 원문은 **서울 리전(`ap-northeast-2`)을 필수로 지정**하므로 리전 조건은 충족하지 않습니다. 현재 무료 프로젝트에서 서울 API가 SCP로 거부된 기록은 [`docs/troubleshooting.md`](docs/troubleshooting.md)에 있습니다.

## 산출물

| 파일 | 내용 | 상태 |
| --- | --- | --- |
| [`docs/architecture.png`](docs/architecture.png) | VPC → Public Subnet → EC2와 외부 HTTP·SSH 흐름 | 실제 구성과 대조 완료 |
| [`infrastructure/cloudformation.yaml`](infrastructure/cloudformation.yaml) | 시드니 VPC·서브넷·IGW·라우트·SG·EC2 구성 | 실제 스택 생성 및 검증 완료 |
| [`infrastructure/iam/`](infrastructure/iam/) | CloudFormation 서비스 역할의 신뢰·권한 정책 | 시드니에서 적용 및 배포 확인 |
| [`site/`](site/) | `B1_1` 웹사이트 파일 복사본 | EC2 Nginx에 배포, 외부 첫 화면 HTTP 200 |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | 서울 정책 거부와 실제 SG 오류 해결 기록 | 작성 완료 |
| [`docs/cleanup-checklist.md`](docs/cleanup-checklist.md) | 과금 리소스 정리 항목 | 실습 후 삭제 결과 기록 |
| [`docs/evidence/external-access.png`](docs/evidence/external-access.png) | AWS CloudShell에서 공개 URL `GET /health`를 호출한 실제 화면 | HTTP 200 / `OK` 확인 |
| [`docs/evidence/verification.txt`](docs/evidence/verification.txt) | 외부·내부·아웃바운드 명령 로그 | 모두 200 확인 |

## 선택한 외부 검증 방식

**방식 B:** 외부에서 `GET http://<EC2_PUBLIC_IP>/health` 요청이 HTTP 200과 `OK`를 반환하는지 확인합니다. 포트폴리오 페이지는 `http://<EC2_PUBLIC_IP>/`로 확인합니다.

| 실제 접속 정보 | 현재 값 |
| --- | --- |
| 리전 | `ap-southeast-2` (시드니, 과제의 서울 조건과 다름) |
| 실습 당시 공개 IP / URL | `http://15.134.214.202/health` |
| HTTP 200 / OK | 2026-10-21 04:16 UTC (13:16 KST) 확인 |
| 증빙 스크린샷 | [`docs/evidence/external-access.png`](docs/evidence/external-access.png) |

스크린샷은 AWS CloudShell에서 공개 IP를 직접 호출한 실제 결과입니다. 실습 후 리소스를 삭제하면 위 URL은 더 이상 열리지 않습니다.

## 계정과 비용 사전 확인

1. 학습자 본인 명의의 AWS 계정을 사용합니다. 다른 사람의 키를 받거나 루트 계정으로 실습하지 않습니다. 이 무료 프로젝트는 서울 리전 사용이 차단되어 학습자 요청에 따라 시드니에서 진행했습니다. [AWS 프로젝트 리전 안내](https://docs.aws.amazon.com/accounts/latest/reference/project-regions.html)
2. 계정 유형·생성일에 따른 Free Tier 또는 크레딧 상태를 **Billing 콘솔에서 직접** 확인합니다. 신규 계정의 무료 혜택과 대상 인스턴스는 계정 조건에 따라 다릅니다. [AWS EC2 Free Tier 안내](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html)
3. 공개 IPv4는 사용 시간에 따른 비용이 생길 수 있습니다. Free Tier 포함 여부도 계정에서 확인합니다. [AWS VPC 퍼블릭 IPv4 안내](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-ip-addressing.html)
4. `./scripts/bootstrap-iam.sh`로 제한된 CloudFormation 실행 역할을, `./scripts/bootstrap-operator.sh`로 시드니 CloudFormation·EC2 조회·특정 역할 전달만 허용한 실습 역할을 만듭니다. 배포는 `b3-operator` 역할 세션으로 실행했습니다. [`docs/iam-plan.md`](docs/iam-plan.md)에 실제 범위와 한계를 기록했습니다.
5. 시드니 리전에서 EC2 키페어를 만들고 개인 키 `.pem`을 로컬의 안전한 위치에 보관합니다. Git에 올리지 않습니다. 본인 인터넷의 **현재 공인 IPv4/32**를 확인합니다.
6. AWS CLI v2, SSH, curl을 설치하고 CLI에 임시 자격 증명 프로필을 설정합니다. 이 작업 Mac에는 AWS CLI v2와 `b3-lab` 임시 프로필을 설정하고 `sts get-caller-identity`를 확인했습니다. [AWS CLI 인증 방법](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-authentication.html)

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

아래 명령은 **시드니 접근 가능한 AWS 계정과 제한된 IAM 역할을 준비한 후** `B3_1` 디렉터리에서 실행합니다. `ROLE_ARN`은 관리자가 만든 전용 CloudFormation 실행 역할입니다. `MY_IP/32`에는 현재 본인 공인 IP를 넣습니다. 실습 후 역할과 키페어를 삭제했으므로 재실행할 때는 먼저 아래 역할·키페어를 다시 준비해야 합니다.

```bash
./scripts/bootstrap-iam.sh b3-lab
./scripts/bootstrap-operator.sh b3-lab
aws configure set role_arn arn:aws:iam::ACCOUNT_ID:role/B3_1OperatorRole --profile b3-operator
aws configure set source_profile b3-lab --profile b3-operator
aws configure set region ap-southeast-2 --profile b3-operator

# 시드니 EC2 키페어는 별도로 생성하고 개인 키를 Git 밖에 보관
./scripts/deploy.sh \
  --profile b3-operator \
  --key-name B3_1-20261021 \
  --key-file /안전한/경로/B3_1-20261021.pem \
  --ssh-cidr MY_IP/32 \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/B3_1CloudFormationRole

./scripts/verify.sh b3-operator /안전한/경로/B3_1-20261021.pem
```

배포 스크립트는 루트 자격 증명을 거절합니다. CloudFormation으로 인프라를 만든 뒤 SSH로 `site/`의 정적 파일을 Nginx 문서 루트에 복사합니다. `/health`가 `OK`인지 확인합니다. 검증 스크립트는 외부 `/health`, 인스턴스 내부 `localhost`, 외부 HTTPS 아웃바운드 결과를 `docs/evidence/verification.txt`에 저장합니다. AWS CloudShell의 실제 외부 호출 화면을 `docs/evidence/external-access.png`에 캡처했습니다.

## 실습 종료 후 정리

접속 증빙을 확보하고 실습을 종료할 때 아래를 실행합니다. 스택 삭제 후 [`docs/cleanup-checklist.md`](docs/cleanup-checklist.md)에 실제 리소스 ID와 확인 결과를 적습니다.

```bash
./scripts/cleanup.sh b3-operator
```

CloudFormation 스택이 삭제되면 인스턴스와 포함된 네트워크 리소스도 함께 삭제되도록 설계했습니다. 삭제 실패 시 스택 Events에서 원인을 확인해야 합니다. 삭제 후 포트폴리오의 EC2 URL은 더 이상 접속할 수 없습니다. 계속 공개할 사이트가 필요하면 별도의 상시 호스팅과 비용 계획이 필요합니다.

이 실습에서는 스택 삭제 뒤 EC2 키페어와 두 IAM 역할도 별도로 삭제하고 로컬 `.pem`을 지웠습니다. `cleanup.sh`는 스택만 삭제하므로 키페어·IAM 역할은 [`docs/cleanup-checklist.md`](docs/cleanup-checklist.md)에 따라 확인해야 합니다.

## 확인한 것과 남은 요건

- CloudFormation YAML 구문 파싱
- `bash -n`으로 스크립트 구문 확인
- `dot`으로 아키텍처 PNG 생성 및 육안 확인
- 복사한 `site/`의 HTML/CSS/JS 파일 존재 확인
- AWS CLI 임시 인증과 `sts get-caller-identity` 성공
- 시드니 CloudFormation 스택 `CREATE_COMPLETE`, EC2 `running`, 외부 첫 화면 HTTP 200
- 외부 `/health` HTTP 200 / `OK`, 서버 내부 `localhost` HTTP 200, 인터넷 아웃바운드 HTTPS 200
- 보안 그룹의 HTTP 80 `0.0.0.0/0`, SSH 22 개인 IP `/32` 확인
- Public Subnet에 `0.0.0.0/0 → Internet Gateway` 활성 라우트 확인
- 서울 리전 API는 이 계정의 SCP에서 거부됨. **과제의 서울 리전 조건은 미충족**

과제 제출 시 리전 차이를 숨기지 마세요. 서울 리전 사용이 가능한 계정으로 다시 배포하거나, 담당자에게 시드니 실습 허용을 받아야 전체 요구사항을 충족합니다. [AWS 프로젝트 리전](https://docs.aws.amazon.com/accounts/latest/reference/project-regions.html)
