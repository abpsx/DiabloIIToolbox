; ============================================================
; 启动器（9 开管理）— 由 _Main.ahk 自动注入前端
;
; 项目约定：Func\xxx.ahk 必须定义与文件名同名的函数（Kits.ahk
; ConstructorFn 按文件名注入 obj.%name% := %name%）。
; 本文件通过 Launcher() 门面返回全部操作，前端调用：
;   this.$ahk.fn.Launcher().Start(dir, params, title, script)
;   this.$ahk.fn.Launcher().Stop(pid)
;   this.$ahk.fn.Launcher().Alive(pid)
;   this.$ahk.fn.Launcher().PickLnk(lnkPath)
;   this.$ahk.fn.Launcher().SelectExe(title)
;   this.$ahk.fn.Launcher().SelectDir(title)
;   this.$ahk.fn.Launcher().SelectAhk(title)
; 状态（pid/配置）由前端管理并持久化到 Setting\launcher.json，
; AHK 侧只提供原子操作，全部返回普通对象（host object 兼容）。
; ============================================================

; ---------------- 门面（与文件名同名，供 ConstructorFn 注入） ----------------
Launcher() {
    return {
        Start: LauncherStart,
        Stop: LauncherStop,
        Alive: LauncherAlive,
        PickLnk: LauncherPickLnk,
        Mem: LauncherMem,
        Click: LauncherClick,
        SelectExe: LauncherSelectExe,
        SelectDir: LauncherSelectDir,
        SelectAhk: LauncherSelectAhk
    }
}

; ---------------- 启动 ----------------
; dir     : D2Loader.exe 完整路径（或 .lnk，推荐先经 LauncherPickLnk 转成 exe+args）
; params  : 启动参数（如 -direct -locale kor -pdir ... -w）
; title   : 窗口标题，多开时用于区分实例（覆盖 params 中的 -title）
; script  : 后台 AHK 点击脚本完整路径（可空）
LauncherStart(dir, params, title, script) {
    if !dir
        return { ok: false, error: "未配置启动文件" }
    if !FileExist(dir)
        return { ok: false, error: "文件不存在: " dir }

    ; 工作目录 = dir 所在目录
    SplitPath dir, , &workDir

    ; 组装命令行（带引号防空格路径）
    cmd := '"' dir '"'
    if params
        cmd .= " " params

    ; 多开窗口区分：已有 -title 则覆盖，否则追加（title 含空格时加引号）
    if title {
        if RegExMatch(params, "i)-title\s+\S+")
            cmd := RegExReplace(cmd, "i)(-title\s+)\S+", "$1" '"' title '"')
        else
            cmd .= ' -title "' title '"'
    }

    ; 启动游戏
    try {
        Run cmd, workDir, , &pid
    } catch as e {
        return { ok: false, error: "启动失败: " e.Message }
    }

    ; 挂载后台 AHK 点击脚本（独立解释器进程）
    if script {
        if FileExist(script)
            try Run A_AhkPath ' "' script '"'
            catch as e
                return { ok: true, pid: pid, warn: "脚本启动失败: " e.Message }
        else
            return { ok: true, pid: pid, warn: "脚本不存在: " script }
    }

    return { ok: true, pid: pid }
}

; ---------------- 停止 ----------------
; 优先 WinClose 优雅关闭（D2 需保存角色），超时 3 秒则 ProcessClose
LauncherStop(pid) {
    if !pid or !ProcessExist(pid)
        return { ok: true, note: "进程不存在" }

    WinClose("ahk_pid " pid)
    if WinWaitClose("ahk_pid " pid, , 3)
        return { ok: true, note: "已优雅关闭" }

    ProcessClose(pid)
    return { ok: true, note: "关闭超时，已强制结束" }
}

; ---------------- 状态 ----------------
LauncherAlive(pid) {
    if !pid
        return { alive: false, title: "" }
    if !ProcessExist(pid)
        return { alive: false, title: "" }
    try
        title := WinGetTitle("ahk_pid " pid)
    catch
        title := ""
    return { alive: true, title: title }
}

