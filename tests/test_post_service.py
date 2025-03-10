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
        session_key=a_session.key, title="A Title")
    return post_service.create_post(create_post_request)


def test_create_a_post(a_post, post_service):
    assert a_post == post_service.find_post_by_id(a_post.id)


def test_add_content_to_a_post(a_session, a_post, post_service):
    paragraph = post_service.add_paragraph_to_post(AddParagraphRequest(
        session_id=a_session.key,
        post_id=a_post.id,
        text="Some text"))
    image = post_service.add_image_to_post(AddImageRequest(
        session_id=a_session.key,
        post_id=a_post.id,
        text="A picture of something",
        src="/image/url"))
    updated_post = post_service.find_post_by_id(a_post.id)
    assert len(updated_post.contents) == 2
    assert [paragraph, image] == updated_post.contents
