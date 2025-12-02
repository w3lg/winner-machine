"""
Tests pour les Modules D/E : Listings.

Tests unitaires et d'intégration pour la génération de listings.
"""
import pytest
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, engine
from app.models import Base
from app.models.product_candidate import ProductCandidate
from app.models.sourcing_option import SourcingOption
from app.models.listing_template import ListingTemplate
from app.models.product_score import ProductScore
from app.jobs.listing_job import ListingJob
from app.services.listing_service import ListingService


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
def db_session(db):
    """Alias pour la fixture db pour compatibilité."""
    return db


@pytest.fixture
def sample_candidate(db):
    """Crée un produit candidat de test."""
    candidate = ProductCandidate(
        asin="B01234567",
        title="Produit Test Électronique Premium",
        category="Electronics & Photo",
        source_marketplace="amazon_fr",
        avg_price=Decimal("29.99"),
        bsr=1234,
        estimated_sales_per_day=Decimal("5.5"),
        reviews_count=150,
        rating=Decimal("4.5"),
        status="selected",
    )
    db_session.add(candidate)
    db_session.commit()
    db_session.refresh(candidate)
    return candidate


@pytest.fixture
def sample_sourcing_option_non_brandable(db, sample_candidate):
    """Crée une option de sourcing non-brandable."""
    option = SourcingOption(
        product_candidate_id=sample_candidate.id,
        supplier_name="Demo Supplier",
        sourcing_type="EU_wholesale",
        unit_cost=Decimal("10.00"),
        shipping_cost_unit=Decimal("2.00"),
        moq=10,
        lead_time_days=7,
        brandable=False,
        bundle_capable=False,
    )
    db_session.add(option)
    db_session.commit()
    db_session.refresh(option)
    return option


@pytest.fixture
def sample_sourcing_option_brandable(db, sample_candidate):
    """Crée une option de sourcing brandable."""
    option = SourcingOption(
        product_candidate_id=sample_candidate.id,
        supplier_name="Demo Brandable Supplier",
        sourcing_type="import_CN",
        unit_cost=Decimal("8.00"),
        shipping_cost_unit=Decimal("1.50"),
        moq=50,
        lead_time_days=14,
        brandable=True,
        bundle_capable=True,
    )
    db_session.add(option)
    db_session.commit()
    db_session.refresh(option)
    return option


@pytest.fixture
def sample_product_score(db, sample_candidate, sample_sourcing_option_brandable):
    """Crée un score A_launch pour le produit."""
    score = ProductScore(
        product_candidate_id=sample_candidate.id,
        sourcing_option_id=sample_sourcing_option_brandable.id,
        selling_price_target=Decimal("29.99"),
        amazon_fees_estimate=Decimal("4.50"),
        logistics_cost_estimate=Decimal("1.50"),
        margin_absolute=Decimal("15.99"),
        margin_percent=Decimal("53.32"),
        estimated_sales_per_day=Decimal("5.5"),
        risk_factor=Decimal("0.1"),
        global_score=Decimal("264.00"),
        decision="A_launch",
    )
    db_session.add(score)
    db_session.commit()
    db_session.refresh(score)
    return score


class TestListingJob:
    """Tests pour ListingJob."""

    def test_listing_job_non_brandable(
        self, db, sample_candidate, sample_sourcing_option_non_brandable
    ):
        """Test 1: ListingJob crée un listing non-brandable."""
        # Vérifier qu'il n'y a pas de listing existant
        existing_listings = (
            db.query(ListingTemplate)
            .filter(ListingTemplate.product_candidate_id == sample_candidate.id)
            .count()
        )
        assert existing_listings == 0

        # Lancer le job
        job = ListingJob(db)
        stats = job.run()

        # Vérifier les stats
        assert stats["products_processed"] == 1
        assert stats["listings_created"] == 1
        assert stats["products_without_sourcing_or_listing"] == 0

        # Vérifier que le listing a été créé
        listing = (
            db_session.query(ListingTemplate)
            .filter(ListingTemplate.product_candidate_id == sample_candidate.id)
            .first()
        )

        assert listing is not None
        assert listing.brandable is False
        assert listing.strategy == "clone_best"
        assert listing.reference_asin == sample_candidate.asin
        assert listing.status == "draft"
        assert listing.title is not None
        assert listing.bullets is not None
        assert isinstance(listing.bullets, list)

    def test_listing_job_brandable(
        self,
        db,
        sample_candidate,
        sample_sourcing_option_brandable,
        sample_product_score,
    ):
        """Test 2: ListingJob crée un listing brandable."""
        # Vérifier qu'il n'y a pas de listing existant
        existing_listings = (
            db.query(ListingTemplate)
            .filter(ListingTemplate.product_candidate_id == sample_candidate.id)
            .count()
        )
        assert existing_listings == 0

        # Lancer le job
        job = ListingJob(db)
        stats = job.run()

        # Vérifier les stats
        assert stats["products_processed"] == 1
        assert stats["listings_created"] == 1

        # Vérifier que le listing a été créé
        listing = (
            db_session.query(ListingTemplate)
            .filter(ListingTemplate.product_candidate_id == sample_candidate.id)
            .first()
        )

        assert listing is not None
        assert listing.brandable is True
        assert listing.strategy == "brand_new"
        assert listing.brand_name is not None
        assert listing.status == "draft"
        assert listing.title is not None
        assert listing.bullets is not None
        assert isinstance(listing.bullets, list)
        assert listing.faq is not None
        assert isinstance(listing.faq, list)

    def test_listing_job_no_sourcing_option(self, db, sample_candidate):
        """Test: ListingJob gère les produits sans option de sourcing."""
        # Lancer le job
        job = ListingJob(db)
        stats = job.run()

        # Vérifier les stats
        assert stats["products_processed"] == 1
        assert stats["listings_created"] == 0
        assert stats["products_without_sourcing_or_listing"] == 1

    def test_listing_job_no_duplicate_listings(
        self, db, sample_candidate, sample_sourcing_option_non_brandable
    ):
        """Test: ListingJob ne crée pas de doublons."""
        # Créer un listing existant
        existing_listing = ListingTemplate(
            product_candidate_id=sample_candidate.id,
            sourcing_option_id=sample_sourcing_option_non_brandable.id,
            brandable=False,
            title="Listing existant",
            status="draft",
        )
        db.add(existing_listing)
        db.commit()

        # Lancer le job
        job = ListingJob(db)
        stats = job.run()

        # Vérifier qu'aucun nouveau listing n'a été créé
        assert stats["products_processed"] == 0
        assert stats["listings_created"] == 0

        # Vérifier qu'il n'y a toujours qu'un seul listing
        listings_count = (
            db.query(ListingTemplate)
            .filter(ListingTemplate.product_candidate_id == sample_candidate.id)
            .count()
        )
        assert listings_count == 1


