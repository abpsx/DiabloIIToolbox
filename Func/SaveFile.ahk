SaveFile(dir, content) {
    fullPath := A_ScriptDir "\" dir

    fWrite := FileOpen(fullPath, "w", "utf-8")
    fWrite.Write(content)
    fWrite.Close()
}