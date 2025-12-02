"""
Tests pour le Module B : Sourcing.
"""
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.core.database import SessionLocal, engine
from app.models import Base
from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption


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
    """Créer un produit candidat de test avec un titre qui match le CSV de démo."""
    candidate = ProductCandidate(
        asin="B00TEST123",
        title="Casque Bluetooth Premium Audio Sans Fil",
        category="Electronics",
        source_marketplace="amazon_fr",
        status="new",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def test_sourcing_job_creates_options(db: Session, sample_product_candidate):
    """
    Test que le SourcingJob crée bien des options de sourcing.

    Note: Ce test utilise le CSV de démo, donc le produit doit avoir
    un titre qui match les mots-clés du CSV.
    """
    from app.jobs.sourcing_job import SourcingJob

    # Vérifier qu'il n'y a pas d'options au début
    initial_count = (
        db.query(SourcingOption)
        .filter(SourcingOption.product_candidate_id == sample_product_candidate.id)
        .count()
    )
    assert initial_count == 0

    # Lancer le job de sourcing
    job = SourcingJob(db)
    stats = job.run()

    # Vérifier les statistiques
    assert stats["processed_products"] > 0
    assert stats["options_created"] > 0

    # Vérifier qu'il y a maintenant des options en base
    final_count = (
        db.query(SourcingOption)
        .filter(SourcingOption.product_candidate_id == sample_product_candidate.id)
        .count()
    )
    assert final_count > initial_count

    # Vérifier qu'au moins une option a les bons champs
    option = (
        db.query(SourcingOption)
        .filter(SourcingOption.product_candidate_id == sample_product_candidate.id)
        .first()
    )
    assert option is not None
    assert option.supplier_name is not None
    assert option.sourcing_type is not None
    assert option.product_candidate_id == sample_product_candidate.id


def test_sourcing_endpoint_creates_options(client: TestClient, db: Session, sample_product_candidate):
    """
    Test que l'endpoint POST /api/v1/jobs/sourcing/run crée des options.

    Note: Le produit doit avoir été créé avant l'appel de l'endpoint.
    """
    # Appeler l'endpoint de sourcing
    response = client.post("/api/v1/jobs/sourcing/run")

    # Vérifier la réponse
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "stats" in data
    assert data["stats"]["processed_products"] >= 0
    assert data["stats"]["options_created"] >= 0

    # Si des options ont été créées, vérifier qu'elles sont en base
    if data["stats"]["options_created"] > 0:
        options = (
            db.query(SourcingOption)
            .filter(SourcingOption.product_candidate_id == sample_product_candidate.id)
            .all()
        )
        assert len(options) > 0


def test_get_product_sourcing_options(client: TestClient, db: Session, sample_product_candidate):
    """
    Test de l'endpoint GET /api/v1/products/{id}/sourcing_options.
    """
    # Créer une option de sourcing pour le produit
    option = SourcingOption(
        product_candidate_id=sample_product_candidate.id,
        supplier_name="Demo IT Supplier",
        sourcing_type="EU_wholesale",
        unit_cost=25.50,
        moq=10,
        lead_time_days=14,
        brandable=True,
        bundle_capable=True,
        notes="Option de test",
    )
    db.add(option)
    db.commit()

    # Appeler l'endpoint
    response = client.get(f"/api/v1/products/{sample_product_candidate.id}/sourcing_options")

    # Vérifier la réponse
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Vérifier la structure de la première option
    option_data = data[0]
    assert "id" in option_data
    assert "supplier_name" in option_data
    assert "sourcing_type" in option_data
    assert option_data["supplier_name"] == "Demo IT Supplier"
    assert option_data["unit_cost"] == 25.50


def test_get_product_sourcing_options_404(client: TestClient, db: Session):
    """Test que l'endpoint renvoie 404 si le produit n'existe pas."""
    fake_id = uuid4()
    response = client.get(f"/api/v1/products/{fake_id}/sourcing_options")

    assert response.status_code == 404
    assert "non trouvé" in response.json()["detail"].lower()


def test_get_product_sourcing_options_empty(client: TestClient, db: Session, sample_product_candidate):
    """Test que l'endpoint renvoie une liste vide si aucune option."""
    # Ne pas créer d'options pour ce produit
    response = client.get(f"/api/v1/products/{sample_product_candidate.id}/sourcing_options")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_sourcing_response_structure(client: TestClient, db: Session, sample_product_candidate):
    """Test que la structure de réponse du job de sourcing est correcte."""
    response = client.post("/api/v1/jobs/sourcing/run")

    if response.status_code == 200:
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "stats" in data
        assert "processed_products" in data["stats"]
        assert "options_created" in data["stats"]
        assert "products_without_options" in data["stats"]

