from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import pytest

from sangsangstudio.clock import Clock
from sangsangstudio.entities import Post
from sangsangstudio.repositories import Repository
from sangsangstudio.services import UserDto, UserService


@dataclass(frozen=True)
class CreatePostRequest:
    session_id: str
    title: str


class PostStatusDto(Enum):
    DRAFT = 0
    PUBLISHED = 1


@dataclass(frozen=True)
class PostDto:
    id: int
    author: UserDto
    created_on: datetime
    title: str
    status: PostStatusDto


class PostService:
    def __init__(self, repository: Repository, clock: Clock):
        self.clock = clock
        self.repository = repository

    def create_post(self, request: CreatePostRequest) -> PostDto:
        session = self.repository.find_session_by_id(request.session_id)
        post = Post(author=session.user, created_on=self.clock.now(), title=request.title)
        self.repository.save_post(post)
        return self.post_to_dto(post)

    def find_post_by_id(self, post_id: int) -> PostDto:
        post = self.repository.find_post_by_id(post_id)
        return self.post_to_dto(post)

    @staticmethod
    def post_to_dto(post: Post) -> PostDto:
        return PostDto(
            id=post.id,
            title=post.title,
            created_on=post.created_on,
            author=UserService.user_to_dto(post.author),
            status=PostStatusDto(post.status.value))


@pytest.fixture
def post_service(repository, clock):
    return PostService(repository=repository, clock=clock)


def test_create_a_post(a_session, post_service):
    create_post_request = CreatePostRequest(
        session_id=a_session.id, title="A Title")
    a_post = post_service.create_post(create_post_request)
    assert a_post == post_service.find_post_by_id(a_post.id)
