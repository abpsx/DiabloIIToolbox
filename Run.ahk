#Include './Kits/Kits.ahk'

; 自检
FuncList := GetAhkFilesWithoutExt()
result := FuncListCheck(FuncList)

if result {
    Reload()
} else {
    Run A_ScriptDir "\_Main.ahk"
}