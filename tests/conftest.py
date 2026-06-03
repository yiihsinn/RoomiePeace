import os


def pytest_configure():
    os.environ["ROOMIEPEACE_DISABLE_LLM_NLU"] = "1"
