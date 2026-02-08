$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = (Resolve-Path "$PSScriptRoot\..").Path
$env:PYTHONPATH = "$Root\src"

$PythonExe = Join-Path $Root "venv\\Scripts\\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$Docs = Join-Path $Root "docs"
$EnvLog = Join-Path $Docs "verification_env.txt"
$SeedLog = Join-Path $Docs "verification_seed_reset.txt"
$HealthLog = Join-Path $Docs "verification_health.txt"
$TestSeedLog = Join-Path $Docs "verification_test_seed_smoke.txt"
$TestRulesLog = Join-Path $Docs "verification_test_enrollment_rules.txt"
$TestConcLog = Join-Path $Docs "verification_test_concurrency_capacity.txt"

Push-Location $Root
try {
    Write-Host "Step0: environment"
    "python --version" | Out-File -Encoding utf8 $EnvLog
    & $PythonExe --version 2>&1 | Out-File -Append -Encoding utf8 $EnvLog
    "PowerShell" | Out-File -Append -Encoding utf8 $EnvLog
    $PSVersionTable.PSVersion | Out-String | Out-File -Append -Encoding utf8 $EnvLog
    "OS" | Out-File -Append -Encoding utf8 $EnvLog
    Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, OSArchitecture | Out-String | Out-File -Append -Encoding utf8 $EnvLog

    Write-Host "Step1: seed reset"
    & $PythonExe -m app.db reset 2>&1 | Tee-Object -FilePath $SeedLog
    if ($LASTEXITCODE -ne 0) { throw "Seed reset failed" }

    Write-Host "Step2: start server"
    $Server = Start-Process -FilePath $PythonExe -ArgumentList @("-m","uvicorn","app.main:app","--app-dir","src","--host","127.0.0.1","--port","8000") -WorkingDirectory $Root -PassThru -WindowStyle Hidden
    try {
        $Deadline = (Get-Date).AddSeconds(60)
        $Healthy = $false
        while (Get-Date -lt $Deadline) {
            try {
                $Resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
                if ($Resp.StatusCode -eq 200) {
                    $Resp | Select-Object StatusCode, Content | Out-File -Encoding utf8 $HealthLog
                    $Healthy = $true
                    break
                }
            } catch {
                Start-Sleep -Seconds 2
            }
        }
        if (-not $Healthy) { throw "Health check failed or timed out" }

        Write-Host "Step3: tests"
        & $PythonExe -m unittest src/tests/test_seed_smoke.py 2>&1 | Tee-Object -FilePath $TestSeedLog
        if ($LASTEXITCODE -ne 0) { throw "test_seed_smoke failed" }
        & $PythonExe -m unittest src/tests/test_enrollment_rules.py 2>&1 | Tee-Object -FilePath $TestRulesLog
        if ($LASTEXITCODE -ne 0) { throw "test_enrollment_rules failed" }
        & $PythonExe -m unittest src/tests/test_concurrency_capacity.py 2>&1 | Tee-Object -FilePath $TestConcLog
        if ($LASTEXITCODE -ne 0) { throw "test_concurrency_capacity failed" }
    } finally {
        if ($Server -and -not $Server.HasExited) {
            Stop-Process -Id $Server.Id -Force
        }
    }
} finally {
    Pop-Location
}
