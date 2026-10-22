# B2_1 나만의 용돈 기입장 — 요구사항별 구현 설명

| 항목 | 내용 |
| --- | --- |
| 분야 | AI/SW 기초 |
| 구분 | Python과 Git 심화 |
| 학습시간 | 60시간 |
| 필수/선택 | 필수 |

이 문서는 과제의 항목 순서에 맞춰 **무엇을 요구하는지 → 내가 무엇을 만들었는지 → 코드가 어떻게 처리하는지**를 적은 리뷰 자료입니다. 명령어는 모두 `B2_1` 폴더에서 실행합니다.

## 1. 미션 소개

**요구사항:** 파일에 영구 저장되는 콘솔 가계부를 만든다. 거래의 추가·조회·수정·삭제뿐 아니라 검색, 월별 요약, 카테고리, 예산, CSV 가져오기·내보내기를 제공한다. 제너레이터, 데코레이터, 타입 힌트, 모듈 분리도 적용한다.

**내 구현:** 사용자 명령을 받는 `cli.py`, 가계부 규칙을 처리하는 `service.py`, JSONL 파일을 읽고 쓰는 `storage.py`, 거래 모델과 검증 함수를 담은 `models.py`로 나눴습니다. 사용자가 명령을 입력하면 **CLI → 서비스 → 저장소 → 파일** 순서로 처리합니다. 거래·카테고리·예산은 각각 별도 파일에 저장되어 프로그램 종료 후에도 남습니다.

## 2. 최종 결과물 — 10가지 기능

| 기능 | 어떤 요구사항인가? | 내가 한 일 | 어떻게 동작하나? |
| --- | --- | --- | --- |
| 1. 거래 추가 `add` | 대화형으로 거래를 입력하고 ID를 출력 | `cli.py`에 입력 질문, `service.py`에 `add()` 구현 | 입력값을 검증해 `Transaction`을 만든 뒤 `transactions.jsonl` 끝에 기록 |
| 2. 거래 목록 `list` | `--limit`만큼 최신순 출력, 스트리밍 처리 | `list()`와 `newest_first()` 구현 | 파일을 한 줄씩 읽고 작은 묶음으로 정렬·병합한 뒤 필요한 건수만 출력 |
| 3. 거래 검색 `search` | 기간·카테고리·타입·메모·태그 필터 | `search()`에서 조건별 비교 구현 | 거래를 순회하며 조건에 맞는 것만 통과시키고 최신순으로 출력 |
| 4. 월별 요약 `summary` | 수입·지출·잔액·지출 TOP N | `summary()`와 `Summary` 모델 구현 | 거래 날짜의 월을 비교해 금액을 누적하고 카테고리 지출을 정렬 |
| 5. 예산 `budget` | 월 예산 저장과 초과 경고 | `set_budget()`과 예산 파일 구현 | 월별 금액을 저장하고 요약 시 지출/예산 사용률을 계산 |
| 6. 카테고리 `category` | 추가·목록·삭제, 사용 중 삭제 방지 | `add_category()`, `remove_category()` 구현 | 삭제 전 거래를 순회해 해당 카테고리 사용 여부 확인 |
| 7. 거래 수정 `update` | ID로 거래 필드 수정 | 옵션 방식 `update()`와 파일 `rewrite()` 구현 | 원본을 읽어 대상 거래만 변경한 임시 파일을 만든 뒤 교체 |
| 8. 거래 삭제 `delete` | ID로 삭제, 없는 ID 처리 | `delete()`와 `rewrite()` 재사용 | 임시 파일에 대상 거래를 빼고 기록한 뒤 교체 |
| 9. 가져오기 `import` | CSV 거래 일괄 등록 | `import_csv()`와 CSV 검증 구현 | 모든 행을 검사해 임시 파일에 준비한 후 한 번에 반영 |
| 10. 내보내기 `export` | 월·기간에 맞는 거래를 CSV로 저장 | `export_csv()`와 조건 검사 구현 | 조건에 맞는 거래를 CSV 임시 파일에 쓰고 완성 후 출력 파일로 교체 |

**추가 필수 구성:** 저장 파일은 `transactions.jsonl`, `categories.jsonl`, `budgets.jsonl`의 세 개입니다. `README.md`에 실행법, 파일 위치·형식, 명령 예시, CSV 스키마를 적었습니다.

