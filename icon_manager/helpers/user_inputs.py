from typing import Optional

EMPTY_LINE = ""
QUESTION_LINE = "========================================================================"
SEPARATION_LINE = "------------------------------------------------------------------------"


def ask_user(message: str, information: Optional[str] = None, strip_quotation: bool = True) -> str:
    print(QUESTION_LINE)
    print(EMPTY_LINE)
    if information is not None:
        print(information)
        print(SEPARATION_LINE)
        print(EMPTY_LINE)
    answer = input(message)
    if strip_quotation:
        return answer.strip('"')
    print(EMPTY_LINE)
    print(QUESTION_LINE)
    return answer


def ask_user_for_path(message: str, information: Optional[str] = None, strip_quotation: bool = True) -> str:
    return ask_user(message, information, strip_quotation)


def ask_user_yes_no_question(question: str, information: Optional[str] = None, strip_quotation: bool = True) -> bool:
    answer = ask_user(question, information, strip_quotation)
    return answer in ('y', 'Y', 'j', 'J')
