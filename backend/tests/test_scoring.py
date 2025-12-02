"""
Tests pour le Module C : Scoring.
"""
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from uuid import uuid4
from decimal import Decimal

from app.main import app
from app.core.database import SessionLocal, engine
from app.models import Base
from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.models.product_score import ProductScore
from app.jobs.scoring_job import ScoringJob


# Créer les tables pour les tests
@pytest.fixture(scope="function")
def db():
    """Créer une session de base de données pour les tests."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Créer un client de test FastAPI."""
    return TestClient(app)


@pytest.fixture
def sample_product_candidate(db: Session):
    """Créer un produit candidat de test."""
    candidate = ProductCandidate(
        asin="B00TEST123",
        title="Test Product",
        category="Electronics",
        source_marketplace="amazon_fr",
        avg_price=Decimal("29.99"),
        estimated_sales_per_day=Decimal("10"),
        status="new",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@pytest.fixture
def sample_sourcing_option(db: Session, sample_product_candidate):
    """Créer une option de sourcing de test."""
    option = SourcingOption(
        product_candidate_id=sample_product_candidate.id,
        supplier_name="Test Supplier",
        sourcing_type="EU_wholesale",
        unit_cost=Decimal("10.00"),
        shipping_cost_unit=Decimal("2.00"),
    )
    db.add(option)
    db.commit()
    db.refresh(option)
    return option


def test_scoring_job_run(db: Session, sample_product_candidate, sample_sourcing_option):
    """Test que ScoringJob crée un ProductScore avec une décision."""
    job = ScoringJob(db)
    stats = job.run()

    assert stats["pairs_scored"] > 0

    # Vérifier qu'un score a été créé
    score = db.query(ProductScore).filter(
        ProductScore.product_candidate_id == sample_product_candidate.id
    ).first()

    assert score is not None
    assert score.decision in ["A_launch", "B_review", "C_drop"]
    assert score.selling_price_target is not None


def test_scoring_endpoint_run(client: TestClient):
    """Test l'endpoint POST /api/v1/jobs/scoring/run retourne 200 avec stats."""
    response = client.post("/api/v1/jobs/scoring/run")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "stats" in data
    assert "pairs_scored" in data["stats"]


def test_get_product_scores(client: TestClient, db: Session, sample_product_candidate, sample_sourcing_option):
    """Test l'endpoint GET /api/v1/products/{product_id}/scores."""
    # D'abord créer un score
    job = ScoringJob(db)
    job.run()

    # Ensuite tester l'endpoint
    response = client.get(f"/api/v1/products/{sample_product_candidate.id}/scores")

    assert response.status_code == 200
    scores = response.json()
    assert isinstance(scores, list)


def test_get_top_scores(client: TestClient, db: Session):
    """Test l'endpoint GET /api/v1/products/scores/top."""
    response = client.get("/api/v1/products/scores/top?decision=A_launch&limit=10")

    assert response.status_code == 200
    scores = response.json()
    assert isinstance(scores, list)


def test_get_top_scores_with_filter(client: TestClient, db: Session):
    """Test que l'endpoint top scores filtre bien par decision."""
    response = client.get("/api/v1/products/scores/top?decision=B_review&limit=5")

    assert response.status_code == 200
    scores = response.json()
    assert isinstance(scores, list)
    # Si des scores existent, vérifier qu'ils ont tous la bonne decision
    for score in scores:
        assert score["decision"] == "B_review"

