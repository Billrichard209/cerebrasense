param(
    [int]$Port = 8080,
    [switch]$NoBrowser
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$pythonCandidates = @(
    (Join-Path $scriptDir "..\.venv\Scripts\python.exe"),
    (Join-Path $scriptDir ".venv\Scripts\python.exe")
)

$pythonExe = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $pythonExe) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $pythonExe = $pythonCommand.Source
    }
}

if (-not $pythonExe) {
    Write-Error "Python was not found. Install Python or create .venv first, then run this launcher again."
    exit 1
}

$url = "http://127.0.0.1:$Port/"

Write-Host "Serving CerebraSense frontend demo from $scriptDir"
Write-Host "Open: $url"
Write-Host "Press Ctrl+C to stop the server."

if (-not $NoBrowser) {
    Start-Process $url | Out-Null
}
& $pythonExe -m http.server $Port --bind 127.0.0.1
