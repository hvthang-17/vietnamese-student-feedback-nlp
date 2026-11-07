param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('backend', 'frontend')]
    [string]$Service
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    if ($Service -eq 'backend') {
        $pythonExecutable = Join-Path $projectRoot '.venv-phobert/Scripts/python.exe'
        if (-not (Test-Path -LiteralPath $pythonExecutable)) {
            throw 'PhoBERT environment missing. See docs/guides/phobert-api-guide.md.'
        }
        & $pythonExecutable -m backend.app serve --env-file config/demo.env
    } else {
        $previousPath = $env:PATH
        $previousApiUrl = $env:VITE_API_URL
        try {
            $portableNode = Join-Path $projectRoot 'data/cache/node/node-v24.22.2-win-x64'
            if (Test-Path -LiteralPath (Join-Path $portableNode 'node.exe')) {
                $env:PATH = "$portableNode;$env:PATH"
            }
            if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
                throw 'Node/npm missing. Install Node.js 20+ or restore the project portable cache.'
            }
            $env:VITE_API_URL = 'http://127.0.0.1:8000'
            & npm.cmd --prefix frontend run dev -- --port 5173 --strictPort
        } finally {
            $env:PATH = $previousPath
            $env:VITE_API_URL = $previousApiUrl
        }
    }
    if ($LASTEXITCODE -ne 0) { throw "Demo process exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
