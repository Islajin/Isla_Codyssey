# E1_3 — Mini NPU Simulator (MAC 연산 시뮬레이터)

AI 모델의 핵심 연산인 MAC(Multiply-Accumulate)을 순수 반복문으로 구현해, 3×3 사용자 입력과 `data.json`의 5×5/13×13/25×25 데이터를 대상으로 Cross(십자가)/X 패턴을 판별하고 크기별 연산 시간을 측정하는 콘솔 프로그램입니다.

## 실행 방법

```bash
python3 main.py
```

- 실행하면 `[모드 선택]`에서 `1`(사용자 입력, 3×3) 또는 `2`(`data.json` 분석)를 입력합니다.
- `data.json`은 `main.py`와 같은 폴더에 있어야 합니다(코드가 스크립트 위치 기준으로 자동 탐색).
- 모드 1은 필터 A, 필터 B, 패턴을 각각 3줄씩 공백으로 구분해 입력받습니다. 숫자 개수가 맞지 않거나 파싱에 실패하면 안내 문구를 출력하고 해당 줄을 다시 입력받습니다.

## 구현 순서

실제로 아래 순서로 만들고 검증했습니다.

1. **요구사항 & 데이터 구조 파악**: `data.json`을 먼저 열어 `filters.size_5/13/25`(각 `cross`/`x` 2차원 배열)와 `patterns.size_{N}_{idx}`(`input` + `expected`) 구조를 확인하고, `expected`가 `'+'`/`'x'`, 필터 키가 `'cross'`/`'x'`로 서로 다르게 표기된 것을 확인했습니다.
2. **핵심 함수부터 설계**: 나머지 로직이 전부 이 위에서 돌아가므로 `normalize_label`(라벨 표준화), `mac_score`(이중 for문 MAC 연산), `judge_label`(epsilon 기반 판정)을 가장 먼저 작성했습니다.
3. **성능 측정 도구 준비**: `measure_avg_ms`(10회 개별 측정 후 평균)와, `data.json`에 없는 3×3 벤치마크용 패턴을 만들기 위한 `generate_cross`/`generate_x`를 미리 만들어 뒀습니다.
4. **모드 1(3×3 사용자 입력) 구현**: `read_row`/`read_matrix`로 입력 검증(개수 불일치·파싱 실패 시 재입력)을 넣고, 미션 소개의 예시 입력(십자가 필터 A, X 필터 B, X 패턴)을 그대로 실행해 A=1.0, B=5.0, 판정 B가 스펙과 정확히 일치하는지 먼저 검증했습니다.
5. **모드 2(`data.json` 분석) 구현**: 필터 로드 → 패턴별 판정 → 성능 분석 → 결과 요약의 4단계를 순서대로 작성했습니다.
6. **예외 처리 강화 및 강제 오류 테스트**: `size_13` 필터를 일부러 지우고 `size_25_1` 패턴 크기를 24×25로 깨뜨린 테스트 데이터를 만들어 실행해보고, 프로그램이 죽지 않고 해당 케이스만 FAIL로 남기는지 확인한 뒤 예외 처리 범위를 다듬었습니다.
7. **실측 후 문서화**: 실제 `data.json`을 돌려서 나온 진짜 PASS/FAIL 결과와 성능 표 수치를 근거로 README의 결과 리포트를 작성했습니다(추측이 아니라 실행 로그 기반).
8. **배포**: 로컬 `Codyssey_E1_3` 폴더와 GitHub `Islajin/Isla_Codyssey` 저장소의 `E1_3` 폴더(main 브랜치)에 동일하게 반영했습니다.
9. **보너스 확장(1차원 배열 최적화)**: `mac_score_1d` + `flatten`을 추가로 구현해 2D/1D 성능 비교까지 붙였습니다(모드 2 성능 분석 절 참고).

## 구현 요약

### 라벨 정규화 — `normalize_label`

```python
LABEL_MAP = {'+': 'Cross', 'cross': 'Cross', 'x': 'X'}

def normalize_label(raw):
    key = str(raw).strip().lower()
    if key not in LABEL_MAP:
        raise ValueError(f"알 수 없는 라벨: {raw}")
    return LABEL_MAP[key]
```

