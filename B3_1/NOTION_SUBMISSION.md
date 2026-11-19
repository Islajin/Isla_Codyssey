# B3_1 | 내 웹사이트를 인터넷에 올려 누구나 쓰게 하기

> **실습 결과:** 서울 리전(`ap-northeast-2`)에 IAM 사용자 `B3_1Learner`로 실제 배포했습니다. 2026-11-20 08:43:34 KST에 `http://43.201.24.70/health`의 HTTP 200 / `OK`를 검증했습니다. 검증 후 리소스를 삭제했으므로 해당 URL은 현재 접속 주소가 아닙니다. 세부 캡처와 원본 출력은 [README](README.md)에 연결했습니다.

## 미션 개요

- 분야: AI/SW 기초 · 클라우드와 AI API
- 목표: 기존 `B1_1` 포트폴리오를 AWS EC2의 Nginx에 배포하고 외부에서 접속 검증
- 리전: **서울 `ap-northeast-2`**
- 외부 접속 검증: **방식 B — `GET http://<퍼블릭IP>/health` → HTTP 200, 본문 `OK`**
- 보너스 HTTPS·Docker: 수행 범위에서 제외

## 최종 결과물

| 결과물 | 파일 | 확인할 내용 |
| --- | --- | --- |
| 아키텍처 다이어그램 | [`docs/architecture.png`](docs/architecture.png) | VPC·Public Subnet·IGW·Route Table·EC2·SG와 요청 흐름 |
| 외부 접속 증빙 | `docs/evidence/external-access.png`, `docs/evidence/verification.txt` | 서울 EC2의 실제 퍼블릭 IP로 `/health` 200/`OK` |
| 트러블슈팅 보고서 | [`docs/troubleshooting.md`](docs/troubleshooting.md) | 증상→가설→검증→조치→결과→재발 방지 |
| 리소스 정리 체크리스트 | [`docs/cleanup-checklist.md`](docs/cleanup-checklist.md) | EC2·EBS·EIP·IGW·VPC 등 종료/삭제 결과 |

## 평가 항목 1 — 기능이 실제로 동작하는가?

### VPC, Public Subnet, Internet Gateway, Route Table 구성

VPC `10.0.0.0/16` 안에 Public Subnet `10.0.1.0/24`를 만들고, Internet Gateway를 VPC에 연결합니다. Public Subnet과 연결된 Route Table에는 `0.0.0.0/0 → Internet Gateway` 경로를 둡니다. EC2는 해당 서브넷에 배치하고 공인 IPv4를 받습니다. 실제 콘솔/CLI 조회 증빙은 `docs/evidence/network.png`에 저장합니다.

### EC2 SSH 접속과 웹 서버

서울 EC2 `t3.micro` 1대에 Amazon Linux 2023과 Nginx를 사용합니다. SSH는 학습자 공인 IPv4 `/32`에서만 접속합니다. `systemctl is-active nginx`, `curl -I http://localhost/`, `curl -I https://example.com`으로 서버 실행·내부 HTTP·인터넷 아웃바운드를 확인합니다. 결과는 `docs/evidence/instance-and-server.png`와 `docs/evidence/verification.txt`에 기록합니다.

### 보안 그룹 최소 포트

인바운드 규칙은 `TCP 80 ← 0.0.0.0/0`, `TCP 22 ← 학습자 공인 IPv4/32` 두 개입니다. 전체 포트 공개 규칙은 만들지 않습니다. 실제 조회 결과는 `docs/evidence/security-group.png`에 저장합니다.

### 외부 접속 방식 B

외부 네트워크에서 `GET http://<서울 EC2 공인 IP>/health`를 호출해 HTTP `200`과 고정 본문 `OK`를 확인합니다. 실제 URL과 검증 시각은 [`README.md`](README.md)에 적고 응답 화면을 `docs/evidence/external-access.png`에 저장합니다. 리소스 삭제 후 과거 URL은 동작하지 않습니다.

### 리소스 정리