; ---------------- .lnk 解析 ----------------
; 把快捷方式还原成 目标程序 + 参数 + 工作目录，供前端填充槽位
LauncherPickLnk(lnkPath) {
    if !lnkPath or !FileExist(lnkPath)
        return { ok: false, error: "文件不存在: " lnkPath }
    if !RegExMatch(lnkPath, "i)\.lnk$")
        return { ok: false, error: "不是 .lnk 快捷方式" }

    try {
        sh := ComObject("WScript.Shell")
        lnk := sh.CreateShortcut(lnkPath)
        return {
            ok: true,
            target: lnk.TargetPath,
            args: lnk.Arguments,
            workDir: lnk.WorkingDirectory
        }
    } catch as e {
        return { ok: false, error: "解析失败: " e.Message }
    }
}

; ---------------- 内存读取（多实例，按 PID） ----------------
; pidsCsv : 逗号分隔的 PID 列表（如 "10264,10300"），批量读取一次
; 返回   : { ok, json } —— json 为 mem_read.py 的原始输出字符串，前端 JSON.parse：
;          {"ok":true,"results":{"10264":{"界面标记":10,...},...}}
LauncherMem(pidsCsv) {
    pids := StrSplit(pidsCsv, ",")
    clean := []
    for p in pids {
        p := Trim(p)
        if RegExMatch(p, "^\d+$") and p > 0
            clean.Push(Integer(p))
    }
    if clean.Length = 0
        return { ok: false, json: "{}", error: "无有效 PID（收到: " pidsCsv "）" }

    pyPath := A_ScriptDir "\Py\mem_read.py"
    cfgPath := A_ScriptDir "\Setting\memory\1.13c.json"
    tmpPath := A_ScriptDir "\Py\_mem_out.json"

    args := ' --config "' cfgPath '"'
    for p in clean
        args .= ' --pid ' p
    args .= ' --out "' tmpPath '"'

    try {
        RunWait('"' "python" '" "' pyPath '"' args, A_ScriptDir "\Py", "Hide")
    } catch as e {
        return { ok: false, json: "{}", error: "内存读取失败: " e.Message }
    }

    if !FileExist(tmpPath)
        return { ok: false, json: "{}", error: "内存读取无输出" }
    raw := FileRead(tmpPath)
    return { ok: true, json: raw }
}

; ---------------- 控件点击（后台 PostMessage，不抢焦点不移动鼠标） ----------------
; x, y : D2 客户区坐标（即控件链 pos），lParam = (y<<16)|x
LauncherClick(pid, x, y) {
    if !pid or !ProcessExist(pid)
        return { ok: false, error: "进程不存在" }
    try
        hwnd := WinGetID("ahk_pid " pid)
    catch
        return { ok: false, error: "找不到窗口 (PID " pid ")" }
    lParam := (Integer(y) & 0xFFFF) | ((Integer(x) & 0xFFFF) << 16)
    PostMessage(0x0201, 0x0001, lParam, , "ahk_pid " pid)  ; WM_LBUTTONDOWN, MK_LBUTTON
    PostMessage(0x0202, 0, lParam, , "ahk_pid " pid)        ; WM_LBUTTONUP
    return { ok: true, hwnd: hwnd, x: Integer(x), y: Integer(y) }
}

; ---------------- 文件/目录选择（复用现有功能） ----------------
LauncherSelectExe(title := "选择启动文件（exe / lnk）") {
    return FileSelect(1, , title, "可执行文件 (*.exe;*.lnk)|*.exe;*.lnk")
}

LauncherSelectDir(title := "选择游戏目录") {
    return DirSelect(, , title)
}

LauncherSelectAhk(title := "选择后台 AHK 脚本") {
    return FileSelect(1, , title, "AutoHotkey 脚本 (*.ahk)|*.ahk")
}