`expected` 값(`'+'`/`'x'`)과 필터 키(`'cross'`/`'x'`)는 표기만 다를 뿐 같은 개념이라, 매핑 딕셔너리 하나로 둘 다 표준 라벨(`Cross`/`X`)로 변환합니다. 콘솔 출력과 PASS/FAIL 비교는 항상 이 표준 라벨을 기준으로 합니다. 매핑에 없는 값이 들어오면 `ValueError`를 던져 호출부(모드 2 케이스 루프)가 그 케이스만 FAIL로 처리하게 합니다.

### MAC 연산 — `mac_score`

```python
def mac_score(pattern, filter_):
    total = 0.0
    for row_p, row_f in zip(pattern, filter_):
        for p, f in zip(row_p, row_f):
            total += p * f
    return total
```

이중 for문(바깥 N번 × 안쪽 N번)으로 같은 위치의 값을 곱해서 누적합을 구합니다. NumPy 등 외부 라이브러리는 사용하지 않았고, 이 이중 루프 구조가 아래 성능 분석의 O(N²) 근거이기도 합니다.

### 동점 처리 정책 — `judge_label`

```python
EPSILON = 1e-9

def judge_label(score_cross, score_x, eps=EPSILON):
    if abs(score_cross - score_x) < eps:
        return 'UNDECIDED'
    return 'Cross' if score_cross > score_x else 'X'
```

`abs(score_cross - score_x) < 1e-9`이면 `UNDECIDED`를 반환합니다. 채점 규칙상 `UNDECIDED`는 expected와 무관하게 항상 FAIL로 처리됩니다.

### 성능 측정 — `measure_avg_ms`

```python
def measure_avg_ms(func, *args, repeats=10):
    result = None
    total_seconds = 0.0
    for _ in range(repeats):
        start = time.perf_counter()
        result = func(*args)
        end = time.perf_counter()
        total_seconds += (end - start)
    avg_ms = (total_seconds / repeats) * 1000
    return result, avg_ms
```

임의의 함수를 10회(`repeats`) 개별 호출하며 각각 `time.perf_counter()`로 측정한 뒤 평균(ms)을 냅니다. 모드 1(필터 A/B 점수 계산)과 모드 2(크기별 MAC 연산) 양쪽 성능 측정에 그대로 재사용됩니다. 모드 2에서는 `data.json`에 없는 3×3 크기를 벤치마크하기 위해 내부적으로 십자가/X 패턴을 생성하는 `generate_cross(n)` / `generate_x(n)`을 사용합니다.

### 스키마 검증 — 모드 2 케이스 루프

```python
try:
    m = re.match(r'size_(\d+)_\d+$', case_id)
    if not m:
        raise ValueError('케이스 키 형식이 size_{N}_{idx}가 아닙니다.')
    n = int(m.group(1))
    if n not in filters_by_size:
        raise ValueError(f'size_{n} 필터가 로드되지 않았습니다.')
    pattern_input = case['input']
    rows, cols = len(pattern_input), len(pattern_input[0]) if pattern_input else 0
    if rows != n or cols != n:
        raise ValueError(f'크기 불일치: 패턴 {rows}×{cols} vs 필터 {n}×{n}')
    ...
except Exception as e:
    print(f"FAIL (처리 불가): {e}")
    failures.append((case_id, str(e)))
```

`data.json`의 패턴 키(`size_{N}_{idx}`)에서 정규식으로 `N`을 뽑아 해당 크기의 필터가 로드됐는지, 패턴 크기가 필터 크기와 일치하는지 확인합니다. 케이스 하나를 통째로 `try/except`로 감싸 두었기 때문에, 문제가 생기면 그 케이스만 FAIL로 기록되고 `for` 루프는 나머지 케이스를 계속 처리합니다 — 실제로 `size_13` 필터를 지우고 `size_25_1` 패턴 크기를 24×25로 깨뜨린 데이터로 프로그램이 죽지 않는지 검증했습니다.

