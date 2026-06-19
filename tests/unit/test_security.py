from src.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password


def test_password_hashing():
    password = "supersecretpassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_create_tokens():
    subject = "user123"
    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject)

    assert isinstance(access_token, str)
    assert isinstance(refresh_token, str)
    assert len(access_token) > 0
    assert len(refresh_token) > 0
