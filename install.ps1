# Registers a per-user logon task that starts llama server hidden in the background.
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$vbs = Join-Path $dir 'start-llama-hidden.vbs'
$action = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument ('"' + $vbs + '"') -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'LlamaServerAutoStart' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Starts llama server in the background at logon' -Force | Out-Null
Get-ScheduledTask -TaskName 'LlamaServerAutoStart' | Select-Object TaskName, State | Format-Table -AutoSize | Out-String
