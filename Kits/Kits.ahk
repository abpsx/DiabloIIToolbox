MapToObject(mapObj) {
    obj := {}
    for key, value in mapObj {
        if (Type(value) = "Map") {
            obj.%key% := MapToObject(value)
        } else {
            obj.%key% := value
        }
    }
    return obj
}

CheckPort(port) {
    ; 执行netstat命令
    cmd := ComObject("WScript.Shell").Exec("cmd /c netstat -ano | findstr :" port)
    result := cmd.StdOut.ReadAll()

    ; 如果找到相关行，则端口被占用
    if (InStr(result, ":" port) && InStr(result, "LISTENING"))
        return true
    return false
}

GetAhkFilesWithoutExt() {
    funcPath := A_ScriptDir "\Func"
    if !DirExist(funcPath)
        return []
    FuncList := []
    Loop Files, funcPath "\*.ahk", "F" {
        SplitPath A_LoopFileName, , , , &nameNoExt
        FuncList.Push(nameNoExt)
    }
    return FuncList
}

FuncListCheck(arr) {
    FuncList := arr
    targetFile := A_ScriptDir "\_AutoInclude.ahk"
    needRewrite := false

    newContent := ""
    for name in FuncList {
        newContent .= "#Include .\Func\" name ".ahk`r`n"
    }

    if FileExist(targetFile) {
        oldTxt := ""
        fRead := FileOpen(targetFile, "r")
        if fRead {
            oldTxt := fRead.Read()
            fRead.Close()
        }

        if (oldTxt != newContent)
            needRewrite := true
    } else {
        needRewrite := true
    }

    if needRewrite {
        fWrite := FileOpen(targetFile, "w")
        if fWrite {
            fWrite.Write(newContent)
            fWrite.Close()
        }
        return true
    } else {
        return false
    }
}


ConstructorFn(FuncList) {
    obj := {}
    for name in FuncList {
        obj.%name% := %name%
    }
    return obj
}


getGuiNav() {
    if FileExist("port.txt")
        port := FileRead("port.txt")
    else
        port := "8080"

    return checkPort(port) ? "http://localhost:" port : "file:///" A_ScriptDir "\Gui\dist\index.html"
}