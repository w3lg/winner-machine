"""
Tests pour les routes dashboard.
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
def sample_winner_data(db: Session):
    """Créer des données de test : produits, sourcing, scores."""
    # Créer un produit candidat
    product = ProductCandidate(
        id=uuid4(),
        asin="TEST001",
        title="Produit de test winner",
        category="Test Category",
        source_marketplace="amazon_fr",
        avg_price=Decimal("25.99"),
        status="scored",
    )
    db.add(product)
    db.flush()
    
    # Créer une option de sourcing
    sourcing = SourcingOption(
        id=uuid4(),
        product_candidate_id=product.id,
        supplier_name="Test Supplier",
        sourcing_type="EU_wholesale",
        unit_cost=Decimal("10.00"),
    )
    db.add(sourcing)
    db.flush()
    
    # Créer un score
    score = ProductScore(
        id=uuid4(),
        product_candidate_id=product.id,
        sourcing_option_id=sourcing.id,
        selling_price_target=Decimal("25.99"),
        margin_absolute=Decimal("12.00"),
        margin_percent=Decimal("46.17"),
        estimated_sales_per_day=Decimal("10.5"),
        global_score=Decimal("120.5"),
        decision="A_launch",
        risk_factor=Decimal("0.1"),
    )
    db.add(score)
    db.commit()
    
    return {
        "product": product,
        "sourcing": sourcing,
        "score": score,
    }


def test_get_winners_no_filters(client: TestClient, db: Session, sample_winner_data):
    """Test récupération des winners sans filtres."""
    response = client.get("/api/v1/dashboard/winners")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data
    assert len(data["items"]) >= 1
    
    # Vérifier que le produit de test est présent
    items = data["items"]
    test_item = next((item for item in items if item["asin"] == "TEST001"), None)
    assert test_item is not None
    assert test_item["decision"] == "A_launch"


def test_get_winners_with_filters(client: TestClient, db: Session, sample_winner_data):
    """Test récupération des winners avec filtres."""
    # Test avec decision filter
    response = client.get("/api/v1/dashboard/winners?decision=A_launch")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Tous les items doivent avoir decision=A_launch
    for item in data["items"]:
        assert item["decision"] == "A_launch"
    
    # Test avec min_margin_percent
    response = client.get("/api/v1/dashboard/winners?min_margin_percent=40")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Tous les items doivent avoir margin_percent >= 40
    for item in data["items"]:
        if item["margin_percent"] is not None:
            assert float(item["margin_percent"]) >= 40


def test_get_winners_empty_result(client: TestClient, db: Session):
    """Test avec des filtres qui ne retournent aucun résultat."""
    response = client.get("/api/v1/dashboard/winners?min_global_score=999999")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["items"]) == 0

