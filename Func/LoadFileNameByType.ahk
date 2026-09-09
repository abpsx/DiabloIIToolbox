LoadFileNameByType(dir, type) {

    fullPath := A_ScriptDir "\" dir
    result := ""

    loop Files, fullPath "\*." type, "F"
    {
        SplitPath A_LoopFileName, , , &ext, &nameNoExt
        if (result = "")
            result := nameNoExt
        else
            result .= "," nameNoExt
    }
    return result
}