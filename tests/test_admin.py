import pytest

from sangsangstudio.services import RegisterAdminRequest, AdminService


@pytest.fixture
def admin_service(user_service, repository, clock):
    return AdminService(repository, clock)


def test_admin_journey(admin_service, a_user):
    request = RegisterAdminRequest(
        user_id=a_user.id,
        first_name="Ally",
        family_name="Jang")
    an_admin = admin_service.register_admin(request)
    assert admin_service.find_admin_by_id(an_admin.id) == an_admin
