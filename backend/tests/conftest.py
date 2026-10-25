import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.security import create_access_token, hash_password
from app.models.organization import Organization
from app.models.user import User, Membership
from app.models.team import Team
from app.models.ticket import Ticket
from app.models.draft import ResponseDraft
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.ai.embeddings import generate_embedding


from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_test_data(db_session):
    org_a = Organization(name="Org Alpha", slug="org-alpha")
    org_b = Organization(name="Org Beta", slug="org-beta")
    db_session.add_all([org_a, org_b])
    db_session.commit()

    user_a = User(
        email="user_a@alpha.com",
        full_name="Agent Alpha",
        hashed_password=hash_password("password123"),
        is_active=True
    )
    user_b = User(
        email="user_b@beta.com",
        full_name="Agent Beta",
        hashed_password=hash_password("password123"),
        is_active=True
    )
    db_session.add_all([user_a, user_b])
    db_session.commit()

    mem_a = Membership(organization_id=org_a.id, user_id=user_a.id, role="admin")
    mem_b = Membership(organization_id=org_b.id, user_id=user_b.id, role="agent")
    db_session.add_all([mem_a, mem_b])
    db_session.commit()

    team_billing = Team(organization_id=org_a.id, name="Billing Support")
    db_session.add(team_billing)
    db_session.commit()

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    return {
        "org_a": org_a,
        "org_b": org_b,
        "user_a": user_a,
        "user_b": user_b,
        "token_a": token_a,
        "token_b": token_b
    }
