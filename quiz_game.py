class QuizGame:
    def __init__(self):
        pass

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
                    print('(퀴즈 풀기 기능은 추후 구현 예정입니다)')
                elif choice == 2:
                    print('(퀴즈 추가 기능은 추후 구현 예정입니다)')
                elif choice == 3:
                    print('(퀴즈 목록 기능은 추후 구현 예정입니다)')
                elif choice == 4:
                    print('(점수 확인 기능은 추후 구현 예정입니다)')
                elif choice == 5:
                    print('\n👋 게임을 종료합니다. 다음에 또 만나요!')
                    break
        except (KeyboardInterrupt, EOFError):
            print('\n\n👋 입력이 중단되어 안전하게 종료합니다.')
