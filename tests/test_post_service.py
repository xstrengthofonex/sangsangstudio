import pytest

from sangsangstudio.services import (
    CreatePostRequest,
    AddParagraphRequest,
    PostService, AddImageRequest)


@pytest.fixture
def post_service(repository, clock):
    return PostService(repository=repository, clock=clock)


@pytest.fixture
def a_post(a_session, post_service):
    create_post_request = CreatePostRequest(
        session_id=a_session.id, title="A Title")
    return post_service.create_post(create_post_request)


def test_create_a_post(a_post, post_service):
    assert a_post == post_service.find_post_by_id(a_post.id)


def test_add_content_to_a_post(a_session, a_post, post_service):
    post_service.add_paragraph_to_post(AddParagraphRequest(
        session_id=a_session.id,
        post_id=a_post.id,
        text="Some text"))
    a_post_with_contents = post_service.add_image_to_post(AddImageRequest(
        session_id=a_session.id,
        post_id=a_post.id,
        text="A picture of something",
        src="/image/url"))
    assert len(a_post_with_contents.contents) == 2
    assert post_service.find_post_by_id(a_post.id) == a_post_with_contents
