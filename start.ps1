# Script de démarrage PowerShell pour Winner Machine v1

Write-Host "🚀 Démarrage de Winner Machine v1" -ForegroundColor Cyan
Write-Host ""

# Vérifier que docker-compose est disponible
$dockerCompose = Get-Command docker-compose -ErrorAction SilentlyContinue
if (-not $dockerCompose) {
    Write-Host "❌ docker-compose n'est pas installé ou pas dans le PATH" -ForegroundColor Red
    Write-Host "   Veuillez installer Docker Desktop ou Docker Compose" -ForegroundColor Yellow
    exit 1
}

# Aller dans le dossier infra
Push-Location infra

try {
    Write-Host "📋 Configuration de l'environnement..." -ForegroundColor Yellow
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Write-Host "   Création du fichier .env depuis .env.example..." -ForegroundColor Gray
            Copy-Item ".env.example" ".env"
        } else {
            Write-Host "   ⚠️  .env.example non trouvé, utilisez les valeurs par défaut" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ✅ Fichier .env existe déjà" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "🐳 Démarrage des services Docker..." -ForegroundColor Yellow
    docker-compose up -d

    Write-Host ""
    Write-Host "⏳ Attente que les services soient prêts..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5

    Write-Host ""
    Write-Host "🗄️  Application des migrations de base de données..." -ForegroundColor Yellow
    try {
        docker-compose exec -T app alembic upgrade head
    } catch {
        Write-Host "   ⚠️  Les migrations ont peut-être déjà été appliquées" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "✅ Services démarrés !" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Accès aux services :" -ForegroundColor Cyan
    Write-Host "   - Backend API : http://localhost:8000"
    Write-Host "   - Documentation : http://localhost:8000/docs"
    Write-Host "   - Health check : http://localhost:8000/health"
    Write-Host "   - n8n : http://localhost:5678"
    Write-Host ""
    Write-Host "📝 Pour voir les logs :" -ForegroundColor Cyan
    Write-Host "   docker-compose logs -f"
    Write-Host ""
    Write-Host "🧪 Tester le Module A :" -ForegroundColor Cyan
    Write-Host "   curl -X POST http://localhost:8000/api/v1/jobs/discover/run"

} finally {
    Pop-Location
}

