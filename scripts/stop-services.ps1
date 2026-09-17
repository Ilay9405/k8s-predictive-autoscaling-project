# scripts/stop-services.ps1 — Stop all PredScale background port-forwarding jobs

Write-Host "🛑 Stopping PredScale Background Services..." -ForegroundColor Red

Get-Job | Where-Object { $_.Name -match "argocd-ui|predscale-dashboard|locust-ui|prometheus-ui|inference-api" } | Stop-Job -ErrorAction SilentlyContinue | Remove-Job -ErrorAction SilentlyContinue

Write-Host "All PredScale background port-forwardings stopped cleanly." -ForegroundColor Green
