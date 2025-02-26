from sangsangstudio.entities import User


def test_repository(repository):
    user = User(id=1, username="user")
    repository.save_user(user)
    assert repository.find_user(user.id) == user