### 실제 명령 하나가 처리되는 과정

`python3 -m budget_app add`를 실행하는 예로 설명하면:

1. `__main__.py`가 `cli.py`의 `main()`을 호출합니다.
2. `argparse`가 `add` 명령을 확인하고, CLI가 `input()`으로 여섯 값을 받습니다.
3. `BudgetService.add()`가 `Transaction`을 만들며 날짜·금액·타입·카테고리를 검증합니다.
4. `LedgerStore.append()`가 거래를 JSONL 한 줄로 저장합니다.
5. CLI가 생성된 거래 ID를 출력합니다. 다음 실행에서는 저장 파일을 다시 읽으므로 이 거래가 목록에 보입니다.

이 흐름을 이해하면 다른 명령도 같은 구조로 설명할 수 있습니다. 조회는 파일에서 읽고, 수정·삭제는 임시 파일을 만든 뒤 교체합니다.

## 3. 과제 목표 — 내 코드로 설명하기

### 파일 기반 저장과 CRUD

`LedgerStore`가 JSONL 파일을 읽고 쓰고, `BudgetService`가 거래의 추가·검색·수정·삭제와 월별 계산을 맡습니다. JSONL은 **한 줄에 JSON 객체 하나**를 저장하는 형식입니다. 같은 저장 폴더를 지정해 다시 실행하면 이전 거래를 읽을 수 있습니다.

### 클래스와 모듈의 책임

| 코드 | 역할 |
| --- | --- |
| `budget_app/models.py` | `Transaction` 데이터 모델, 날짜·금액 등 검증 |
| `budget_app/storage.py` | `LedgerStore`의 파일 입출력과 최신순 정렬 |
| `budget_app/service.py` | `BudgetService`의 기능 규칙과 `Summary` 결과 |
| `budget_app/cli.py` | 명령어 해석, 대화형 입력, 사용자 출력 |
| `budget_app/__main__.py` | `python3 -m budget_app` 실행 진입점 |

예를 들어 `add`는 CLI가 입력을 받고, 서비스가 카테고리 존재 여부를 확인하며, 저장소가 거래 파일에 기록합니다.

### `yield` 제너레이터 스트리밍

`storage.py`의 `transactions()`는 거래 파일을 한 줄씩 읽어 `yield`로 한 건씩 넘깁니다. `summary`는 거래를 순회하며 합계만 누적합니다. `list`와 `search`는 날짜 최신순으로 보여 줘야 하므로 `newest_first()`가 최대 1,000건씩 정렬해 임시 파일에 쓰고 병합합니다. 이렇게 하면 전체 거래를 한 번에 메모리에 올리지 않습니다.

### 데코레이터로 공통 기능 분리

`cli.py`의 `@timed`는 `main()`의 실행 시간 측정을 분리한 데코레이터입니다. 환경 변수 `BUDGET_APP_TIMING=1`일 때만 시간을 출력합니다.

```bash
BUDGET_APP_TIMING=1 python3 -m budget_app list --limit 5
```

### 타입 힌트로 함수 계약 표현

`transactions() -> Iterator[Transaction]`은 거래를 한 건씩 제공한다는 뜻입니다. `summary(month: str, top: int) -> Summary`는 월 문자열과 순위 개수를 받아 요약 객체를 반환한다는 뜻입니다. 타입 힌트는 코드 이해를 돕고, 실제 사용자 입력의 올바른 값인지는 `valid_date()`, `positive_amount()` 등이 검사합니다.

## 4. 기능 요구 사항 — 세부 구현

### 4-1. 실행 및 입력 방식

**요구사항:** `python -m budget_app <command> [options]` 형식, 모든 명령의 `--help`, 기본 대화형 입력, 긴 옵션 `--` 표기.

**내 구현:** `argparse`로 명령을 만들었습니다. `add`와 `category add`는 대화형이고, `update`는 과제에서 허용한 **옵션 방식**으로 고정했습니다. 조회·검색·요약·삭제·입출력은 옵션 방식입니다. `--data-dir`은 명령 앞에 놓습니다.

