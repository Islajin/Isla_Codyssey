# B3_1 트러블슈팅 기록

## 실제 장애: 서울 리전 API가 AWS 조직 정책에서 거부됨

| 단계 | 기록 |
| --- | --- |
| 증상 | 2026-10-21 서울 리전(`ap-northeast-2`)에서 `cloudformation:ValidateTemplate`, `cloudformation:DescribeStacks`, `ec2:DescribeInstanceTypes`가 `explicit deny in a service control policy`로 실패함. |
| 가설 | CLI 인증 실패 또는 계정의 선택 리전이 서울이 아닌 상태에서 AWS 조직 정책이 서울 API를 차단함. |
| 검증 | `aws sts get-caller-identity --profile b3-lab`은 성공해 임시 역할 세션임을 확인함. 같은 템플릿의 `ValidateTemplate`과 `t3.micro` 조회는 시드니(`ap-southeast-2`)에서 성공함. 따라서 템플릿 구문이나 CLI 인증보다 계정 리전 정책이 원인임을 확인함. AWS 공식 문서도 이 유형의 새 프로젝트가 한국 주소에는 시드니를 선택 리전으로 할당한다고 설명함. |
| 조치 | 서울 리전에서 자원을 생성하지 않고 중단함. 현재 무료 프로젝트의 고정 리전을 임의로 우회하지 않았음. 서울 리전 사용이 가능한 별도 계정 또는 계정의 고급 기능 전환 여부는 사용자 결정이 필요함. |
| 결과 | 서울 리전은 계속 차단되어 **과제 리전 조건 미충족**. 학습자 요청으로 시드니에서 별도 실습을 진행함. |
| 재발 방지 | 배포 전에 반드시 대상 리전으로 `ValidateTemplate`과 EC2 조회를 실행해 계정 리전 정책을 확인하도록 README에 기록함. |

근거: [AWS 프로젝트 리전 안내](https://docs.aws.amazon.com/accounts/latest/reference/project-regions.html), [AWS 프로젝트 SCP 안내](https://docs.aws.amazon.com/accounts/latest/reference/scps-and-rcps-for-projects.html). `AccessDenied` 출력에는 계정·조직 식별자가 포함되어 있으므로 공개 저장소에는 원문 전체를 넣지 않았습니다.

## 실제 장애: 보안 그룹 설명의 허용되지 않는 문자

| 단계 | 기록 |
| --- | --- |
| 증상 | 2026-10-21 첫 시드니 CloudFormation 배포에서 `WebSecurityGroup`이 `CREATE_FAILED`가 되었고 스택이 `ROLLBACK_COMPLETE`로 종료됨. |
| 가설 | `SecurityGroupIngress.Description` 값에 EC2가 허용하지 않는 문자가 포함됨. |
| 검증 | `describe-stack-events`의 `Invalid rule description` 오류와 허용 문자 목록을 확인함. 템플릿의 `SSH from the learner's IPv4 only`에 있는 작은따옴표가 허용 목록에 없었음. |
| 조치 | 설명을 `SSH from the learner IPv4 only`로 바꿈. 실패 스택 삭제 완료를 기다린 뒤 같은 템플릿으로 재배포함. |
| 결과 | `WebSecurityGroup`, 전체 `b3-1` 스택이 `CREATE_COMPLETE`. SSH 접속과 외부 `/health` HTTP 200/`OK` 확인. 실제 증빙은 [`evidence/verification.txt`](evidence/verification.txt), [`evidence/external-access.png`](evidence/external-access.png). |
| 재발 방지 | 보안 그룹 설명에는 영문·숫자·EC2 허용 기호만 쓰고, CloudFormation 실패 시 Events의 첫 `CREATE_FAILED` 원인을 확인함. `ValidateTemplate` 통과만으로 서비스별 값 제약까지 검증되지는 않음을 배포 전 점검에 추가함. |

### 실제 사용한 확인 명령

```bash
aws cloudformation describe-stack-events --profile b3-operator --region ap-southeast-2 --stack-name b3-1
curl -i http://15.134.214.202/health
```

실습 후 스택과 EC2는 삭제했으므로 위 과거 공개 URL은 더 이상 접속되지 않습니다.
