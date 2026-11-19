# Removes the logon task (does not stop a running server; use stop-llama.ps1 for that).
Unregister-ScheduledTask -TaskName 'LlamaServerAutoStart' -Confirm:$false -ErrorAction SilentlyContinue
"Removed LlamaServerAutoStart."
