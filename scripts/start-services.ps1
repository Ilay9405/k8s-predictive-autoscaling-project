# scripts/start-services.ps1 — Start all PredScale services as background jobs and open browser tabs

Write-Host "Starting PredScale Background Services..." -ForegroundColor Green

# Stop any old running jobs first to prevent port conflicts
Get-Job | Where-Object { $_.Name -match "argocd-ui|predscale-dashboard|locust-ui|prometheus-ui|inference-api" } | Stop-Job -ErrorAction SilentlyContinue | Remove-Job -ErrorAction SilentlyContinue

# 1. ArgoCD Web UI (Port 8080)
Start-Job -Name "argocd-ui" -ScriptBlock { kubectl port-forward svc/argocd-server -n argocd 8080:443 } | Out-Null
Write-Host "  [+] ArgoCD UI:          https://localhost:8080 (User: admin | Pass: YeqWrJWWSOfTNlqa)" -ForegroundColor Cyan

# 2. PredScale Dashboard (Port 3000)
Start-Job -Name "predscale-dashboard" -ScriptBlock { kubectl port-forward -n predscalens svc/dashboard-service 3000:80 } | Out-Null
Write-Host "  [+] PredScale Dashboard: http://localhost:3000" -ForegroundColor Cyan

# 3. Locust Traffic Generator (Port 8089)
Start-Job -Name "locust-ui" -ScriptBlock { kubectl port-forward -n predscalens svc/locust-service 8089:8089 } | Out-Null
Write-Host "  [+] Locust Load UI:      http://localhost:8089" -ForegroundColor Cyan

# 4. Prometheus Monitoring (Port 9090)
Start-Job -Name "prometheus-ui" -ScriptBlock { kubectl port-forward -n monitoring svc/prometheus-k8s 9090:9090 } | Out-Null
Write-Host "  [+] Prometheus UI:       http://localhost:9090" -ForegroundColor Cyan

# 5. ML Inference API Docs (Port 8000)
Start-Job -Name "inference-api" -ScriptBlock { kubectl port-forward -n predscalens svc/ml-inference-service 8000:8000 } | Out-Null
Write-Host "  [+] Inference API Docs:   http://localhost:8000/docs" -ForegroundColor Cyan

Write-Host "All 5 background services are running!" -ForegroundColor Yellow
Write-Host "Opening browser tabs..." -ForegroundColor Green

# Open browser tabs automatically
Start-Process "https://localhost:8080"
Start-Process "http://localhost:3000"
Start-Process "http://localhost:8089"
Start-Process "http://localhost:9090"
Start-Process "http://localhost:8000/docs"

Write-Host "To stop services later, run: .\scripts\stop-services.ps1" -ForegroundColor Yellow
