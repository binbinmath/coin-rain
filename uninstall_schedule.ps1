# 卸载 CoinRainDaily 和 CoinRainTest 任务计划
$Tasks = @('CoinRainDaily', 'CoinRainTest', 'CoinRainTest1Min')
foreach ($t in $Tasks) {
    if (Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $t -Confirm:$false
        Write-Host "已卸载任务：$t"
    } else {
        Write-Host "任务 $t 不存在，无需卸载。"
    }
}
Read-Host "按 Enter 退出"
