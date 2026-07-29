from quiz import Quiz

DEFAULT_QUIZZES = [
    {
        'question': '고양이가 하루 평균 자는 시간은 약 몇 시간일까요?',
        'choices': ['8시간', '12시간', '16시간', '20시간'],
        'answer': 3,
        'hint': '고양이는 하루의 3분의 2 가까이를 잠으로 보냅니다.',
    },
    {
        'question': '고양이 수염(vibrissae)의 주요 기능은 무엇일까요?',
        'choices': ['장식용', '주변 공간과 크기 감지', '냄새 맡기', '체온 조절'],
        'answer': 2,
        'hint': '어두운 곳이나 좁은 틈을 지날 때 특히 유용합니다.',
    },
    {
        'question': '다음 중 고양이 품종이 아닌 것은?',
        'choices': ['러시안 블루', '스코티시 폴드', '페르시안', '골든리트리버'],
        'answer': 4,
        'hint': '보기 중 하나는 개(犬) 품종입니다.',
    },
    {
        'question': '집고양이의 야생 조상으로 알려진 동물은?',
        'choices': ['회색늑대', '아프리카들고양이', '스라소니', '사막여우'],
        'answer': 2,
        'hint': '중동 지역 사막에 서식하던 작은 야생 고양이입니다.',
    },
    {
        'question': '고양이가 꼬리를 세우고 살짝 흔들 때 일반적으로 나타내는 감정은?',
        'choices': ['불안', '반가움/친근함', '공격 준비', '졸림'],
        'answer': 2,
        'hint': '주인을 반길 때 자주 보이는 행동입니다.',
    },
    {
        'question': '고양이 눈이 어두운 곳에서도 잘 보이도록 도와주는 반사판 구조의 이름은?',
        'choices': ['홍채', '각막', '타페텀 루시덤', '수정체'],
        'answer': 3,
        'hint': '어두운 곳에서 고양이 눈이 빛나 보이는 이유입니다.',
    },
    {
        'question': '세계에서 가장 큰 고양이 품종으로 알려진 것은?',
        'choices': ['먼치킨', '메인쿤', '싱가푸라', '아비시니안'],
        'answer': 2,
        'hint': '이름에 미국의 한 주 이름이 들어갑니다.',
    },
]


class QuizGame:
    def __init__(self):
        self.quizzes = [Quiz.from_dict(item) for item in DEFAULT_QUIZZES]

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

        total = len(self.quizzes)
        print(f'\n📝 퀴즈를 시작합니다! (총 {total}문제)')

        correct = 0
        for index, quiz in enumerate(self.quizzes, start=1):
            print('-' * 40)
            quiz.display(index)
            answer = self.prompt_int('\n정답 입력: ', 1, 4)
            if quiz.check_answer(answer):
                print('✅ 정답입니다!')
                correct += 1
            else:
                print(f'❌ 오답입니다. 정답은 {quiz.answer}번이었습니다.')

        score = round(correct / total * 100)
        print('\n' + '=' * 40)
        print(f'🏆 결과: {total}문제 중 {correct}문제 정답! ({score}점)')
        print('=' * 40)

    # ---------- 퀴즈 추가 ----------
    def add_quiz(self):
        print('\n📌 새로운 퀴즈를 추가합니다.')
        question = self.prompt_text('문제를 입력하세요: ')
        choices = []
        for i in range(1, 5):
            choices.append(self.prompt_text(f'선택지 {i}: '))
        answer = self.prompt_int('정답 번호 (1-4): ', 1, 4)
        self.quizzes.append(Quiz(question, choices, answer))
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
                    print('(점수 확인 기능은 추후 구현 예정입니다)')
                elif choice == 5:
                    print('\n👋 게임을 종료합니다. 다음에 또 만나요!')
                    break
        except (KeyboardInterrupt, EOFError):
            print('\n\n👋 입력이 중단되어 안전하게 종료합니다.')
