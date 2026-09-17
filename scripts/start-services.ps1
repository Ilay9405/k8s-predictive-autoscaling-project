# scripts/start-services.ps1 — Start all PredScale services in visible PowerShell windows that stay open (-NoExit)

Write-Host "Starting PredScale Port-Forwarding Windows..." -ForegroundColor Green

# 1. ArgoCD Web UI (Port 8080)
Write-Host "  [+] Opening ArgoCD UI port-forward window (Port 8080)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '--- ArgoCD UI (Port 8080) ---' -ForegroundColor Green; kubectl port-forward svc/argocd-server -n argocd 8080:443"

# 2. PredScale Dashboard (Port 3000)
Write-Host "  [+] Opening PredScale Dashboard port-forward window (Port 3000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '--- PredScale Dashboard (Port 3000) ---' -ForegroundColor Green; kubectl port-forward -n predscalens svc/dashboard-service 3000:80"

# 3. Prometheus Monitoring (Port 9090)
Write-Host "  [+] Opening Prometheus UI port-forward window (Port 9090)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '--- Prometheus UI (Port 9090) ---' -ForegroundColor Green; kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090"

# 4. ML Inference API Docs (Port 8000)
Write-Host "  [+] Opening Inference API Docs port-forward window (Port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '--- Inference API Docs (Port 8000) ---' -ForegroundColor Green; kubectl port-forward -n predscalens svc/ml-inference-service 8000:8000"

# Give port-forwards 3 seconds to establish connections before opening browser tabs
Start-Sleep -Seconds 3

Write-Host "Opening browser tabs..." -ForegroundColor Green
cmd.exe /c start https://localhost:8080
cmd.exe /c start http://localhost:3000
cmd.exe /c start http://localhost:9090
cmd.exe /c start http://localhost:8000/docs

Write-Host "All service windows launched with -NoExit (they will stay open to show status and errors)." -ForegroundColor Yellow
