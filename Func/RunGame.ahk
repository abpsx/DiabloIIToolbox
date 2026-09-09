; params := "-direct -locale kor -pdir anhei2mapBUS -skiptobnet  -nofixaspect -nohide -title Bus -w"
; Run 'D2Loader.exe ' params, "G:\game\diablo 2"
; gameDir := "G:\game\diablo 2"

RunGame(gameDir, params) {
    SplitPath(gameDir, &filepath)
    if StrCompare(filepath, "D2Loader.exe", true) = 0 {
        Run 'D2Loader.exe ' params, RegExReplace(gameDir, "i)D2Loader\.exe$", ""), , &pid
    } else {
        Run gameDir, , , &pid
    }

    return pid
}