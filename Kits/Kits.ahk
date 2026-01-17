class _kits {
    static CheckPort(port) {
        ; 执行netstat命令
        cmd := ComObject("WScript.Shell").Exec("cmd /c netstat -ano | findstr :" port)
        result := cmd.StdOut.ReadAll()

        ; 如果找到相关行，则端口被占用
        if (InStr(result, ":" port) && InStr(result, "LISTENING"))
            return true
        return false
    }

    abc := '123'
}