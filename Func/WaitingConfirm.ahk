WaitingConfirm(text := "确认游戏正常启动后点(是)", title := "确认操作") {
    result := MsgBox(text, title, "YesNo")
    return result = "Yes" ? 1 : 0
}