검증 화면을 저장한 후 CloudFormation 스택을 삭제합니다. EC2 `terminated`, EBS `NotFound`, Elastic IP 없음 또는 Release, IGW·Subnet·Route Table·SG·VPC 삭제를 실제 조회로 확인합니다. NAT Gateway·ALB/ELB·RDS는 애초에 생성하지 않습니다. 결과는 [`docs/cleanup-checklist.md`](docs/cleanup-checklist.md)에 기록합니다.

## 평가 항목 2 — 구성과 선택을 설명할 수 있는가?

### 외부 요청의 경로

사용자 → 공용 인터넷 → VPC에 연결된 Internet Gateway → 공인 IPv4가 있는 Public Subnet의 EC2 → 보안 그룹의 TCP 80 허용 → Nginx → `/health`의 `OK` 순서입니다. 응답은 역방향으로 돌아갑니다. 서브넷의 기본 경로가 IGW를 가리키기 때문에 EC2에서 외부로 나가는 일반 인터넷 트래픽도 전달됩니다. 네트워크 ACL과 인스턴스 방화벽도 통신을 차단하지 않아야 합니다.

### 보안 그룹 기준

브라우저의 공개 HTTP는 누구나 사용할 수 있도록 80만 전체 인터넷에 엽니다. 서버 관리용 SSH는 학습자 한 명의 현재 IP로 제한합니다. 데이터베이스 포트나 모든 포트는 열지 않습니다. 보안 그룹은 인스턴스의 **네트워크 통신**을 제어합니다.

### 외부 검증을 방식 B로 선택한 이유

`/health`는 화면 디자인과 무관하게 HTTP 상태 코드와 고정 문구를 동시에 확인할 수 있습니다. 외부 요청이 실제로 EC2의 Nginx까지 도달했는지 재현 가능한 명령으로 보여줍니다. 메인 페이지 `http://<퍼블릭IP>/`는 포트폴리오가 표시되는지도 별도로 확인합니다.

### 정리 기준과 이유

EC2 실행 시간, EBS 저장 공간, 사용 중 또는 남은 퍼블릭 IPv4/EIP 등이 비용 요인이 될 수 있습니다. 그래서 먼저 증빙을 확보하고 스택을 삭제한 다음 연결된 리소스가 모두 사라졌는지 조회합니다. 삭제 순서는 연결 관계를 고려합니다. CloudFormation이 EC2·SG·라우트·IGW·서브넷·VPC의 역순 의존성을 처리하도록 하고, 키페어·IAM 역할 등 스택 밖의 항목은 별도로 삭제합니다.

## 평가 항목 3 — 핵심 개념과 보안 원칙을 이해하는가?

### Public Subnet의 `0.0.0.0/0 → IGW`가 필요한 이유

`0.0.0.0/0`은 VPC 내부 경로에 해당하지 않는 모든 IPv4 목적지를 뜻합니다. 이 경로가 IGW를 가리켜야 Public Subnet의 EC2가 인터넷으로 응답·아웃바운드 요청을 보낼 수 있습니다. 경로만으로 충분하지 않고 IGW 연결, 공인 IP, 허용된 보안 그룹 규칙이 함께 필요합니다.

### Security Group과 IAM의 책임 차이

Security Group은 IP·프로토콜·포트를 기준으로 EC2에 들어오고 나가는 **패킷**을 허용합니다. IAM은 누가 `RunInstances`, `CreateVpc`, `DeleteStack` 같은 **AWS API 작업**을 수행할 수 있는지 결정합니다. HTTP 접속 오류는 SG/라우팅/서버 쪽부터, AWS API `AccessDenied`는 IAM 정책·SCP·리전 조건부터 조사합니다. 과제용 `B3_1Learner` IAM 사용자에는 서울 리전의 CloudFormation·EC2/VPC 작업과 공용 AMI 조회만 허용하도록 설계했습니다. `AdministratorAccess`, S3/RDS 관리 권한은 부여하지 않습니다.

