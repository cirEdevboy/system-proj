from app.security import hash_password, verify_password

def test_password():
    h=hash_password('12345678')
    assert verify_password('12345678',h)
    assert not verify_password('errada',h)