### 시뮬레이터 최적화(보너스) — `flatten` / `mac_score_1d`

```python
def flatten(matrix):
    flat = []
    for row in matrix:
        flat.extend(row)
    return flat


def mac_score_1d(pattern_flat, filter_flat, n):
    total = 0.0
    for idx in range(n * n):
        total += pattern_flat[idx] * filter_flat[idx]
    return total
```

`flatten`이 2차원 리스트를 길이 N²의 1차원 리스트로 펼치고, `mac_score_1d`는 `range(n * n)`으로 단일 인덱스만 증가시키며 곱해서 더합니다(2차원 버전의 `zip` 중첩 대신 1차원 순차 접근). 같은 패턴/필터를 `flatten`으로 변환해 `mac_score`(2D)와 `mac_score_1d`(1D)에 각각 `measure_avg_ms`로 10회씩 돌려 전/후 시간을 비교합니다(동일 입력·동일 반복 횟수).

## 결과 리포트

### 실제 실행 결과 (`data.json`, 2026-08-05 기준)

```
총 테스트: 6개
통과: 3개
실패: 3개

실패 케이스:
- size_13_2: 동점(UNDECIDED) 처리 규칙에 따라 FAIL
- size_25_1: 동점(UNDECIDED) 처리 규칙에 따라 FAIL
- size_5_1: 동점(UNDECIDED) 처리 규칙에 따라 FAIL
```

### FAIL 원인 분석 — 3건 모두 "수치 비교 문제"

3건의 FAIL은 라벨/스키마 문제가 아니라 **부동소수점 오차**로 인한 것입니다. `data.json`의 `size_5_1`, `size_13_2`, `size_25_1` 필터는 값을 의도적으로 조금씩 어긋나게 설계해(예: 십자가 필터 중앙값을 1.0이 아닌 0.9로, X 필터 대각선을 1.0이 아닌 0.1×여러 칸으로) 수학적으로는 Cross 점수와 X 점수가 정확히 같아지도록(동점) 만들어 놓았습니다. 그런데 컴퓨터가 실수를 더하는 순서와 방식이 Cross 쪽(한 번에 0.9를 더함)과 X 쪽(0.1을 여러 번 나눠서 더함)에서 다르기 때문에, 이진 부동소수점 표현의 반올림 오차가 누적돼 `0.9`와 `0.8999999999999999`처럼 이론상 같아야 할 값이 미세하게 달라집니다. 이 세 케이스는 `abs(score_cross - score_x) < 1e-9` 규칙에 걸려 `UNDECIDED`로 판정되고, 채점 규칙상 `UNDECIDED`는 `expected`가 무엇이든 무조건 FAIL로 집계됩니다. 즉, 로직 오류가 아니라 "동점을 FAIL로 간주한다"는 정책과 부동소수점의 본질적 한계가 만나 생긴, 데이터셋이 의도한 결과입니다. 만약 epsilon 비교 없이 `==`로 직접 비교했다면 두 값이 미세하게 달라서 오히려 (우연히) 한쪽으로 판정이 갈렸을 것이고, 그 판정이 `expected`와 맞는지는 순전히 반올림 방향에 달린 운의 문제가 됩니다 — epsilon 정책은 바로 이런 "우연한 정답/오답"을 막고 "판정 불가"임을 명시적으로 드러내기 위해 필요합니다.

나머지 3건(`size_5_2`, `size_13_1`, `size_25_2`)은 필터 간 점수 차이가 충분히 커서 epsilon 문제 없이 명확하게 판정되었고, 모두 `expected`와 일치해 PASS했습니다.

### 성능 표 및 시간 복잡도(O(N²)) 분석

```
크기       평균 시간(ms)    연산 횟수
-------------------------------------
3×3            0.001           9
5×5            0.002           25
13×13          0.009           169
25×25          0.028           625
```

