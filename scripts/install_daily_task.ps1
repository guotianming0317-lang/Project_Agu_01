param(
    [switch]$RunNow,
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$taskName = "ProjectAgu01-DailyNewsWorkflow"
$workflowScript = Join-Path $projectRoot "scripts\run_start_daily_news_workflow.ps1"

if (-not (Test-Path $workflowScript)) {
    throw "Workflow script was not found: $workflowScript"
}

if ($Remove) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Removed scheduled task: $taskName"
    exit 0
}

$powershell = Join-Path $PSHOME "powershell.exe"
$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$workflowScript`""
$action = New-ScheduledTaskAction -Execute $powershell -Argument $arguments -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At "09:25"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Project Agu 01 daily market, news, and announcement workflow" `
    -Force | Out-Null

Write-Host "Installed scheduled task: $taskName"
Write-Host "Schedule: daily at 09:25"
Write-Host "Working directory: $projectRoot"
Write-Host "Status command: Get-ScheduledTask -TaskName '$taskName'"

if ($RunNow) {
    Start-ScheduledTask -TaskName $taskName
    Write-Host "Started one immediate run."
}
