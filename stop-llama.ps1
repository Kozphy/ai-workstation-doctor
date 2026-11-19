# Stops any running llama server.
Get-Process -Name llama -ErrorAction SilentlyContinue | Stop-Process -Force
"Stopped llama server."
