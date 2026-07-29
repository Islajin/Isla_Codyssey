import json
import os
import random

from cat_quizzes import DEFAULT_QUIZZES
from quiz import Quiz

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state.json')


class QuizGame:
    def __init__(self, state_file=STATE_FILE):
        self.state_file = state_file
        self.quizzes = []
        self.best_score = 0
        self.load_state()

    # ---------- 파일 입출력 ----------
    def load_state(self):
        if not os.path.exists(self.state_file):
            self._load_defaults()
            self.save_state()
            print(f'📂 저장된 데이터가 없어 기본 퀴즈 데이터로 시작합니다. (퀴즈 {len(self.quizzes)}개)')
            return

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            quizzes = [Quiz.from_dict(item) for item in data['quizzes']]
            if not quizzes:
                raise ValueError('퀴즈 데이터가 비어 있습니다.')
            self.quizzes = quizzes
            self.best_score = data.get('best_score', 0)
            print(f'📂 저장된 데이터를 불러왔습니다. (퀴즈 {len(self.quizzes)}개, 최고점수 {self.best_score}점)')
        except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError):
            print('⚠️ 저장된 데이터가 손상되어 기본 퀴즈 데이터로 초기화합니다.')
            self._load_defaults()
            self.save_state()

    def _load_defaults(self):
        self.quizzes = [Quiz.from_dict(item) for item in DEFAULT_QUIZZES]
        self.best_score = 0

    def save_state(self):
        data = {
            'quizzes': [quiz.to_dict() for quiz in self.quizzes],
            'best_score': self.best_score,
        }
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as error:
            print(f'⚠️ 저장 중 오류가 발생했습니다: {error}')

    # ---------- 입력 검증 ----------
    @staticmethod
    def prompt_int(prompt, min_value, max_value):
        while True:
            raw = input(prompt).strip()
            if raw == '':
                print(f'⚠️ 입력이 없습니다. {min_value}-{max_value} 사이의 숫자를 입력하세요.')
                continue
            try:
                value = int(raw)
            except ValueError:
                print(f'⚠️ 잘못된 입력입니다. {min_value}-{max_value} 사이의 숫자를 입력하세요.')
                continue
            if not (min_value <= value <= max_value):
                print(f'⚠️ 잘못된 입력입니다. {min_value}-{max_value} 사이의 숫자를 입력하세요.')
                continue
            return value

    @staticmethod
    def prompt_text(prompt):
        while True:
            raw = input(prompt).strip()
            if raw == '':
                print('⚠️ 입력이 없습니다. 다시 입력하세요.')
                continue
            return raw

    # ---------- 퀴즈 풀기 ----------
    def play_quiz(self):
        if not self.quizzes:
            print('\n⚠️ 등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해주세요.')
            return

        max_count = len(self.quizzes)
        if max_count == 1:
            count = 1
        else:
            count = self.prompt_int(f'\n몇 문제를 푸시겠습니까? (1-{max_count}): ', 1, max_count)

        pool = self.quizzes[:]
        random.shuffle(pool)
        pool = pool[:count]
        print(f'\n📝 퀴즈를 시작합니다! (총 {count}문제)')

        correct = 0
        earned_points = 0.0
        for index, quiz in enumerate(pool, start=1):
            print('-' * 40)
            quiz.display(index)
            is_correct, points = self._ask_single(quiz)
            if is_correct:
                correct += 1
            earned_points += points

        score = round(earned_points / count * 100)
        print('\n' + '=' * 40)
        print(f'🏆 결과: {count}문제 중 {correct}문제 정답! ({score}점)')
        if score > self.best_score:
            self.best_score = score
            print('🎉 새로운 최고 점수입니다!')
        print('=' * 40)
        self.save_state()

    def _ask_single(self, quiz):
        hint_used = False
        while True:
            raw = input('\n정답 입력 (힌트를 보려면 h 입력): ').strip()
            if raw.lower() == 'h':
                print(f'💡 힌트: {quiz.hint}' if quiz.hint else '💡 이 문제에는 힌트가 없습니다.')
                hint_used = True
                continue
            if raw == '':
                print('⚠️ 입력이 없습니다. 1-4 사이의 숫자를 입력하세요.')
                continue
            try:
                answer = int(raw)
            except ValueError:
                print('⚠️ 잘못된 입력입니다. 1-4 사이의 숫자를 입력하세요.')
                continue
            if not (1 <= answer <= 4):
                print('⚠️ 잘못된 입력입니다. 1-4 사이의 숫자를 입력하세요.')
                continue
            break

        if quiz.check_answer(answer):
            if hint_used:
                print('✅ 정답입니다! (힌트 사용으로 점수가 절반만 반영됩니다)')
                return True, 0.5
            print('✅ 정답입니다!')
            return True, 1.0

        print(f'❌ 오답입니다. 정답은 {quiz.answer}번이었습니다.')
        return False, 0.0

    # ---------- 퀴즈 추가 ----------
    def add_quiz(self):
        print('\n📌 새로운 퀴즈를 추가합니다.')
        question = self.prompt_text('문제를 입력하세요: ')
        choices = []
        for i in range(1, 5):
            choices.append(self.prompt_text(f'선택지 {i}: '))
        answer = self.prompt_int('정답 번호 (1-4): ', 1, 4)
        hint = input('힌트 (없으면 그냥 Enter): ').strip()
        self.quizzes.append(Quiz(question, choices, answer, hint))
        self.save_state()
        print('\n✅ 퀴즈가 추가되었습니다!')

    # ---------- 퀴즈 목록 ----------
    def list_quizzes(self):
        if not self.quizzes:
            print('\n⚠️ 등록된 퀴즈가 없습니다.')
            return
        print(f'\n📋 등록된 퀴즈 목록 (총 {len(self.quizzes)}개)')
        print('-' * 40)
        for index, quiz in enumerate(self.quizzes, start=1):
            print(f'[{index}] {quiz.question}')
        print('-' * 40)

    # ---------- 점수 확인 ----------
    def show_score(self):
        if self.best_score == 0:
            print('\n⚠️ 아직 퀴즈를 푼 기록이 없습니다.')
            return
        print(f'\n🏆 최고 점수: {self.best_score}점')

    # ---------- 메뉴 ----------
    def show_menu(self):
        print('\n' + '=' * 40)
        print('        🎯 나만의 퀴즈 게임 🎯')
        print('=' * 40)
        print('1. 퀴즈 풀기')
        print('2. 퀴즈 추가')
        print('3. 퀴즈 목록')
        print('4. 점수 확인')
        print('5. 종료')
        print('=' * 40)

    def run(self):
        try:
            while True:
                self.show_menu()
                choice = self.prompt_int('선택: ', 1, 5)
                if choice == 1:
                    self.play_quiz()
                elif choice == 2:
                    self.add_quiz()
                elif choice == 3:
                    self.list_quizzes()
                elif choice == 4:
                    self.show_score()
                elif choice == 5:
                    self.save_state()
                    print('\n👋 게임을 종료합니다. 다음에 또 만나요!')
                    break
        except (KeyboardInterrupt, EOFError):
            self.save_state()
            print('\n\n👋 입력이 중단되어 안전하게 저장 후 종료합니다.')