### SSH·DB 포트를 전 세계에 열면 안 되는 이유

22나 3306/5432를 `0.0.0.0/0`에 열면 인터넷 전체에서 로그인 시도와 취약점 탐지가 가능합니다. 관리 포트는 내 IP `/32`로 제한하고 필요할 때만 사용합니다. 데이터베이스가 필요한 구조라면 사설 서브넷과 애플리케이션 SG를 소스로 사용하는 방식이 더 적절합니다.

### 가설 → 검증 → 조치

오류를 보면 먼저 관찰된 증상과 예상 범위를 구분합니다. 예를 들어 외부 `/health` 타임아웃이면 공인 IP·라우팅·SG·서버 순서로 확인하고, `curl localhost`까지 실패하면 Nginx 프로세스와 로그를 봅니다. 확인한 원인에만 변경을 적용하고 동일 명령으로 재검증합니다. 실제 실습 사례와 명령 출력은 [`docs/troubleshooting.md`](docs/troubleshooting.md)에 기록합니다.

## 평가 항목 4 — 장애와 변경 상황을 판단할 수 있는가?

### 외부에서 열리지 않을 때 점검 순서

1. 공인 IPv4가 EC2에 붙어 있고 주소를 올바르게 입력했는지 확인합니다.
2. IGW가 VPC에 연결되고 Public Subnet의 Route Table에 `0.0.0.0/0 → IGW`가 있는지 확인합니다.
3. SG의 HTTP 80 소스와 NACL을 확인합니다. SSH 오류라면 현재 학습자 IP와 `/32` 규칙을 비교합니다.
4. EC2에 SSH로 들어가 `curl -I localhost`, `systemctl status nginx`, `/var/log/nginx/error.log`, `/var/log/cloud-init-output.log`를 확인합니다.
5. 한 항목씩 조치하고 외부 GET을 다시 실행합니다.

### IAM 권한이 부족할 때

실패한 AWS API 작업명·리소스 ARN·리전·오류의 `explicit deny`/`implicit deny`를 확인합니다. CloudFormation Events와 IAM 정책, 조직 SCP를 대조한 후 필요한 작업과 리소스 범위만 추가합니다. 무작정 관리자 권한을 주지 않습니다.

### 인스턴스가 2대로 늘어나면

두 EC2에 동일한 앱을 배포하고 여러 AZ의 서브넷과 Application Load Balancer, 대상 그룹·헬스 체크를 고려합니다. ALB가 공개 HTTP(S)를 받고 EC2의 SG는 ALB SG에서만 앱 포트를 허용하도록 바꿉니다. 배포·장애 복구를 위해 Auto Scaling을 추가할 수 있습니다. 다만 이 실습은 비용과 요구사항 때문에 1대만 구성합니다.

### 예상보다 비용이 늘어나면

Billing에서 리전·서비스·사용 유형을 먼저 확인한 뒤 EC2 실행 시간, EBS 및 스냅샷, 공인 IPv4/EIP, NAT Gateway, Load Balancer, 데이터 전송을 차례로 조회합니다. 본 실습에서 만든 리소스만 식별해 삭제하고 다시 목록을 조회합니다. Billing 반영에는 지연이 있어 리소스 목록의 삭제 확인과 청구 화면을 함께 기록합니다.

## 평가 항목 5 — 보너스

HTTPS와 Docker는 이번 제출 범위에서 제외했습니다. 보너스 미부여로 표시합니다.

## 제출 전 최종 확인

- [x] 서울 리전 `ap-northeast-2`의 실제 URL과 검증 시각을 README에 기록
- [x] 네트워크·EC2/서버·보안 그룹·IAM·외부 접속 캡처를 README에 연결
- [x] Nginx 준비 전 reload 실패와 해결 사례를 기록
- [x] EC2·EBS·EIP·IGW·VPC 정리 결과 최종 조회와 캡처 확인
- [x] 과거 시드니 증빙을 별도 보관하고 서울 결과와 구분
