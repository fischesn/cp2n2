param(
    [Parameter()]
    [ValidatePattern('^v[0-9]+\.[0-9]+(?:\.[0-9]+)?$')]
    [string]$Version = 'v5.1.1',

    [Parameter()]
    [string]$OutputRoot = 'release'
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $repositoryRoot

$candidateName = "cp2n2-$Version"
$releaseDirectory = (Resolve-Path -LiteralPath (Join-Path $repositoryRoot (Join-Path $OutputRoot $candidateName))).Path
$sourceArchive = Join-Path $releaseDirectory "$candidateName-source.zip"
$evidenceArchive = Join-Path $releaseDirectory "$candidateName-evidence.zip"
$sourceChecksums = Join-Path $releaseDirectory 'SHA256SUMS.txt'
$evidenceChecksums = Join-Path $releaseDirectory 'EVIDENCE-SHA256SUMS.txt'

foreach ($path in @($sourceArchive, $evidenceArchive, $sourceChecksums, $evidenceChecksums)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required release input is missing: $path"
    }
}

function Confirm-ChecksumLine {
    param(
        [Parameter(Mandatory)] [string]$ChecksumFile,
        [Parameter(Mandatory)] [string]$FileName,
        [Parameter(Mandatory)] [string]$FilePath
    )

    $line = Get-Content -LiteralPath $ChecksumFile | Where-Object { $_ -match "  $([regex]::Escape($FileName))$" }
    if (-not $line -or $line -notmatch '^([0-9a-f]{64})  ') {
        throw "Missing checksum for $FileName"
    }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $FilePath).Hash.ToLowerInvariant()
    if ($actual -ne $Matches[1]) {
        throw "Checksum mismatch for $FileName"
    }
}

Confirm-ChecksumLine -ChecksumFile $sourceChecksums -FileName (Split-Path -Leaf $sourceArchive) -FilePath $sourceArchive
Confirm-ChecksumLine -ChecksumFile $evidenceChecksums -FileName (Split-Path -Leaf $evidenceArchive) -FilePath $evidenceArchive

$bundlePath = Join-Path $releaseDirectory "$candidateName-zenodo.zip"
$bundleChecksumsPath = Join-Path $releaseDirectory 'ZENODO-SHA256SUMS.txt'
if (Test-Path -LiteralPath $bundlePath) {
    throw "Zenodo bundle already exists: $bundlePath"
}

$stagingName = '.zenodo-staging-' + [guid]::NewGuid().ToString('N')
$stagingDirectory = Join-Path $releaseDirectory $stagingName
New-Item -ItemType Directory -Path $stagingDirectory | Out-Null

try {
    Expand-Archive -LiteralPath $sourceArchive -DestinationPath $stagingDirectory
    $bundleRoot = Join-Path $stagingDirectory $candidateName
    if (-not (Test-Path -LiteralPath $bundleRoot)) {
        throw "Unexpected source archive layout: $bundleRoot"
    }

    $evidenceDirectory = Join-Path $bundleRoot 'zenodo-evidence'
    New-Item -ItemType Directory -Path $evidenceDirectory | Out-Null
    Expand-Archive -LiteralPath $evidenceArchive -DestinationPath $evidenceDirectory
    Copy-Item -LiteralPath (Join-Path $releaseDirectory 'release-manifest.json') -Destination $evidenceDirectory
    Copy-Item -LiteralPath (Join-Path $releaseDirectory 'evidence-manifest.json') -Destination $evidenceDirectory
    Copy-Item -LiteralPath $sourceChecksums -Destination $evidenceDirectory
    Copy-Item -LiteralPath $evidenceChecksums -Destination $evidenceDirectory

    $recordDirectory = Join-Path $bundleRoot 'zenodo-record'
    New-Item -ItemType Directory -Path $recordDirectory | Out-Null
    Copy-Item -LiteralPath (Join-Path $repositoryRoot 'CITATION.cff') -Destination $recordDirectory
    Copy-Item -LiteralPath (Join-Path $repositoryRoot '.zenodo.json') -Destination $recordDirectory
    Copy-Item -LiteralPath (Join-Path $repositoryRoot 'docs\zenodo-v5.1.1-record.md') -Destination $recordDirectory

    Push-Location -LiteralPath $stagingDirectory
    try {
        & tar.exe -a -c -f $bundlePath $candidateName
        if ($LASTEXITCODE -ne 0) {
            throw 'Portable Zenodo ZIP creation failed.'
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    $resolvedStaging = (Resolve-Path -LiteralPath $stagingDirectory).Path
    if (-not $resolvedStaging.StartsWith($releaseDirectory + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe staging path: $resolvedStaging"
    }
    Remove-Item -LiteralPath $resolvedStaging -Recurse -Force
}

$bundleHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $bundlePath).Hash.ToLowerInvariant()
Set-Content -LiteralPath $bundleChecksumsPath -Encoding ascii -NoNewline -Value "$bundleHash  $(Split-Path -Leaf $bundlePath)`n"

Write-Output "Zenodo bundle prepared: $bundlePath"
Write-Output "SHA-256: $bundleHash"