```bash
python3 -m budget_app --help
python3 -m budget_app search --help
python3 -m budget_app --data-dir ./data/demo list --limit 5
```

### 4-2. 데이터 모델과 입력 검증

**요구사항:** 거래의 고유 `id`, `income/expense` 타입, `YYYY-MM-DD` 날짜, 양수 금액, 카테고리, 선택 메모·태그. `dataclass`와 클래스 2개 이상 사용.

**내 구현:** `models.py`의 `Transaction`은 `@dataclass(frozen=True)`입니다. `LedgerStore`, `BudgetService`, `Summary`도 클래스로 만들었습니다. ID는 `TX-`와 UUID 일부를 조합합니다. 실제 존재하는 날짜인지, 금액이 0보다 큰 정수인지, 타입이 `income` 또는 `expense`인지 검사합니다. 거래 카테고리는 등록된 목록에 있어야 합니다. 입력 오류는 재입력 대신 원인과 수정 방향을 알려 주고 종료합니다.

### 4-3. 저장 정책과 초기 실행

**요구사항:** JSONL 또는 CSV 중 하나를 영구 저장 형식으로 선택하고 거래·카테고리·예산 파일 3개 이상 사용. 폴더 변경 가능. 첫 실행 처리.

**내 구현:** 영구 저장은 **JSONL**이고, CSV는 가져오기·내보내기용입니다. 기본 폴더는 현재 실행 위치의 `./data`; `--data-dir`로 바꿀 수 있습니다. 첫 실행에 폴더와 파일을 만들고 기본 카테고리 `food`, `transport`, `rent`, `salary`, `other`를 등록합니다.

| 파일 | 내용 | 한 줄 예시 |
| --- | --- | --- |
| `transactions.jsonl` | 거래 | `{"id":"TX-...","date":"2024-01-15","type":"expense","category":"food","amount":15000,"memo":"점심","tags":["meal"]}` |
| `categories.jsonl` | 카테고리 | `{"name":"food"}` |
| `budgets.jsonl` | 월 예산 | `{"month":"2024-01","amount":10000}` |

### 4-4. 거래 추가 `add`

**요구사항:** 날짜·타입·카테고리·금액·메모·태그를 대화형으로 입력하고, 등록 카테고리만 사용하며, 저장 후 ID 출력.

**내 구현:** CLI가 여섯 값을 순서대로 질문하고 서비스가 검사한 후 저장소에 추가합니다. 메모와 태그는 비워 둘 수 있습니다.

```text
$ python3 -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수 정수): 15000
메모(선택): 점심
태그(쉼표 구분, 선택): meal
[저장 완료] id=TX-실행시생성된값
```

### 4-5. 목록 `list`와 검색 `search`

**요구사항:** 목록의 `--limit`, 최신순 출력과 스트리밍. 검색의 `--from`, `--to`, `--category`, `--type`, `--q`, `--tag`.

**내 구현:** `list` 기본값은 20건입니다. `search`는 여러 조건을 동시에 적용하며 메모 키워드는 대소문자를 구분하지 않고, 태그는 정확히 일치시킵니다. 날짜가 같은 경우 ID 역순입니다. 둘 다 거래 파일을 제너레이터로 읽고 최신순 정렬을 적용합니다.

```bash
python3 -m budget_app list --limit 5
python3 -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food --type expense --q 점심 --tag meal
```

### 4-6. 수정 `update`와 삭제 `delete`

**요구사항:** ID로 수정·삭제, 없는 ID 처리, 파일 재작성 시 데이터 안전성 고려.

**내 구현:** `update`에서 생략한 필드는 유지하고 입력한 필드만 바꿉니다. `delete`는 지정 ID의 거래를 제거합니다. `storage.py`의 `rewrite()`가 한 줄씩 읽으며 새 임시 파일을 만들고, 성공하면 `os.replace()`로 교체합니다. 잘못된 금액으로 수정해 오류가 나면 기존 파일은 유지됩니다. 없는 ID는 메시지를 출력하고 종료 코드 1로 끝납니다.

```bash
python3 -m budget_app update --id TX-실제ID --amount 17000 --memo 저녁
python3 -m budget_app delete --id TX-실제ID
```

### 4-7. 월별 요약 `summary`와 예산 `budget`

