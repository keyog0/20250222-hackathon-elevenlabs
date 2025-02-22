import secrets


def create_secret_key(length: int = 64) -> str:
    """
    비밀 키를 생성합니다.
    config.py에 비밀 키 생성해서 넣어주세요.
    """
    return secrets.token_urlsafe(length)


if __name__ == "__main__":
    print(create_secret_key())
