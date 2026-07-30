class Quiz:
    def __init__(self, question, choices, answer, hint=''):
        self.question = question
        self.choices = choices
        self.answer = answer
        self.hint = hint

    def display(self, index):
        print(f'\n[문제 {index}]')
        print(self.question)
        print()
        for i, choice in enumerate(self.choices, start=1):
            print(f'{i}. {choice}')

    def check_answer(self, user_answer):
        return user_answer == self.answer

    def to_dict(self):
        return {
            'question': self.question,
            'choices': self.choices,
            'answer': self.answer,
            'hint': self.hint,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            question=data['question'],
            choices=data['choices'],
            answer=data['answer'],
            hint=data.get('hint', ''),
        )