class TestListingAPI:
    """Tests pour les endpoints API de listings."""

    def test_generate_listings_endpoint(self, client, db, sample_candidate, sample_sourcing_option_non_brandable):
        """Test 3: POST /api/v1/jobs/listing/generate_for_selected."""
        response = client.post("/api/v1/jobs/listing/generate_for_selected")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "stats" in data
        assert data["stats"]["products_processed"] == 1
        assert data["stats"]["listings_created"] == 1

    def test_get_product_listing_templates(
        self, client, db, sample_candidate, sample_sourcing_option_non_brandable
    ):
        """Test 4: GET /api/v1/products/{id}/listing_templates."""
        # Créer un listing d'abord
        listing = ListingTemplate(
            product_candidate_id=sample_candidate.id,
            sourcing_option_id=sample_sourcing_option_non_brandable.id,
            brandable=False,
            title="Test Listing",
            status="draft",
        )
        db.add(listing)
        db.commit()

        # Appeler l'endpoint
        response = client.get(f"/api/v1/products/{sample_candidate.id}/listing_templates")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Test Listing"
        assert data[0]["brandable"] is False
        assert data[0]["status"] == "draft"

    def test_get_product_listing_templates_not_found(self, client):
        """Test: GET /api/v1/products/{id}/listing_templates avec produit inexistant."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/products/{fake_id}/listing_templates")

        assert response.status_code == 404

    def test_get_top_draft_listings(
        self, client, db, sample_candidate, sample_sourcing_option_non_brandable
    ):
        """Test: GET /api/v1/listings/top_drafts."""
        # Créer quelques listings en draft
        listing1 = ListingTemplate(
            product_candidate_id=sample_candidate.id,
            sourcing_option_id=sample_sourcing_option_non_brandable.id,
            brandable=False,
            title="Listing Draft 1",
            status="draft",
        )
        db.add(listing1)
        db.commit()

        # Appeler l'endpoint
        response = client.get("/api/v1/listings/top_drafts?limit=10")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(item["status"] == "draft" for item in data)


class TestExportCSV:
    """Tests pour l'export CSV."""

    def test_export_csv_with_listing_ids(
        self, client, db, sample_candidate, sample_sourcing_option_non_brandable
    ):
        """Test 5: POST /api/v1/listings/export_csv avec listing_ids."""
        # Créer un listing
        listing = ListingTemplate(
            product_candidate_id=sample_candidate.id,
            sourcing_option_id=sample_sourcing_option_non_brandable.id,
            brandable=False,
            title="Test Listing Export",
            bullets=["Bullet 1", "Bullet 2"],
            description="Description test",
            status="draft",
        )
        db.add(listing)
        db.commit()

        # Exporter
        response = client.post(
            "/api/v1/listings/export_csv",
            json={"listing_ids": [str(listing.id)], "export_all_drafts": False},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

        # Vérifier le contenu CSV
        csv_content = response.text
        assert "asin" in csv_content
        assert "title" in csv_content
        assert "Test Listing Export" in csv_content

    def test_export_csv_all_drafts(
        self, client, db, sample_candidate, sample_sourcing_option_non_brandable
    ):
        """Test: POST /api/v1/listings/export_csv avec export_all_drafts."""
        # Créer quelques listings
        listing1 = ListingTemplate(
            product_candidate_id=sample_candidate.id,
            sourcing_option_id=sample_sourcing_option_non_brandable.id,
            brandable=False,
            title="Draft 1",
            status="draft",
        )
        listing2 = ListingTemplate(
            product_candidate_id=sample_candidate.id,
            sourcing_option_id=sample_sourcing_option_non_brandable.id,
            brandable=False,
            title="Draft 2",
            status="ready",  # Ne sera pas exporté
        )
        db.add_all([listing1, listing2])
        db.commit()

        # Exporter tous les drafts
        response = client.post(
            "/api/v1/listings/export_csv",
            json={"export_all_drafts": True},
        )

        assert response.status_code == 200
        csv_content = response.text
        assert "Draft 1" in csv_content
        assert "Draft 2" not in csv_content  # Status ready, pas draft

    def test_export_csv_empty_request(self, client):
        """Test: POST /api/v1/listings/export_csv sans paramètres."""
        response = client.post(
            "/api/v1/listings/export_csv",
            json={},
        )

        assert response.status_code == 400

    def test_export_csv_no_listings(self, client):
        """Test: POST /api/v1/listings/export_csv avec aucun listing."""
        response = client.post(
            "/api/v1/listings/export_csv",
            json={"export_all_drafts": True},
        )

        assert response.status_code == 404

