conda deactivate
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
Write-Host "PYTHONPATH has been set to: $env:PYTHONPATH"
