# Dot-source this file before starting a native Windows backend or readiness check.
# The dedicated worker must already be provisioned with compose.worker.yml.
$taskRepo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$taskDockerBin = Join-Path $env:LOCALAPPDATA 'Programs/DockerDesktop/resources/bin'
if (Test-Path -LiteralPath $taskDockerBin) { $env:PATH = $taskDockerBin + ';' + $env:PATH }
$env:DOCKER_HOST = 'tcp://127.0.0.1:2376'
$env:DOCKER_TLS_VERIFY = '1'
$env:DOCKER_CERT_PATH = Join-Path $taskRepo '.local/worker-certs'
$env:DOCKER_CONFIG = Join-Path $taskRepo '.local/docker-client'
New-Item -ItemType Directory -Force -Path $env:DOCKER_CONFIG | Out-Null
$env:ENVIRONMENT = 'production'
$env:ALLOW_DEMO_SESSIONS = 'false'
