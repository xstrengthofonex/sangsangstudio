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


@pytest.fixture
def a_paragraph(a_session, a_post, post_service):
    return post_service.add_paragraph_to_post(AddParagraphRequest(
        session_id=a_session.key,
        post_id=a_post.id,
        text="Some text"))

@pytest.fixture
def an_image(a_session, a_post, post_service):
    return post_service.add_image_to_post(AddImageRequest(
        session_id=a_session.key,
        post_id=a_post.id,
        text="A picture of something",
        src="/image/url"))

def test_contents(a_session, a_post, post_service, a_paragraph, an_image):
    updated_post = post_service.find_post_by_id(a_post.id)
    assert len(updated_post.contents) == 2
    assert [a_paragraph, an_image] == updated_post.contents

    post_service.delete_content(a_session, an_image.id)
    updated_post = post_service.find_post_by_id(a_post.id)
    assert len(updated_post.contents) == 1
    assert an_image not in updated_post.contents

