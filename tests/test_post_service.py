import pytest

from sangsangstudio.services import (
    CreatePostRequest,
    PostService,
    AddContentRequest,
    UpdateContentRequest)


@pytest.fixture
def post_service(repository, clock):
    return PostService(repository=repository, clock=clock)


@pytest.fixture
def a_post(a_session, post_service):
    create_post_request = CreatePostRequest(user=a_session.user, title="A Title")
    return post_service.create_post(create_post_request)


def test_create_a_post(a_post, post_service):
    assert a_post == post_service.find_post_by_id(a_post.id)


@pytest.fixture
def a_paragraph(a_session, a_post, post_service):
    return post_service.add_content_to_post(AddContentRequest(
        user=a_session.user,
        post_id=a_post.id,
        text="Some text"))

@pytest.fixture
def an_image(a_session, a_post, post_service):
    return post_service.add_content_to_post(AddContentRequest(
        user=a_session.user,
        post_id=a_post.id,
        text="A picture of something",
        src="/image/url"))

def test_add_another_post(a_session, a_post, post_service):
    another_post = post_service.create_post(CreatePostRequest(
        user=a_session.user, title="Another Post"))
    assert post_service.find_all_posts() == [another_post, a_post]


def test_contents(a_session, a_post, post_service, a_paragraph, an_image):
    # User adds to content sections to a post
    # User searches for the post and sees the added contents
    updated_post = post_service.find_post_by_id(a_post.id)
    assert len(updated_post.contents) == 2
    assert [a_paragraph, an_image] == updated_post.contents

    # User updates the paragraph section
    updated_paragraph = post_service.update_content(UpdateContentRequest(
        user=a_session.user,
        content_id=updated_post.id,
        text="Updated text"))
    updated_post = post_service.find_post_by_id(a_post.id)
    assert updated_paragraph in updated_post.contents

    # User deletes the image
    post_service.delete_content(a_session, an_image.id)
    updated_post = post_service.find_post_by_id(a_post.id)
    assert len(updated_post.contents) == 1
    assert an_image not in updated_post.contents


