LoadJson(dir, filename) {
    fullPath := A_ScriptDir "\" dir "\" filename
    return FileRead(fullPath)
}