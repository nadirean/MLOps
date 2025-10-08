from app import welcome_root, health_check


def test_welcome_root():
    response = welcome_root()
    assert response == {"message": "Welcome to the ML API"}


def test_health_check():
    response = health_check()
    assert response == {"status": "ok"}
