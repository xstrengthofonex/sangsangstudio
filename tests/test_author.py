import pytest

from sangsangstudio.services import (
    CreatePostRequest,
    AuthorService,
    AddContentRequest,
    UpdateContentRequest)


@pytest.fixture
def author_service(repository, clock):
    return AuthorService(repository=repository, clock=clock)


@pytest.fixture
def a_post(a_session, author_service):
    create_post_request = CreatePostRequest(user=a_session.user, title="A Title")
    return author_service.create_post(create_post_request)


def test_create_a_post(a_post, author_service):
    assert a_post == author_service.find_post_by_id(a_post.id)


@pytest.fixture
def a_paragraph(a_session, a_post, author_service):
    return author_service.add_content_to_post(AddContentRequest(
        user=a_session.user,
        post_id=a_post.id,
        text="Some text"))

@pytest.fixture
def an_image(a_session, a_post, author_service):
    return author_service.add_content_to_post(AddContentRequest(
        user=a_session.user,
        post_id=a_post.id,
        text="A picture of something",
        src="/image/url"))

def test_add_another_post(a_session, a_post, author_service):
    another_post = author_service.create_post(CreatePostRequest(
        user=a_session.user, title="Another Post"))
    assert author_service.find_all_posts() == [another_post, a_post]


def test_contents(a_session, a_post, author_service, a_paragraph, an_image):
    # User adds to content sections to a post
    # User searches for the post and sees the added contents
    updated_post = author_service.find_post_by_id(a_post.id)
    assert len(updated_post.contents) == 2
    assert [a_paragraph, an_image] == updated_post.contents

    # User updates the paragraph section
    updated_paragraph = author_service.update_content(UpdateContentRequest(
        user=a_session.user,
        content_id=updated_post.id,
        text="Updated text"))
    assert author_service.find_content_by_id(updated_paragraph.id) == updated_paragraph

    # User deletes the image
    author_service.delete_content(a_session, an_image.id)
    updated_post = author_service.find_post_by_id(a_post.id)
    assert len(updated_post.contents) == 1
    assert an_image not in updated_post.contents


