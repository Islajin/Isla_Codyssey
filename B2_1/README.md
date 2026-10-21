# B2_1 나만의 용돈 기입장

Python 표준 라이브러리만 사용하는 파일 기반 콘솔 가계부입니다. Python 3.10 이상에서 실행합니다.

## 실행

이 폴더(`B2_1`)에서 실행합니다. 별도 설치가 필요하지 않습니다.

```bash
python3 -m budget_app --help
python3 -m budget_app add
python3 -m budget_app list --limit 5
```

모든 명령과 하위 명령에서 `--help`를 사용할 수 있습니다. 저장 폴더를 바꾸려면 **명령 앞에** `--data-dir`을 놓습니다.

```bash
python3 -m budget_app --data-dir ./my-data summary --month 2024-01
```

첫 실행 시 저장 폴더와 세 파일을 자동으로 만들고 기본 카테고리 `food`, `transport`, `rent`, `salary`, `other`를 등록합니다. `add`와 `category add`는 대화형 입력입니다. `update`는 **옵션 방식**으로 고정했습니다.

## 주요 명령

```bash
python3 -m budget_app category list
python3 -m budget_app category add
python3 -m budget_app category remove --name hobby

python3 -m budget_app add
python3 -m budget_app list --limit 10
python3 -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food --type expense --q 점심 --tag meal
python3 -m budget_app summary --month 2024-01 --top 3
python3 -m budget_app budget set --month 2024-01 --amount 500000
python3 -m budget_app budget show --month 2024-01

python3 -m budget_app update --id TX-예시ID --amount 17000 --memo 저녁 --tags meal,friend
python3 -m budget_app delete --id TX-예시ID

python3 -m budget_app import --from sample.csv
python3 -m budget_app export --out january.csv --month 2024-01
python3 -m budget_app export --out range.csv --from 2024-01-01 --to 2024-01-31
```

`export`에는 `--month` 또는 날짜 범위 조건을 하나 이상 지정해야 합니다. `--month`와 날짜 범위를 함께 주면 두 조건의 교집합을 내보냅니다. `list`와 `search`는 날짜 최신순입니다. 같은 날짜에서는 ID 역순입니다. 사용 중인 카테고리는 삭제할 수 없습니다. `summary`는 데이터 없는 달을 명시하고, 예산이 있으면 사용률과 초과 경고를 보여 줍니다.

## 저장 위치와 형식

기본 저장 폴더는 현재 작업 디렉터리의 `./data`입니다. 아래 JSONL 파일 3개가 각각 한 줄에 JSON 객체 하나를 저장합니다.

| 파일 | 내용 | 예시 |
| --- | --- | --- |
| `transactions.jsonl` | 거래 | `{"id":"TX-...","date":"2024-01-15","type":"expense","category":"food","amount":15000,"memo":"점심","tags":["meal"]}` |
| `categories.jsonl` | 등록된 카테고리 | `{"name":"food"}` |
| `budgets.jsonl` | 월 예산 | `{"month":"2024-01","amount":500000}` |

`data/`는 `.gitignore`에 포함되어 개인 거래 정보가 Git에 올라가지 않습니다. 세 파일을 함께 백업하면 데이터를 옮길 수 있습니다.

## CSV 가져오기/내보내기 스키마

UTF-8, 헤더 포함 CSV입니다. `import`는 UTF-8 BOM도 읽습니다. `memo`나 `tags` 열은 생략할 수 있습니다.

| 열 | 필수 | 형식 |
| --- | --- | --- |
| `date` | 예 | 실제 날짜 `YYYY-MM-DD` |
| `type` | 예 | `income` 또는 `expense` |
| `category` | 예 | 등록된 카테고리명 |
| `amount` | 예 | 0보다 큰 정수 |
| `memo` | 아니요 | 문자열 |
| `tags` | 아니요 | 쉼표로 구분한 문자열. CSV에서는 따옴표로 묶음 |

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,점심,meal
2024-01-16,expense,transport,2000,버스,"commute,school"
```

가져오기 전 모든 행을 검증합니다. 한 행이라도 잘못되면 몇 행인지 알려 주고 **아무 거래도 반영하지 않습니다**. 가져온 거래에는 새 고유 ID를 부여합니다. 동일 CSV를 다시 가져오면 별도 거래가 추가됩니다.

## 구조와 안전성

| 모듈 | 책임 |
| --- | --- |
| `models.py` | `Transaction` dataclass, 날짜·금액·카테고리 검증 |
| `storage.py` | JSONL 읽기/쓰기, 임시 파일을 통한 원자적 교체, 외부 병합 정렬 |
| `service.py` | CRUD, 검색, 요약, 예산·카테고리 규칙, CSV 입출력 |
| `cli.py` | 명령 해석, 대화형 입력, 출력, 사용자 오류 처리 |

`transactions()`는 `yield`로 한 줄씩 읽습니다. 최신순 출력은 1,000건씩 정렬한 임시 파일들을 병합해 전체 거래를 메모리에 올리지 않습니다. 수정·삭제·가져오기는 새 임시 파일이 완성된 뒤 `os.replace`로 교체합니다. 실행 시간 측정 데코레이터는 `BUDGET_APP_TIMING=1`일 때 활성화됩니다.

```bash
BUDGET_APP_TIMING=1 python3 -m budget_app list --limit 5
python3 -m unittest discover -s tests -v
```

오류는 원인과 해결 방향을 표준 오류로 출력하고 종료 코드 1을 반환합니다. `--help`나 정상 실행은 종료 코드 0입니다.