**요구사항:** 해당 월의 수입·지출·잔액·카테고리 TOP N, 데이터 없는 달 표시. 월 예산 저장과 사용률·초과 경고.

**내 구현:** 거래를 한 건씩 읽으며 지정 월의 수입과 지출을 누적합니다. 잔액은 수입에서 지출을 뺀 값입니다. 예산은 `budgets.jsonl`에 저장하고, 사용률은 `지출 / 예산 × 100`입니다. 지출이 예산보다 클 때 경고합니다.

```bash
python3 -m budget_app budget set --month 2024-01 --amount 10000
python3 -m budget_app budget show --month 2024-01
python3 -m budget_app summary --month 2024-01 --top 3
```

예산 10,000원에 지출 15,000원이면 사용률 150.0%와 초과 경고가 나옵니다. 거래가 없는 월이면 `데이터 없음`을 출력합니다.

### 4-8. 카테고리 관리 `category`

**요구사항:** 추가·목록·삭제. 사용 중인 카테고리 삭제 시 차단하거나 대체 카테고리 요구.

**내 구현:** `category add`는 이름을 대화형으로 받고, `category list`는 저장된 목록을 보여 줍니다. `category remove --name`은 해당 카테고리를 쓰는 거래가 있으면 삭제를 막습니다.

```bash
python3 -m budget_app category list
python3 -m budget_app category add
python3 -m budget_app category remove --name hobby
```

### 4-9. CSV 가져오기 `import`와 내보내기 `export`

**요구사항:** UTF-8 헤더 포함 CSV. 필수 열 `date,type,category,amount`; 선택 열 `memo,tags`. 내보내기는 월 또는 날짜 조건 필수.

