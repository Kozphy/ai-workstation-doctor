' Starts "llama server" with no window and logs output.
Set sh = CreateObject("WScript.Shell")
dir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.Run "cmd /c llama server > """ & dir & "\llama-server.log"" 2>&1", 0, False
