from roomiepeace.guardrails import guardrail_check


def test_playful_output_is_safe():
    result = guardrail_check("垃圾桶目前進入最終型態，拜託今晚拯救一下人類文明。")
    assert result["safe"] is True


def test_personal_attack_is_unsafe():
    result = guardrail_check("你是垃圾人又是廢物，快去倒垃圾。")
    assert result["safe"] is False
    assert "contains_personal_attack" in result["issues"]


def test_court_disclaimer_is_safe():
    result = guardrail_check("室友法庭只作為娛樂提醒，不具法律效力。")
    assert result["safe"] is True