**내 구현:** 가져오기는 UTF-8 BOM도 읽습니다. 모든 행을 먼저 검증해 임시 파일에 준비하므로 잘못된 행이 하나라도 있으면 거래를 전혀 추가하지 않습니다. 오류에는 행 번호를 보여 줍니다. 정상 거래에는 새 ID가 붙으며, 같은 CSV를 다시 가져오면 새 거래가 추가됩니다. 내보내기는 `--month` 또는 `--from`/`--to` 중 하나 이상을 요구합니다. 월과 기간을 함께 주면 두 조건의 교집합을 내보냅니다.

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,점심,meal
2024-01-16,expense,transport,2000,버스,"commute,school"
```

```bash
python3 -m budget_app import --from sample.csv
python3 -m budget_app export --out january.csv --month 2024-01
python3 -m budget_app export --out range.csv --from 2024-01-01 --to 2024-01-31
```

### 4-10. 데코레이터, 오류 처리, 모듈화

**요구사항:** 데코레이터 1개 이상 실제 적용, 사용자에게 원인과 힌트 표시, 오류 종료 코드, 모듈 3개 이상.

**내 구현:** `@timed`를 `main()`에 적용했습니다. 사용자 오류는 `AppError`로 전달하고 CLI가 `[오류] 원인`을 출력합니다. 파일 경로·권한 오류 등에는 힌트를 덧붙입니다. 정상 종료는 0, 오류 종료는 1입니다. 코드가 모델·저장소·서비스·CLI의 네 모듈로 나뉩니다.

## 5. 보너스 과제

| 선택 과제 | 적용 여부 | 설명 |
| --- | --- | --- |
| 백업 기능 | 미구현 | 별도의 `backup` 명령은 없습니다. |
| 반복 내역 | 미구현 | 월급·월세 자동 생성은 없습니다. |
| 테이블 정렬 | 일부 적용 | 거래 출력에서 `type` 열 폭을 맞추지만 모든 열의 표 정렬 기능은 없습니다. |
| 저장 원자성 강화 | 구현 | 수정·삭제와 카테고리·예산 저장은 임시 파일 작성 후 교체합니다. CSV 내보내기도 임시 파일을 사용합니다. |

## 6. 개발 환경

Python 3.10 이상과 표준 라이브러리만 사용합니다. `pip install`은 필요하지 않습니다.

```bash
cd B2_1  # 저장소 최상위 폴더에서 실행
python3 --version
python3 -m budget_app --help
```

## 7. 제약 사항

| 제약 | 내 구현 |
| --- | --- |
| 외부 라이브러리 금지 | `argparse`, `csv`, `dataclasses`, `json`, `pathlib`, `tempfile` 등 표준 라이브러리만 사용 |
| JSONL 또는 CSV 중 하나로 영구 저장 | JSONL 선택. CSV는 데이터 교환용 |
| 저장 파일 3개 이상 | 거래·카테고리·예산 파일 3개 |
| 옵션은 `--` 표기 | `--help`, `--limit`, `--month`, `--from` 등 |
| 오류에 스택트레이스 금지·비정상 종료 | 사용자 입력 오류는 원인 메시지와 종료 코드 1 |

## 8. 결과 예시 및 실행해 볼 명령

아래 순서대로 실행하면 추가 → 검색 → 예산 경고 → 수정 → 내보내기 → 삭제 → 가져오기를 볼 수 있습니다. 기존 `./data`와 섞이지 않도록 `./data/review`를 사용합니다. `--data-dir`은 명령 앞에 둡니다. 반복 실행하면 이전 거래가 남아 건수가 달라질 수 있습니다.

### 8-1. 초기화와 거래 추가

```bash
cd B2_1  # 저장소 최상위 폴더에서 실행
python3 -m budget_app --data-dir ./data/review category list
python3 -m budget_app --data-dir ./data/review add
```

`add` 질문에는 `2024-01-15` → `expense` → `food` → `15000` → `점심` → `meal` 순서로 입력합니다. 출력된 `TX-...`를 복사합니다.

### 8-2. 조회·검색·예산 초과

```bash
python3 -m budget_app --data-dir ./data/review list --limit 5
python3 -m budget_app --data-dir ./data/review search --from 2024-01-01 --to 2024-01-31 --category food --tag meal
python3 -m budget_app --data-dir ./data/review budget set --month 2024-01 --amount 10000
python3 -m budget_app --data-dir ./data/review summary --month 2024-01 --top 3
```

한 거래만 추가했다면 요약에 지출 15,000원, 예산 사용률 150.0%, 초과 경고가 나타납니다.

### 8-3. 수정·CSV·삭제

`TX-실제ID`를 앞에서 받은 ID로 바꿉니다.

```bash
python3 -m budget_app --data-dir ./data/review update --id TX-실제ID --amount 17000 --memo 저녁
python3 -m budget_app --data-dir ./data/review export --out january.csv --month 2024-01
python3 -m budget_app --data-dir ./data/review delete --id TX-실제ID
python3 -m budget_app --data-dir ./data/review import --from january.csv
python3 -m budget_app --data-dir ./data/review list --limit 5
```

가져온 거래는 새 ID로 추가됩니다. 해당 카테고리를 사용하는 거래가 남았다면 삭제 거부도 볼 수 있습니다.

```bash
python3 -m budget_app --data-dir ./data/review category remove --name food
python3 -m budget_app --data-dir ./data/review delete --id 없는ID
```

### 8-4. 자동 테스트

```bash
python3 -m unittest discover -s tests -v
```

`tests/test_budget_app.py`의 4개 테스트는 CRUD·검색·요약·예산·영구 저장, 잘못된 수정과 CSV 가져오기 실패 시 데이터 보존, CSV 왕복과 오류 종료 코드, 여러 정렬 묶음의 병합을 검사합니다.

## 리뷰에서 설명할 핵심 질문

1. **왜 파일을 세 개로 나눴나?** 거래·카테고리·예산은 서로 다른 데이터라 각각 저장하고 관리하기 위해서입니다.
2. **왜 `yield`를 썼나?** 거래를 한 줄씩 읽어 파일 전체를 한 번에 메모리에 올리지 않기 위해서입니다.
3. **왜 임시 파일을 썼나?** 수정 중 오류가 발생해도 기존 파일을 유지하기 위해서입니다.
4. **왜 서비스와 CLI를 나눴나?** 사용자 입력·출력과 가계부 규칙의 책임을 구분하기 위해서입니다.
5. **현재 범위는?** 한 사람이 사용하는 콘솔 프로그램입니다. 여러 프로세스가 동시에 같은 파일에 쓰는 상황을 위한 파일 잠금은 없습니다.
