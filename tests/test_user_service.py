import pytest

from conftest import user_service, a_user, login_request, a_session
from sangsangstudio.services import (
    UnauthorizedLogin,
    LoginRequest,
    SessionNotFound)


def test_create_user(user_service, a_user):
    assert user_service.find_user(a_user.id) == a_user


def test_login_fail(user_service, a_user):
    with pytest.raises(UnauthorizedLogin):
        request = LoginRequest(username=a_user.username, password="wrongpassword")
        user_service.login(request)


def test_login_success(user_service, a_session):
    assert a_session == user_service.find_session(a_session.key)


def test_multiple_logins_returns_existing_session(user_service, a_session, login_request):
    another_session = user_service.login(login_request)
    assert another_session == a_session


def test_logout_deletes_session(user_service, a_session):
    user_service.logout(a_session.key)
    with pytest.raises(SessionNotFound):
        user_service.find_session(a_session.key)
