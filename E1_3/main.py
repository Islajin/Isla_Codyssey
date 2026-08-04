import json
import os
import re
import time

EPSILON = 1e-9
LABEL_MAP = {'+': 'Cross', 'cross': 'Cross', 'x': 'X'}
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')


def normalize_label(raw):
    key = str(raw).strip().lower()
    if key not in LABEL_MAP:
        raise ValueError(f"알 수 없는 라벨: {raw}")
    return LABEL_MAP[key]


def mac_score(pattern, filter_):
    total = 0.0
    for row_p, row_f in zip(pattern, filter_):
        for p, f in zip(row_p, row_f):
            total += p * f
    return total


def judge_label(score_cross, score_x, eps=EPSILON):
    if abs(score_cross - score_x) < eps:
        return 'UNDECIDED'
    return 'Cross' if score_cross > score_x else 'X'


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


def generate_cross(n):
    mid = n // 2
    return [[1.0 if (r == mid or c == mid) else 0.0 for c in range(n)] for r in range(n)]


def generate_x(n):
    return [[1.0 if (r == c or r + c == n - 1) else 0.0 for c in range(n)] for r in range(n)]


def read_row(n, label):
    while True:
        raw = input().split()
        if len(raw) != n:
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요.")
            continue
        try:
            return [float(x) for x in raw]
        except ValueError:
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요.")


def read_matrix(n, label):
    print(f"{label} ({n}줄 입력, 공백 구분)")
    return [read_row(n, label) for _ in range(n)]


def load_data(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_filters(raw_filters):
    filters_by_size = {}
    for size_key, raw in raw_filters.items():
        m = re.match(r'size_(\d+)$', size_key)
        if not m:
            continue
        n = int(m.group(1))
        try:
            labeled = {}
            for shape_key, matrix in raw.items():
                labeled[normalize_label(shape_key)] = matrix
            if 'Cross' not in labeled or 'X' not in labeled:
                raise ValueError('cross/x 필터가 모두 필요합니다.')
            filters_by_size[n] = labeled
            print(f"✓ size_{n:<3}필터 로드 완료 (Cross, X)")
        except Exception as e:
            print(f"✗ size_{n} 필터 로드 실패: {e}")
    return filters_by_size


def print_perf_table(rows):
    print(f"{'크기':<10} {'평균 시간(ms)':<14} {'연산 횟수'}")
    print("-" * 37)
    for n, avg_ms in rows:
        print(f"{f'{n}×{n}':<10} {avg_ms:<14.3f} {n * n}")


def mode1():
    print("\n#----------------------------------------")
    print("# [1] 필터 입력")
    print("#----------------------------------------")
    filter_a = read_matrix(3, "필터 A")
    filter_b = read_matrix(3, "필터 B")

    print("\n#----------------------------------------")
    print("# [2] 패턴 입력")
    print("#----------------------------------------")
    pattern = read_matrix(3, "패턴")

    print("\n#----------------------------------------")
    print("# [3] MAC 결과")
    print("#----------------------------------------")
    (score_a, score_b), avg_ms = measure_avg_ms(
        lambda: (mac_score(pattern, filter_a), mac_score(pattern, filter_b))
    )
    verdict = judge_label(score_a, score_b)
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_ms:.3f} ms")
    if verdict == 'UNDECIDED':
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {'A' if verdict == 'Cross' else 'B'}")

    print("\n#----------------------------------------")
    print("# [4] 성능 분석 (3×3)")
    print("#----------------------------------------")
    print_perf_table([(3, avg_ms)])


def mode2():
    print("\n#----------------------------------------")
    print("# [1] 필터 로드")
    print("#----------------------------------------")
    try:
        data = load_data(DATA_PATH)
    except Exception as e:
        print(f"data.json 로드 실패: {e}")
        return

    filters_by_size = load_filters(data.get('filters', {}))

    print("\n#----------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#----------------------------------------")
    patterns = data.get('patterns', {})
    total = 0
    passed = 0
    failures = []

    for case_id in sorted(patterns.keys()):
        total += 1
        print(f"--- {case_id} ---")
        case = patterns[case_id]
        try:
            m = re.match(r'size_(\d+)_\d+$', case_id)
            if not m:
                raise ValueError('케이스 키 형식이 size_{N}_{idx}가 아닙니다.')
            n = int(m.group(1))

            if n not in filters_by_size:
                raise ValueError(f'size_{n} 필터가 로드되지 않았습니다.')

            pattern_input = case['input']
            rows = len(pattern_input)
            cols = len(pattern_input[0]) if rows else 0
            if rows != n or cols != n:
                raise ValueError(f'크기 불일치: 패턴 {rows}×{cols} vs 필터 {n}×{n}')

            filt = filters_by_size[n]
            score_cross = mac_score(pattern_input, filt['Cross'])
            score_x = mac_score(pattern_input, filt['X'])
            verdict = judge_label(score_cross, score_x)
            expected = normalize_label(case['expected'])

            print(f"Cross 점수: {score_cross}")
            print(f"X 점수: {score_x}")

            if verdict == 'UNDECIDED':
                print(f"판정: UNDECIDED | expected: {expected} | FAIL (동점 규칙)")
                failures.append((case_id, '동점(UNDECIDED) 처리 규칙에 따라 FAIL'))
            elif verdict == expected:
                print(f"판정: {verdict} | expected: {expected} | PASS")
                passed += 1
            else:
                print(f"판정: {verdict} | expected: {expected} | FAIL")
                failures.append((case_id, f'판정 불일치: 결과 {verdict}, expected {expected}'))
        except Exception as e:
            print(f"FAIL (처리 불가): {e}")
            failures.append((case_id, str(e)))

    print("\n#----------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#----------------------------------------")
    benchmark_inputs = [(3, generate_cross(3), generate_cross(3))]
    for n in sorted(filters_by_size.keys()):
        cross_filter = filters_by_size[n]['Cross']
        benchmark_inputs.append((n, cross_filter, cross_filter))

    perf_rows = []
    for n, pat, filt in benchmark_inputs:
        _, avg_ms = measure_avg_ms(mac_score, pat, filt)
        perf_rows.append((n, avg_ms))
    print_perf_table(perf_rows)

    print("\n#----------------------------------------")
    print("# [3-1] 보너스: 시뮬레이터 최적화 (2D 반복문 vs 1차원 배열 변환)")
    print("#----------------------------------------")
    print(f"{'크기':<10} {'2D 평균(ms)':<14} {'1D 평균(ms)':<14} {'비율(2D/1D)'}")
    print("-" * 55)
    for (n, pat, filt), (_, avg_2d) in zip(benchmark_inputs, perf_rows):
        pat_flat, filt_flat = flatten(pat), flatten(filt)
        _, avg_1d = measure_avg_ms(mac_score_1d, pat_flat, filt_flat, n)
        ratio = avg_2d / avg_1d if avg_1d else float('inf')
        print(f"{f'{n}×{n}':<10} {avg_2d:<14.3f} {avg_1d:<14.3f} {ratio:.2f}x")

    print("\n#----------------------------------------")
    print("# [4] 결과 요약")
    print("#----------------------------------------")
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {len(failures)}개")
    if failures:
        print("\n실패 케이스:")
        for case_id, reason in failures:
            print(f"- {case_id}: {reason}")


def main():
    print("=== Mini NPU Simulator ===\n")
    print("[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    choice = input("선택: ").strip()

    if choice == '1':
        mode1()
    elif choice == '2':
        mode2()
    else:
        print("잘못된 선택입니다. 1 또는 2를 입력하세요.")


if __name__ == '__main__':
    main()
