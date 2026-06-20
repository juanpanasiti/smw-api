from src.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password


def test_password_hashing():
    """
    Test password hashing and verification functionality.

    Verifies that get_password_hash hashes passwords securely and verify_password
    accurately matches passwords against their hashes.
    """
    password = "supersecretpassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_tokens():
    """
    Test the generation of access and refresh JSON Web Tokens (JWT).

    Verifies that create_access_token and create_refresh_token generate non-empty
    JWT string tokens for a given subject.
    """
    subject = "user123"
    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject)

    assert isinstance(access_token, str)
    assert isinstance(refresh_token, str)
    assert len(access_token) > 0
    assert len(refresh_token) > 0
