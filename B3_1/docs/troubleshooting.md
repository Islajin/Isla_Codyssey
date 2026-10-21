# B3_1 트러블슈팅 기록

## 실제 장애: 서울 리전 API가 AWS 조직 정책에서 거부됨

| 단계 | 기록 |
| --- | --- |
| 증상 | 2026-10-21 서울 리전(`ap-northeast-2`)에서 `cloudformation:ValidateTemplate`, `cloudformation:DescribeStacks`, `ec2:DescribeInstanceTypes`가 `explicit deny in a service control policy`로 실패함. |
| 가설 | CLI 인증 실패 또는 계정의 선택 리전이 서울이 아닌 상태에서 AWS 조직 정책이 서울 API를 차단함. |
| 검증 | `aws sts get-caller-identity --profile b3-lab`은 성공해 임시 역할 세션임을 확인함. 같은 템플릿의 `ValidateTemplate`과 `t3.micro` 조회는 시드니(`ap-southeast-2`)에서 성공함. 따라서 템플릿 구문이나 CLI 인증보다 계정 리전 정책이 원인임을 확인함. AWS 공식 문서도 이 유형의 새 프로젝트가 한국 주소에는 시드니를 선택 리전으로 할당한다고 설명함. |
| 조치 | 서울 리전에서 자원을 생성하지 않고 중단함. 현재 무료 프로젝트의 고정 리전을 임의로 우회하지 않았음. 서울 리전 사용이 가능한 별도 계정 또는 계정의 고급 기능 전환 여부는 사용자 결정이 필요함. |
| 결과 | 원인 확인. **서울 배포, SSH, 외부 HTTP는 미실행·미검증.** 시드니에서 템플릿 검증만 성공했으며 AWS 리소스는 생성하지 않음. |
| 재발 방지 | 배포 전에 반드시 대상 리전으로 `ValidateTemplate`과 EC2 조회를 실행해 계정 리전 정책을 확인하도록 README에 기록함. |

근거: [AWS 프로젝트 리전 안내](https://docs.aws.amazon.com/accounts/latest/reference/project-regions.html), [AWS 프로젝트 SCP 안내](https://docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html). `AccessDenied` 출력에는 계정·조직 식별자가 포함되어 있으므로 공개 저장소에는 원문 전체를 넣지 않았습니다.

## 실제 네트워크/권한 오류가 발생하면 아래에 추가

아래 항목은 예시가 아닌 **실행할 때 채우는 템플릿**입니다. 임의의 성공 결과를 적지 마세요.

```text
날짜/시간:
증상: (명령, HTTP 상태, SSH 오류 메시지)
가설: (예: SSH 소스 IP 불일치, 0.0.0.0/0 경로 누락, Nginx 미실행)
검증: (CloudFormation Events, SG 규칙, Route Table, cloud-init-output.log, curl 결과)
조치:
결과: (전/후 명령 출력 또는 스크린샷 경로)
재발 방지:
```

### 확인 명령 예시

```bash
aws cloudformation describe-stack-events --profile b3-lab --region ap-northeast-2 --stack-name b3-1
ssh -i /path/to/key.pem ec2-user@<PUBLIC_IP> 'sudo systemctl status nginx --no-pager'
ssh -i /path/to/key.pem ec2-user@<PUBLIC_IP> 'sudo tail -n 80 /var/log/cloud-init-output.log'
curl -v http://<PUBLIC_IP>/health
```
