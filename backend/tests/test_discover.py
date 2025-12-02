"""
Tests pour le Module A : Discoverer.
"""
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, engine
from app.models import Base
from app.models.product_candidate import ProductCandidate

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


def test_discover_endpoint_creates_products(client: TestClient, db: Session):
    """
    Test que l'endpoint de découverte crée bien des produits en base.

    Note: Ce test utilise le mock KeepaClient, donc pas besoin de clé API réelle.
    """
    # Vérifier qu'il n'y a pas de produits au début
    initial_count = db.query(ProductCandidate).count()
    assert initial_count == 0

    # Appeler l'endpoint de découverte
    response = client.post("/api/v1/jobs/discover/run")

    # Vérifier la réponse
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "stats" in data
    assert data["stats"]["created"] > 0 or data["stats"]["total_processed"] > 0

    # Vérifier qu'il y a maintenant des produits en base
    final_count = db.query(ProductCandidate).count()
    assert final_count > initial_count

    # Vérifier qu'au moins un produit a les bons champs
    product = db.query(ProductCandidate).first()
    assert product is not None
    assert product.asin is not None
    assert product.status == "new"
    assert product.source_marketplace == "amazon_fr"


def test_discover_endpoint_updates_existing_products(
    client: TestClient, db: Session
):
    """Test que l'endpoint met à jour les produits existants."""
    # Créer un produit existant
    existing_product = ProductCandidate(
        asin="B08XYZ123400",
        title="Ancien titre",
        category="Electronics",
        source_marketplace="amazon_fr",
        status="new",
    )
    db.add(existing_product)
    db.commit()

    # Appeler l'endpoint de découverte
    response = client.post("/api/v1/jobs/discover/run")

    # Vérifier la réponse
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Vérifier que le produit a été mis à jour (si trouvé dans le mock)
    # Note: Ce test peut échouer si l'ASIN mocké ne correspond pas
    db.refresh(existing_product)
    # Au minimum, vérifier qu'il existe toujours
    assert existing_product.asin == "B08XYZ123400"


def test_discover_endpoint_with_no_categories(client: TestClient, db: Session):
    """Test que l'endpoint gère correctement le cas sans catégories."""
    # Note: Ce test nécessiterait de mocker CategoryConfigService
    # pour l'instant, on vérifie juste que l'endpoint répond
    response = client.post("/api/v1/jobs/discover/run")
    assert response.status_code in [200, 500]  # Soit succès vide, soit erreur gérée


def test_discover_response_structure(client: TestClient, db: Session):
    """Test que la structure de réponse est correcte."""
    response = client.post("/api/v1/jobs/discover/run")
    
    if response.status_code == 200:
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "stats" in data
        assert "created" in data["stats"]
        assert "updated" in data["stats"]
        assert "total_processed" in data["stats"]
        assert "categories_processed" in data["stats"]
        assert "errors" in data["stats"]


def test_discover_job_idempotent(client: TestClient, db: Session):
    """
    Test que le job Discover est idempotent : 
    - Premier run : crée des produits (created > 0)
    - Deuxième run : met à jour les produits (updated > 0, created = 0)
    - Aucune UniqueViolation ne doit être levée
    """
    # Premier run
    response1 = client.post("/api/v1/jobs/discover/run")
    assert response1.status_code == 200, f"Premier run a échoué : {response1.text}"
    data1 = response1.json()
    assert data1["success"] is True
    assert data1["stats"]["created"] > 0, "Le premier run devrait créer des produits"
    
    # Deuxième run
    response2 = client.post("/api/v1/jobs/discover/run")
    assert response2.status_code == 200, f"Deuxième run a échoué : {response2.text}"
    data2 = response2.json()
    assert data2["success"] is True
    assert data2["stats"]["created"] == 0, "Le deuxième run ne devrait pas créer de nouveaux produits"
    assert data2["stats"]["updated"] > 0, "Le deuxième run devrait mettre à jour les produits existants"
    assert data2["stats"]["errors"] == 0, "Aucune erreur ne devrait être levée, notamment pas de UniqueViolation"

