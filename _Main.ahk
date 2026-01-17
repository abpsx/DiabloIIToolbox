#Include <WebView2\WebView2>
#Include './_AutoInclude.ahk'
#Include './Kits/Kits.ahk'

injectObj := { fn: ConstructorFn(GetAhkFilesWithoutExt()) }

; || 创建窗口
main := Gui()
main.Opt("-Resize")

main.Show(Format('w{} h{}', A_ScreenWidth * 0.6, A_ScreenHeight * 0.6))
wvc := WebView2.CreateControllerAsync(main.Hwnd).await2()
wv := wvc.CoreWebView2

wv.Navigate(getGuiNav())

; || 注入函数到前端
wv.AddHostObjectToScript('ahk', injectObj)