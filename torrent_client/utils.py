from random import randint


def generate_peer_id() -> str:
    return f"-PC0001-{''.join([str(randint(0, 9)) for _ in range(12)])}"