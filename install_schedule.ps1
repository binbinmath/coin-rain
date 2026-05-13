# 注册每日 17:00 运行 金币雨.exe 的任务计划
# 用法：右键 -> 使用 PowerShell 运行

$ErrorActionPreference = 'Stop'
$TaskName = 'CoinRainDaily'
$ExePath = Join-Path $PSScriptRoot 'dist\金币雨.exe'

if (-not (Test-Path $ExePath)) {
    Write-Error "找不到 $ExePath。请先双击 build.bat 完成打包。"
    exit 1
}

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "检测到已存在的任务 $TaskName，先卸载..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action = New-ScheduledTaskAction -Execute $ExePath
$Trigger = New-ScheduledTaskTrigger -Daily -At '17:00'
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable:$false `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId $env:UserName -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description '每天 17:00 在主屏幕播放金币雨彩蛋动画（约 4.5 秒）' | Out-Null

Write-Host ""
Write-Host "=== 已注册任务：$TaskName ==="
Write-Host "触发：每天 17:00"
Write-Host "动作：$ExePath"
Write-Host ""
Write-Host "提示：可以在 Windows '任务计划程序' 里搜索 '$TaskName' 查看/调试。"
Write-Host "     卸载请运行 uninstall_schedule.ps1。"
Read-Host "按 Enter 退出"
