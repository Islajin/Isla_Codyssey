# B3_1 트러블슈팅 기록

## 현재 기록: CLI 인증·실습 역할이 없어 실제 AWS 배포 전

| 단계 | 기록 |
| --- | --- |
| 증상 | 2026-10-21 초기에는 AWS 계정과 CLI 인증이 없어서 스택 생성, SSH, 외부 HTTP 검증을 실행할 수 없었음. |
| 가설 | 실습용 자격 증명과 역할이 없어 AWS API 호출이 불가능함. |
| 검증 | 초기 로컬에서 `command -v aws`와 `~/.aws` 구성을 확인해 AWS CLI/프로필이 없었음. 이후 학습자가 AWS 계정을 생성했고, 콘솔에서 무료 플랜과 IAM 화면을 확인함. |
| 조치 | AWS CLI를 설치하고 CloudFormation 템플릿, 배포·검증·정리 스크립트, 실행 역할 정책을 작성함. CLI 인증과 역할 적용은 진행 중. |
| 결과 | 계정과 CLI 프로그램은 준비됐으나 AWS 실배포와 외부 접속은 **미검증**. 성공으로 기록하지 않음. |
| 재발 방지 | 실습 시작 전 계정, 리전, IAM 역할, EC2 키페어, 비용 한도를 확인하는 사전 점검표를 README에 추가함. |

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
