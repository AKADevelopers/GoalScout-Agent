$ErrorActionPreference = "Stop"

$Package = "github:AKADevelopers/GoalScout-Agent"

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "GoalScout Agent install needs npm. Install Node.js first, then run this installer again."
}

$HasPython = (Get-Command python -ErrorAction SilentlyContinue) -or
    (Get-Command py -ErrorAction SilentlyContinue) -or
    (Get-Command python3 -ErrorAction SilentlyContinue)

if (-not $HasPython) {
    throw "GoalScout Agent needs Python 3.11 or newer. Install Python first, then run this installer again."
}

if ($env:GOALSCOUT_INSTALL_DRY_RUN -eq "1") {
    Write-Output "npm install -g $Package"
    exit 0
}

npm install -g $Package
Write-Output "GoalScout Agent installed. Run: goalscout-agent onboard"
