"""Shared pytest fixtures — Redis via testcontainers (no manual server required)."""
from __future__ import annotations

import pytest
import redis as redis_lib
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="session")
def redis_container():
    """Start a Redis container once for the entire test session.

    Yields a connected redis.Redis client; the container is stopped
    automatically when all tests finish.
    """
    with RedisContainer() as container:
        client = redis_lib.Redis(
            host=container.get_container_host_ip(),
            port=int(container.get_exposed_port(6379)),
            decode_responses=True,
        )
        yield client


@pytest.fixture
def redis_clean(redis_container: redis_lib.Redis) -> redis_lib.Redis:
    """Return a clean Redis client — FLUSHDB is called before each test.

    Function-scoped so every test starts with an empty keyspace,
    preventing state leakage between tests.
    """
    redis_container.flushdb()
    yield redis_container
