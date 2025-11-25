Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Check if Python is installed
On Error Resume Next
WshShell.Run "python --version", 0, True
If Err.Number <> 0 Then
    MsgBox "Python is not installed!" & vbCrLf & vbCrLf & _
           "Please install Python from:" & vbCrLf & _
           "https://www.python.org/downloads/", _
           vbCritical, "IPFS Backup Tool"
    WScript.Quit
End If
On Error Goto 0

' Check if requests is installed
returnCode = WshShell.Run("python -c ""import requests""", 0, True)
If returnCode <> 0 Then
    ' Install requests silently
    WshShell.Run "pip install requests", 0, True
End If

' Create csv_files folder if it doesn't exist
csvFolder = scriptDir & "\csv_files"
If Not fso.FolderExists(csvFolder) Then
    fso.CreateFolder(csvFolder)
End If

' Run the GUI application (no console window)
WshShell.Run "pythonw """ & scriptDir & "\ipfs_backup_gui.py""", 0, False

' Clean up
Set WshShell = Nothing
Set fso = Nothing