`mac_score`는 N×N 패턴과 필터의 모든 칸을 정확히 한 번씩 곱하고 더하므로 연산 횟수는 항상 N²입니다(3×3=9, 5×5=25, 13×13=169, 25×25=625 — 표의 "연산 횟수" 열과 정확히 일치). 표의 평균 시간도 이 연산 횟수 증가와 같은 추세로 늘어납니다: 3×3→5×5는 연산 횟수가 약 2.8배(9→25) 늘 때 시간도 약 2배 늘었고, 5×5→13×13은 연산 횟수가 약 6.8배(25→169) 늘 때 시간은 약 4.5배, 13×13→25×25는 연산 횟수가 약 3.7배(169→625) 늘 때 시간은 약 3.1배 늘었습니다. 측정값이 짧은 시간 단위(ms)라 시스템 잡음(캐시, OS 스케줄링 등)의 영향을 받아 배율이 딱 떨어지지는 않지만, 전체적으로 "패턴 한 변의 길이가 k배가 되면 소요 시간은 대략 k²배가 된다"는 O(N²) 경향이 뚜렷하게 나타납니다. 이는 `mac_score`의 이중 for문 구조(바깥 루프 N번 × 안쪽 루프 N번)가 곧 O(N²)이라는 것과 정확히 대응됩니다. 실제 AI 모델의 필터가 이보다 훨씬 크고 개수도 훨씬 많아지면, 이 N²의 증가폭이 CPU의 직렬 처리로는 감당하기 어려운 수준이 되기 때문에 병렬 MAC 연산에 특화된 NPU가 필요해지는 이유이기도 합니다.

### 보너스: 2D 반복문 vs 1차원 배열 최적화 비교 (실측)

```
크기       2D 평균(ms)      1D 평균(ms)      비율(2D/1D)
-------------------------------------------------------
3×3            0.001           0.001           1.73x
5×5            0.002           0.001           1.98x
13×13          0.009           0.006           1.51x
25×25          0.028           0.023           1.21x
```

같은 입력(각 크기의 Cross 필터를 패턴이자 필터로 사용), 같은 반복 횟수(10회)로 `mac_score`(2D, `zip` 중첩)와 `mac_score_1d`(1D, `flatten` 후 단일 인덱스 접근)를 비교했습니다. 모든 크기에서 1D 버전이 더 빨랐습니다(1.2~2배). `zip`은 두 리스트를 순회할 때마다 튜플을 만들어 언패킹하는 오버헤드가 있는 반면, 1차원 배열을 정수 인덱스로 순차 접근하는 쪽이 파이썬 인터프리터 입장에서 더 단순한 연산이라 그 차이가 발생합니다. 다만 크기가 커질수록(25×25) 비율이 1.21x로 줄어드는데, 이는 크기가 커질수록 전체 연산 시간 중 "접근 방식 차이"가 차지하는 비중보다 "곱셈·덧셈 자체의 절대량(N²)"이 차지하는 비중이 커지기 때문으로 해석할 수 있습니다.

## 보너스 과제

| 항목 | 상태 | 설명 |
| --- | --- | --- |
| 패턴 생성기 개발 | ✅ 구현 | `generate_cross(n)` / `generate_x(n)`이 임의 크기 N의 십자가·X 패턴을 만듭니다. 원래는 모드 2 성능 분석에서 `data.json`에 없는 3×3 벤치마크용 데이터가 필요해서 만든 함수인데, 그대로 보너스 요구사항(크기 N을 넣으면 십자가/X를 자동 생성)을 충족합니다. 모드 1/성능 분석 어디서든 `generate_cross(3)`처럼 바로 재사용할 수 있습니다. |
| 시뮬레이터 최적화(1차원 배열 변환 + 전/후 성능 비교) | ✅ 구현 | `flatten`으로 2차원 리스트를 길이 N²의 1차원 리스트로 펼치고, `mac_score_1d`가 단일 인덱스(`range(n*n)`)로 접근하도록 구현했습니다. 동일 입력·동일 반복 횟수(10회)로 2D/1D 버전을 각각 측정해 위 표처럼 비교했고, 모든 크기에서 1D가 더 빨랐습니다. |

## 참고

 [docs/notion_summary.md](docs/notion_summary.md)를 참고
