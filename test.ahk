#Requires AutoHotkey v2.0
#SingleInstance Force
; g := Gui("+LastFound +AlwaysOnTop -Caption +ToolWindow")
; g.Show(Format('w{} h{}', A_ScreenWidth, A_ScreenHeight))

; 注册系统鼠标移动钩子
OnMessage(0x0200, OnMouseMove11)

OnMouseMove11(wParam, lParam, *) {
    MouseGetPos(&x, &y, &z)
    ToolTip "X:" x " Y:" y " Z:" z
}

Esc:: ExitApp