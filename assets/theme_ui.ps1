param()

$ErrorActionPreference = 'SilentlyContinue'
$ConfirmPreference = 'None'
$ProgressPreference = 'SilentlyContinue'
$VER = '1.6.0'
$BUILD_DATE = '2026-11-19'
$REPO_URL = 'https://github.com/sammaosamsam/GlassDesk'
$PACK = $PSScriptRoot
$cfg  = Get-Content (Join-Path $PACK 'install_config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$ADMIN_PS = Join-Path $env:TEMP 'GlassDesk_admin.ps1'
$FLAG     = Join-Path $env:TEMP 'GlassDesk_admin.flag'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$COL_BG      = [System.Drawing.Color]::FromArgb(20, 22, 27)
$COL_PANEL   = [System.Drawing.Color]::FromArgb(28, 31, 38)
$COL_TEXT    = [System.Drawing.Color]::FromArgb(232, 234, 239)
$COL_DIM     = [System.Drawing.Color]::FromArgb(140, 149, 164)
$COL_BLUE    = [System.Drawing.Color]::FromArgb(76, 141, 255)
$COL_RED     = [System.Drawing.Color]::FromArgb(229, 100, 110)
$COL_GREEN   = [System.Drawing.Color]::FromArgb(55, 199, 160)
$COL_GRAY    = [System.Drawing.Color]::FromArgb(45, 51, 62)

function Icon-Path([string]$f) {
    return ((Join-Path (Join-Path $PACK 'icons') $f) + ',0')
}

# ---- 浅色主题映射：exe -> l_<slug>.ico（大小写不敏感，避免 chrome.exe / 360se.exe 等漏匹配）----
$script:useLight = $false
$script:lightIcons = @{}
$script:darkIcons  = @{}
foreach ($p in $cfg.icons.PSObject.Properties) {
    $base = [System.IO.Path]::GetFileNameWithoutExtension($p.Value)
    $ln   = 'l_' + $base + '.ico'
    $k    = $p.Name.ToLower()
    $script:darkIcons[$k] = $p.Value
    if (Test-Path (Join-Path (Join-Path $PACK 'icons') $ln)) { $script:lightIcons[$k] = $ln }
}
function Ico-Name([string]$exe) {
    $k = $exe.ToLower()
    if ($script:useLight -and $script:lightIcons.ContainsKey($k)) { return $script:lightIcons[$k] }
    if ($script:darkIcons.ContainsKey($k)) { return $script:darkIcons[$k] }
    return $null
}

# 少数快捷方式没有 TargetPath（指向应用/商店项），只能按快捷方式显示名匹配
$script:nameIcons = @{
    '微信' = 'wechat.ico'
    '控制面板' = 'sys_cpl.ico'
}
function Ico-NameByName([string]$base) {
    $v = $script:nameIcons[$base]
    if (-not $v) { return $null }
    if ($script:useLight) {
        $l = 'l_' + $v
        if (Test-Path (Join-Path (Join-Path $PACK 'icons') $l)) { return $l }
    }
    return $v
}

# region 核心动作
function Apply-ShortcutIcons {
    $ws = New-Object -ComObject WScript.Shell
    $icd = Join-Path $PACK 'icons'
    $n = 0
    foreach ($dir in @((Join-Path $env:USERPROFILE 'Desktop'), 'C:\Users\Public\Desktop')) {
        if (-not (Test-Path -LiteralPath $dir)) { continue }
        Get-ChildItem -LiteralPath $dir -Filter *.lnk -Force | ForEach-Object {
            try {
                $sc  = $ws.CreateShortcut($_.FullName)
                $exe = [System.IO.Path]::GetFileName($sc.TargetPath)
                $ico = if ($exe -ne '') { Ico-Name $exe } else { Ico-NameByName $_.BaseName }
                if ($ico -and (Test-Path -LiteralPath (Join-Path $icd $ico))) {
                    $sc.IconLocation = (Icon-Path $ico)
                    $sc.Save()
                    $n++
                    return
                }
                # 兜底：按当前图标路径切换（l_xxx.ico <-> xxx.ico），保证任何 lnk 都能跟随主题
                $cur = ($sc.IconLocation -split ',')[0]
                if ($cur -and (Test-Path -LiteralPath $cur) -and ($cur.StartsWith($icd))) {
                    $leaf = [System.IO.Path]::GetFileName($cur)
                    if ($script:useLight) {
                        if (-not $leaf.StartsWith('l_')) { $leaf = 'l_' + $leaf }
                    } else {
                        if ($leaf.StartsWith('l_')) { $leaf = $leaf.Substring(2) }
                    }
                    $target = Join-Path $icd $leaf
                    if (Test-Path -LiteralPath $target) {
                        $sc.IconLocation = ($target + ',0')
                        $sc.Save()
                        $n++
                    }
                }
            } catch { }
        }
    }
    return $n
}

function Apply-SystemIcons {
    $m = @{
        '{20D04FE0-3AEA-1069-A2D8-08002B30309D}' = 'sys_pc.ico'
        '{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}' = 'sys_network.ico'
        '{645FF040-5081-101B-9F08-00AA002F954E}' = 'sys_bin.ico'
        '{59031A47-3F72-44A7-89C5-5595FE6B30EE}' = 'sys_user.ico'
        '{21EC2020-3AEA-1069-A2DD-08002B30309D}' = 'sys_cpl.ico'
    }
    if ($script:useLight -and $cfg.system_icons_light) {
        foreach ($g in $cfg.system_icons_light.PSObject.Properties.Name) { $m[$g] = $cfg.system_icons_light.$g }
    }
    foreach ($g in $m.Keys) {
        foreach ($base in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\CLSID',
                           'HKCU:\Software\Classes\CLSID')) {
            $k = Join-Path (Join-Path $base $g) 'DefaultIcon'
            if (-not (Test-Path $k)) { New-Item -Path $k -Force | Out-Null }
            $v = Icon-Path $m[$g]
            Set-ItemProperty -Path $k -Name '(default)' -Value $v
            if ($g -eq '{645FF040-5081-101B-9F08-00AA002F954E}') {
                Set-ItemProperty -Path $k -Name 'Empty' -Value $v
                Set-ItemProperty -Path $k -Name 'Full'  -Value $v
            }
        }
    }
}

function Write-AdminScript([string]$mode) {
    $fi = $cfg.folder_icon
    if ($script:useLight -and $cfg.folder_icon_light) {
        if (Test-Path (Join-Path (Join-Path $PACK 'icons') $cfg.folder_icon_light)) { $fi = $cfg.folder_icon_light }
    }
    $ic = (Join-Path (Join-Path $PACK 'icons') $fi)
    $bl = (Join-Path (Join-Path $PACK 'icons') $cfg.blank_icon)
    $lines = @(
        '$ErrorActionPreference = "SilentlyContinue"',
        '$ConfirmPreference = "None"',
        '$ProgressPreference = "SilentlyContinue"',
        ('$ico  = "' + $ic + ',0"'),
        ('$blank = "' + $bl + ',0"'),
        ('$mode = "' + $mode + '"'),
        '$styleOnly = $mode.StartsWith("icons-")',
        'if ($styleOnly) { $mode = $mode.Substring(6) }',
        ('$icd = "' + (Join-Path $PACK 'icons') + '"'),
        ('$flag = "' + $FLAG + '"'),
        ('$si = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons"'),
        'if (-not (Test-Path $si)) { New-Item -Path $si -Force | Out-Null }',
        'if (-not $styleOnly) {',
        'foreach ($p in @("HKLM:\SOFTWARE\Classes\Directory\DefaultIcon","HKLM:\SOFTWARE\Classes\Folder\DefaultIcon")) {',
        '  if (Test-Path $p) { foreach ($n in (Get-Item $p).GetValueNames()) { Remove-ItemProperty -Path $p -Name $n -Force } }',
        '}',
        '}',
        'if ($styleOnly) {',
        '  # 仅切换风格：文件夹图标要跟着换，小箭头保持原状',
        '  Set-ItemProperty -Path $si -Name "3" -Value $ico',
        '  Set-ItemProperty -Path $si -Name "4" -Value $ico',
        '} elseif ($mode -eq "restore") {',
        '  foreach ($n in @("3","4","29")) { Remove-ItemProperty -Path $si -Name $n -Force }',
        '} else {',
        '  Set-ItemProperty -Path $si -Name "3" -Value $ico',
        '  Set-ItemProperty -Path $si -Name "4" -Value $ico',
        '  Set-ItemProperty -Path $si -Name "29" -Value $blank',
        '}',
        '# 快捷方式图标（含公共桌面）：先按 exe 名查表，查不到再按现有图标路径 l_ 前缀互换',
        '$dark  = ''' + ($script:darkIcons  | ConvertTo-Json -Compress) + ''' | ConvertFrom-Json',
        '$light = ''' + ($script:lightIcons | ConvertTo-Json -Compress) + ''' | ConvertFrom-Json',
        '$names = ''' + ($script:nameIcons  | ConvertTo-Json -Compress) + ''' | ConvertFrom-Json',
        '$ws = New-Object -ComObject WScript.Shell',
        '$dirs = @((Join-Path $env:USERPROFILE "Desktop"), "C:\Users\Public\Desktop", (Join-Path $env:USERPROFILE "OneDrive\Desktop"))',
        'foreach ($d in $dirs) {',
        '  if (-not (Test-Path -LiteralPath $d)) { continue }',
        '  Get-ChildItem -LiteralPath $d -Filter *.lnk -Force | ForEach-Object {',
        '    try {',
        '      $sc = $ws.CreateShortcut($_.FullName)',
        '      $exe = [System.IO.Path]::GetFileName($sc.TargetPath).ToLower()',
        '      $loc = $sc.IconLocation',
        '      if ($loc -and $loc.Contains(",")) { $p = $loc.Split(",")[0] } else { $p = $loc }',
        '      $nm = [System.IO.Path]::GetFileName($p)',
        '      if ($mode -eq "restore") {',
        '        if ($p -and $p.StartsWith($icd)) {',
        '          $tp = $sc.TargetPath',
        '          if ($tp -and (Test-Path -LiteralPath $tp)) { $sc.IconLocation = $tp + ",0" } else { return }',
        '          $sc.Save()',
        '        }',
        '        return',
        '      }',
        '      $want = $null',
        '      if ($exe -ne "") {',
        '        if ($mode -eq "light") { $want = $light.$exe } else { $want = $dark.$exe }',
        '      }',
        '      if (-not $want -and $exe -eq "") { $want = $names.($_.BaseName) }',
        '      if ($want -and $mode -eq "light" -and -not $want.StartsWith("l_")) { $want = "l_" + $want }',
        '      if ($want -and $mode -ne "light" -and $want.StartsWith("l_")) { $want = $want.Substring(2) }',
        '      if (-not $want -and $nm -ne "") {',
        '        if ($mode -eq "light") { if ($nm.StartsWith("l_")) { $want = $nm } else { $want = "l_" + $nm } }',
        '        else { if ($nm.StartsWith("l_")) { $want = $nm.Substring(2) } else { $want = $nm } }',
        '      }',
        '      if ($want) {',
        '        $full = Join-Path $icd $want',
        '        if (Test-Path -LiteralPath $full) { $sc.IconLocation = $full + ",0"; $sc.Save() }',
        '      }',
        '    } catch { }',
        '  }',
        '}',
        'Set-Content -LiteralPath $flag -Value "ok" -Encoding ASCII'
    )
    Set-Content -LiteralPath $ADMIN_PS -Value ($lines -join "`r`n") -Encoding UTF8
}

function Run-Admin([string]$mode) {
    Write-AdminScript $mode
    if (Test-Path $FLAG) { Remove-Item $FLAG -Force }
    $p = Start-Process -FilePath 'powershell.exe' -Verb RunAs `
         -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',("`"" + $ADMIN_PS + "`"") -PassThru -WindowStyle Hidden
    if ($null -eq $p) { return $false }
    $p.WaitForExit(120000) | Out-Null
    Start-Sleep -Milliseconds 500
    return (Test-Path $FLAG)
}

# 桌面图标尺寸：重启资源管理器后 Windows 有时会把 IconSize 重置成大图标。
# 这里在重启前记下当前尺寸，重启后原样写回，做到“原来多大就一直多大”。
$script:bagKey = 'HKCU:\Software\Microsoft\Windows\Shell\Bags\1\Desktop'
function Get-DesktopIconSize {
    if (Test-Path $script:bagKey) {
        $v = (Get-ItemProperty $script:bagKey -Name IconSize -ErrorAction SilentlyContinue).IconSize
        if ($null -ne $v) { return [int]$v }
    }
    return $null
}
function Set-DesktopIconSize([int]$size) {
    if ($size -le 0) { return }
    if (-not (Test-Path $script:bagKey)) { New-Item -Path $script:bagKey -Force | Out-Null }
    Set-ItemProperty -Path $script:bagKey -Name 'IconSize' -Value $size -Type DWord
}

function Restart-Explorer {
    $ConfirmPreference = 'None'
    $iconSize = Get-DesktopIconSize
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    $cache = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Explorer'
    if (Test-Path -LiteralPath $cache) {
        # 用 -Recurse -Force -Confirm:$false 静默删除，避免出现“确认 是/否”的交互提示
        Get-ChildItem -LiteralPath $cache -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like 'iconcache*.db' -or $_.Name -like 'thumbcache*.db' -or $_.Name -like '*CacheToDelete' } |
            ForEach-Object {
                try { Remove-Item -LiteralPath $_.FullName -Recurse -Force -Confirm:$false -ErrorAction SilentlyContinue } catch { }
            }
    }
    & "$env:SystemRoot\System32\ie4uinit.exe" -ClearIconCache 2>$null
    Start-Sleep -Milliseconds 800
    Start-Process explorer.exe
    if ($iconSize) {
        Start-Sleep -Seconds 4
        Set-DesktopIconSize $iconSize
    }
}

# 让桌面上的文件夹始终用玻璃文件夹图标，而不是“内容缩略图”
# 做法：给每个桌面文件夹写 desktop.ini（IconResource 指向当前风格图标）+ 文件夹加 System 属性
function Update-FolderIni {
    $fi = $cfg.folder_icon
    if ($script:useLight -and $cfg.folder_icon_light) { $fi = $cfg.folder_icon_light }
    $ico = Join-Path (Join-Path $PACK 'icons') $fi
    if (-not (Test-Path $ico)) { return 0 }
    $n = 0
    $desk = Join-Path $env:USERPROFILE 'Desktop'
    if (-not (Test-Path $desk)) { return 0 }
    Get-ChildItem -LiteralPath $desk -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.PSIsContainer } |
        ForEach-Object {
            $ini = Join-Path $_.FullName 'desktop.ini'
            $body = @(
                '[.ShellClass_Info]',
                ('IconResource=' + $ico + ',0'),
                '[ViewState]',
                'Mode=',
                'Vid=',
                'FolderType=Generic'
            ) -join "`r`n"
            try {
                [System.IO.File]::WriteAllText($ini, $body, [System.Text.Encoding]::Unicode)
                $item = Get-Item -LiteralPath $ini -Force
                $item.Attributes = [System.IO.FileAttributes]'Hidden, System'
                $dir = Get-Item -LiteralPath $_.FullName
                if (-not ($dir.Attributes -band [System.IO.FileAttributes]::System)) {
                    $dir.Attributes = $dir.Attributes -bor [System.IO.FileAttributes]::System
                }
                # 桌面上自定义图标要求文件夹带只读/系统属性，否则 Explorer 不读 desktop.ini
                if (-not ($dir.Attributes -band [System.IO.FileAttributes]::ReadOnly)) {
                    $dir.Attributes = $dir.Attributes -bor [System.IO.FileAttributes]::ReadOnly
                }
                $n++
            } catch { }
        }
    return $n
}

# 控制面板的命名空间图标在 HKLM\SOFTWARE\Classes\CLSID 里，属于 TrustedInstaller，管理员也改不了。
# 于是隐藏系统那个“控制面板”，在桌面放一个指向 control.exe 的同名快捷方式，用我们的玻璃图标。
function Set-ControlPanelItem {
    # 桌面上会出现两种“控制面板”命名空间项（Control Panel 主页 / 所有控制面板项），都隐藏掉
    $gList = @('{21EC2020-3AEA-1069-A2DD-08002B30309D}',
               '{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}',
               '{26EE0668-A00A-44D7-9371-BEB064C98683}')
    $bases = @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel',
               'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\ClassicStartMenu')
    $state = Join-Path $env:TEMP 'GlassDesk_hideicons.json'
    if (-not (Test-Path $state)) {
        $snap = @{}
        foreach ($b in $bases) { foreach ($g in $gList) { $v = (Get-ItemProperty $b -Name $g -ErrorAction SilentlyContinue).$g; if ($null -ne $v) { $snap[($b + '|' + $g)] = $v } } }
        ($snap | ConvertTo-Json -Compress) | Set-Content -LiteralPath $state -Encoding UTF8
    }
    foreach ($b in $bases) {
        if (-not (Test-Path $b)) { New-Item -Path $b -Force | Out-Null }
        foreach ($g in $gList) { Set-ItemProperty -Path $b -Name $g -Value 1 -Type DWord }
    }
    $lnk = Join-Path (Join-Path $env:USERPROFILE 'Desktop') '控制面板.lnk'
    $ico = Join-Path (Join-Path $PACK 'icons') $(if ($script:useLight) { 'l_sys_cpl.ico' } else { 'sys_cpl.ico' })
    if (-not (Test-Path $ico)) { return }
    $ws = New-Object -ComObject WScript.Shell
    $sc = $ws.CreateShortcut($lnk)
    $sc.TargetPath = Join-Path $env:SystemRoot 'System32\control.exe'
    $sc.IconLocation = $ico + ',0'
    $sc.Description = '控制面板'
    $sc.Save()
}

# 文件夹里放了文件后，Explorer 会拿内容缩略图顶掉自定义文件夹图标。
# 这里按“始终显示图标、从不显示缩略图”处理，保证整桌面风格统一；原设置记在状态文件里，还原时写回。
function Set-IconsOnly {
    $adv = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'
    $state = Join-Path $env:TEMP 'GlassDesk_iconsonly.txt'
    if (-not (Test-Path $state)) {
        $old = (Get-ItemProperty $adv -Name IconsOnly -ErrorAction SilentlyContinue).IconsOnly
        if ($null -eq $old) { $old = 0 }
        Set-Content -LiteralPath $state -Value $old -Encoding UTF8
    }
    Set-ItemProperty -Path $adv -Name 'IconsOnly' -Value 1
}
function Restore-IconsOnly {
    $adv = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced'
    $state = Join-Path $env:TEMP 'GlassDesk_iconsonly.txt'
    if (Test-Path $state) {
        $old = [int](Get-Content -LiteralPath $state -Raw).Trim()
        Set-ItemProperty -Path $adv -Name 'IconsOnly' -Value $old
        Remove-Item -LiteralPath $state -Force -ErrorAction SilentlyContinue
    }
}

function Set-WallpaperFile([string]$name) {
    $p = Join-Path (Join-Path $PACK 'wallpapers') $name
    if (-not (Test-Path $p)) { return $false }
    Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name 'WallpaperStyle' -Value '10'
    Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name 'TileWallpaper' -Value '0'
    Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name 'Wallpaper' -Value $p
    $sig = '[DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);'
    if (-not ('Win32Wall' -as [type])) {
        Add-Type -MemberDefinition $sig -Name 'Win32Wall' -Namespace 'DG'
    }
    [DG.Win32Wall]::SystemParametersInfo(20, 0, $p, 3) | Out-Null
    return $true
}
# endregion

# region 界面
$form = New-Object System.Windows.Forms.Form
$form.Text = 'GlassDesk · 双色玻璃桌面主题'
$form.ClientSize = New-Object System.Drawing.Size(700, 632)
$form.StartPosition = 'CenterScreen'
$form.BackColor = $COL_BG
$form.ForeColor = $COL_TEXT
$form.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 9)
$form.FormBorderStyle = 'FixedSingle'
$form.MaximizeBox = $false

$title = New-Object System.Windows.Forms.Label
$title.Text = 'GlassDesk'
$title.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 19, [System.Drawing.FontStyle]::Bold)
$title.ForeColor = $COL_BLUE
$title.Location = New-Object System.Drawing.Point(24, 16)
$title.Size = New-Object System.Drawing.Size(160, 38)
$form.Controls.Add($title)

$sub = New-Object System.Windows.Forms.Label
$sub.Text = ('v' + $VER + ' · 深色 / 浅色双主题 · 一键安装 / 切换 / 还原 · 开源 MIT')
$sub.ForeColor = $COL_DIM
$sub.Location = New-Object System.Drawing.Point(176, 28)
$sub.Size = New-Object System.Drawing.Size(370, 24)
$form.Controls.Add($sub)

$divider = New-Object System.Windows.Forms.Panel
$divider.Location = New-Object System.Drawing.Point(24, 62)
$divider.Size = New-Object System.Drawing.Size(652, 1)
$divider.BackColor = [System.Drawing.Color]::FromArgb(42, 47, 57)
$form.Controls.Add($divider)

$info = New-Object System.Windows.Forms.Label
$info.Text = ('图标库 ' + $cfg.icons.PSObject.Properties.Name.Count + ' 个程序 · 深色 ' + $cfg.wallpapers.Count + ' 张 / 浅色壁纸另附')
$info.ForeColor = $COL_DIM
$info.Location = New-Object System.Drawing.Point(24, 74)
$info.Size = New-Object System.Drawing.Size(300, 20)
$form.Controls.Add($info)

function New-Btn([string]$text, [int]$x, [int]$y, [int]$w, [int]$h, $color, [scriptblock]$onClick) {
    $b = New-Object System.Windows.Forms.Button
    $b.Text = $text
    $b.Location = New-Object System.Drawing.Point($x, $y)
    $b.Size = New-Object System.Drawing.Size($w, $h)
    $b.FlatStyle = 'Flat'
    $b.FlatAppearance.BorderSize = 0
    $b.BackColor = $color
    $b.ForeColor = [System.Drawing.Color]::White
    $b.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 10, [System.Drawing.FontStyle]::Bold)
    $b.Cursor = [System.Windows.Forms.Cursors]::Hand
    $b.Add_Click($onClick)
    $form.Controls.Add($b)
    return $b
}

$script:logBox = New-Object System.Windows.Forms.TextBox
$script:logBox.Multiline = $true
$script:logBox.ReadOnly = $true
$script:logBox.ScrollBars = 'Vertical'
$script:logBox.BackColor = [System.Drawing.Color]::FromArgb(16, 18, 23)
$script:logBox.ForeColor = [System.Drawing.Color]::FromArgb(198, 206, 218)
$script:logBox.BorderStyle = 'FixedSingle'
$script:logBox.Font = New-Object System.Drawing.Font('Consolas', 9)
$script:logBox.Location = New-Object System.Drawing.Point(24, 424)
$script:logBox.Size = New-Object System.Drawing.Size(652, 184)
$form.Controls.Add($script:logBox)

function Log([string]$m) {
    $script:logBox.AppendText($m + "`r`n")
    [System.Windows.Forms.Application]::DoEvents()
}

function Run-Job([scriptblock]$work, [string]$doneText) {
    $form.Cursor = [System.Windows.Forms.Cursors]::WaitCursor
    Log '────────────────────────'
    & $work
    Log ('[完成] ' + $doneText)
    $form.Cursor = [System.Windows.Forms.Cursors]::Default
}

# ---- 左栏：三个主按钮，等宽等高、垂直对齐 ----
$btnInstall = New-Btn '一键安装' 24 100 210 50 $COL_BLUE {
    Run-Job {
        $n = Apply-ShortcutIcons
        Log ('快捷方式图标已更新：' + $n + ' 个')
        Apply-SystemIcons
        Log '系统图标已更新（此电脑 / 网络 / 回收站 / 用户文件夹 / 控制面板）'
        Set-ControlPanelItem
        Set-IconsOnly
        Log ('桌面文件夹图标已统一：' + (Update-FolderIni) + ' 个文件夹')
        if (Run-Admin $(if ($script:useLight) { 'light' } else { 'dark' })) {
            Log '文件夹蒙版 + 隐藏小箭头 已生效'
        } else {
            Log '！未获得管理员权限，跳过文件夹蒙版'
        }
        $w = $combo.SelectedItem
        if (-not $w) {
            if ($script:useLight) { $w = $cfg.default_wallpaper_light } else { $w = $cfg.default_wallpaper }
        }
        if ($script:useLight) { Log '当前为浅色风格：使用浅底图标 + 浅色文件夹图标' }
        if (Set-WallpaperFile $w) { Log ('壁纸已设置：' + $w) }
        Restart-Explorer
        Log '资源管理器已重启，图标缓存已重建'
    } '安装完成'
}

$btnRestore = New-Btn '一键还原' 24 162 210 50 $COL_RED {
    $r = [System.Windows.Forms.MessageBox]::Show('将把快捷方式图标、系统图标、文件夹蒙版、小箭头全部恢复为系统默认。' + "`r`n" + '确定继续？', '确认还原', 'YesNo', 'Question')
    if ($r -ne 'Yes') { return }
    Run-Job {
        # 还原快捷方式图标：优先写回目标程序自身图标（最可靠），并提权覆盖公共桌面
        $rst = Join-Path $env:TEMP 'GlassDesk_restore.ps1'
        $code = @(
            '$ErrorActionPreference = "SilentlyContinue"',
            '$ConfirmPreference = "None"',
            '$sh = New-Object -ComObject WScript.Shell',
            '$fix = 0',
            'foreach ($d in @((Join-Path $env:USERPROFILE "Desktop"), "C:\Users\Public\Desktop", (Join-Path $env:USERPROFILE "OneDrive\Desktop"))) {',
            '  if (-not (Test-Path -LiteralPath $d)) { continue }',
            '  Get-ChildItem -LiteralPath $d -Filter *.lnk -Force | ForEach-Object {',
            '    try {',
            '      $sc = $sh.CreateShortcut($_.FullName)',
            '      $tp = $sc.TargetPath',
            '      if ($tp -and (Test-Path -LiteralPath $tp)) { $sc.IconLocation = $tp + ",0" } else { return }',
            '      $sc.Save(); $fix++',
            '    } catch { }',
            '  }',
            '}',
            'Set-Content -LiteralPath "' + (Join-Path $env:TEMP 'GlassDesk_restore.flag') + '" -Value $fix -Encoding ASCII'
        )
        Set-Content -LiteralPath $rst -Value ($code -join "`r`n") -Encoding ASCII
        $flagR = Join-Path $env:TEMP 'GlassDesk_restore.flag'
        if (Test-Path $flagR) { Remove-Item $flagR -Force }
        Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',("`"" + $rst + "`"") -Wait
        if (Test-Path $flagR) {
            Log ('快捷方式图标已恢复为程序默认：' + (Get-Content $flagR -Raw).Trim() + ' 个')
        } else {
            Log '快捷方式图标已恢复（用户桌面）；公共桌面需要管理员权限'
        }
        $m = @('{20D04FE0-3AEA-1069-A2D8-08002B30309D}','{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}',
               '{645FF040-5081-101B-9F08-00AA002F954E}','{59031A47-3F72-44A7-89C5-5595FE6B30EE}',
               '{21EC2020-3AEA-1069-A2DD-08002B30309D}')
        foreach ($g in $m) {
            foreach ($base in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\CLSID',
                               'HKCU:\Software\Classes\CLSID')) {
                $k = Join-Path (Join-Path $base $g) 'DefaultIcon'
                if (Test-Path $k) { Remove-Item -Path $k -Recurse -Force }
            }
        }
        Log '系统图标已恢复'
        # 还原：删掉我们放的控制面板快捷方式，恢复系统自带的命名空间项
        $cplLnk = Join-Path (Join-Path $env:USERPROFILE 'Desktop') '控制面板.lnk'
        $icons_dir = Join-Path $PACK 'icons'
        if (Test-Path -LiteralPath $cplLnk) {
            $ws2 = New-Object -ComObject WScript.Shell
            $c = $ws2.CreateShortcut($cplLnk)
            if ($c.IconLocation -like ($icons_dir + '*')) { Remove-Item -LiteralPath $cplLnk -Force }
        }
        $gCpl = '{21EC2020-3AEA-1069-A2DD-08002B30309D}'
        $gCpl2 = @('{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}', '{26EE0668-A00A-44D7-9371-BEB064C98683}')
        $stateH = Join-Path $env:TEMP 'GlassDesk_hideicons.json'
        foreach ($base in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel',
                            'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\ClassicStartMenu')) {
            if (-not (Test-Path $base)) { continue }
            Remove-ItemProperty -Path $base -Name $gCpl -Force -ErrorAction SilentlyContinue
            foreach ($gg in $gCpl2) { Remove-ItemProperty -Path $base -Name $gg -Force -ErrorAction SilentlyContinue }
        }
        if (Test-Path $stateH) {
            $snap = Get-Content -LiteralPath $stateH -Raw | ConvertFrom-Json
            foreach ($p in $snap.PSObject.Properties) {
                $parts = $p.Name -split '|'
                if ($parts.Count -eq 2 -and (Test-Path $parts[0])) {
                    Set-ItemProperty -Path $parts[0] -Name $parts[1] -Value ([int]$p.Value) -Type DWord -ErrorAction SilentlyContinue
                }
            }
            Remove-Item -LiteralPath $stateH -Force -ErrorAction SilentlyContinue
        }
        # 还原：去掉我们写进桌面文件夹的 desktop.ini 自定义图标，并恢复缩略图设置
        Get-ChildItem -LiteralPath (Join-Path $env:USERPROFILE 'Desktop') -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.PSIsContainer } | ForEach-Object {
                $ini = Join-Path $_.FullName 'desktop.ini'
                if (Test-Path -LiteralPath $ini) {
                    $txt = Get-Content -LiteralPath $ini -Raw -ErrorAction SilentlyContinue
                    if ($txt -and $txt.Contains($icons_dir)) {
                        $dir0 = Get-Item -LiteralPath $_.FullName
                        if ($dir0.Attributes -band [System.IO.FileAttributes]::ReadOnly) {
                            $dir0.Attributes = $dir0.Attributes -bxor [System.IO.FileAttributes]::ReadOnly
                        }
                        Remove-Item -LiteralPath $ini -Force -ErrorAction SilentlyContinue
                    }
                }
            }
        Restore-IconsOnly
        Log '控制面板与文件夹图标已恢复系统默认'
        if (Run-Admin 'restore') { Log '文件夹蒙版与小箭头已恢复默认' }
        Restart-Explorer
    } '还原完成'
}

$btnArrow = New-Btn '只去掉小箭头' 24 224 210 50 $COL_GREEN {
    Run-Job {
        if (Run-Admin 'apply') {
            Log '快捷方式小箭头已隐藏'
            Restart-Explorer
        } else {
            Log '！未获得管理员权限'
        }
    } '去箭头完成'
}

$btnCache = New-Btn '重建图标缓存' 24 286 210 50 $COL_GRAY {
    Run-Job { Restart-Explorer; Log '图标与缩略图缓存已清空并重建' } '缓存重建完成'
}

# ---- 右栏：壁纸预览 + 选择 ----
$wpTitle = New-Object System.Windows.Forms.Label
$wpTitle.Text = '壁纸预览'
$wpTitle.ForeColor = $COL_TEXT
$wpTitle.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 9, [System.Drawing.FontStyle]::Bold)
$wpTitle.Location = New-Object System.Drawing.Point(266, 100)
$wpTitle.Size = New-Object System.Drawing.Size(120, 22)
$form.Controls.Add($wpTitle)

$script:preview = New-Object System.Windows.Forms.PictureBox
$script:preview.Location = New-Object System.Drawing.Point(266, 124)
$script:preview.Size = New-Object System.Drawing.Size(410, 231)
$script:preview.SizeMode = 'Zoom'
$script:preview.BackColor = [System.Drawing.Color]::FromArgb(14, 16, 20)
$script:preview.BorderStyle = 'FixedSingle'
$form.Controls.Add($script:preview)

$combo = New-Object System.Windows.Forms.ComboBox
$combo.DropDownStyle = 'DropDownList'
$combo.Location = New-Object System.Drawing.Point(266, 368)
$combo.Size = New-Object System.Drawing.Size(230, 26)
$combo.FlatStyle = 'Flat'
$combo.BackColor = $COL_PANEL
$combo.ForeColor = $COL_TEXT
foreach ($w in $cfg.wallpapers) { $combo.Items.Add($w) | Out-Null }
$combo.SelectedItem = $cfg.default_wallpaper
$form.Controls.Add($combo)

function Show-Preview([string]$name) {
    if (-not $name) { return }
    $p = Join-Path (Join-Path $PACK 'wallpapers') $name
    if (-not (Test-Path $p)) { return }
    if ($script:preview.Image) { $script:preview.Image.Dispose() }
    $fs = [System.IO.File]::Open($p, 'Open', 'Read', 'ReadWrite')
    $img = [System.Drawing.Image]::FromStream($fs)
    $script:preview.Image = $img
    $fs.Close()
}

$combo.Add_SelectedIndexChanged({ Show-Preview $combo.SelectedItem })

# ---- 风格切换：深色 / 浅色 两个独立按钮 ----
$lightCount = 0
if ($cfg.icons_light) { $lightCount = $cfg.icons_light.PSObject.Properties.Name.Count }
$darkCount = $cfg.icons.PSObject.Properties.Name.Count

$styleTip = New-Object System.Windows.Forms.Label
$styleTip.Text = '图标风格（点深色 / 浅色立即整套生效）'
$styleTip.ForeColor = $COL_DIM
$styleTip.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 9)
$styleTip.Location = New-Object System.Drawing.Point(24, 336)
$styleTip.Size = New-Object System.Drawing.Size(400, 18)
$form.Controls.Add($styleTip)

function Set-Style([bool]$light) {
    $script:useLight = $light
    $combo.Items.Clear()
    $list = $cfg.wallpapers
    $def  = $cfg.default_wallpaper
    if ($light -and $cfg.wallpapers_light -and $cfg.wallpapers_light.Count -gt 0) {
        $list = $cfg.wallpapers_light
        $def  = $cfg.default_wallpaper_light
    }
    foreach ($w in $list) { $combo.Items.Add($w) | Out-Null }
    $combo.SelectedItem = $def
    Show-Preview $def
    if ($light) {
        $script:lightBtn.BackColor = $COL_BLUE
        $script:darkBtn.BackColor  = $COL_PANEL
        $script:styleTip.Text = '图标风格：浅色（浅底图标 + 浅色壁纸）'
        Log ('已切换到浅色风格：图标库 ' + $lightCount + ' 个 · 浅色壁纸 ' + $list.Count + ' 张')
    } else {
        $script:darkBtn.BackColor  = $COL_BLUE
        $script:lightBtn.BackColor = $COL_PANEL
        $script:styleTip.Text = '图标风格：深色（深色磨砂底板）'
        Log ('已切换到深色风格：图标库 ' + $darkCount + ' 个 · 壁纸 ' + $list.Count + ' 张')
    }
    # 切风格只换图标与壁纸，不重复动文件夹蒙版和小箭头（那是“一键安装”的职责）
    Run-Job {
        $mode = if ($script:useLight) { 'light' } else { 'dark' }
        $n = Apply-ShortcutIcons
        Log ('快捷方式图标已更新：' + $n + ' 个（' + $mode + '）')
        Apply-SystemIcons
        Log '系统图标已更新（此电脑 / 网络 / 回收站 / 用户文件夹）'
        Set-ControlPanelItem
        Set-IconsOnly
        $fn = Update-FolderIni
        Log ('桌面文件夹图标已统一：' + $fn + ' 个文件夹')
        if (Run-Admin ('icons-' + $mode)) { Log '公共桌面快捷方式已同步切换' }
        else { Log '！未获得管理员权限，公共桌面快捷方式可能未切换' }
        if (Set-WallpaperFile $combo.SelectedItem) { Log ('壁纸已设置：' + $combo.SelectedItem) }
        Restart-Explorer
        Log '资源管理器已重启，图标缓存已重建'
    } '风格已切换'
}

$script:darkBtn = New-Btn '深色风格' 24 356 100 32 $COL_PANEL { Set-Style $false }
$script:lightBtn = New-Btn '浅色风格' 132 356 100 32 $COL_PANEL { Set-Style $true }

$wpBtn = New-Btn '应用壁纸' 508 368 78 27 $COL_BLUE {
    $w = $combo.SelectedItem
    if ($w -and (Set-WallpaperFile $w)) { Log ('壁纸已切换：' + $w) } else { Log '！壁纸切换失败' }
}

$openBtn = New-Btn '图标库' 594 368 82 27 $COL_GRAY {
    Start-Process explorer.exe (Join-Path $PACK 'icons')
}

$aboutLink = New-Btn ('关于 v' + $VER) 570 16 112 28 $COL_GRAY {
    $txt = @(
        'GlassDesk 双色玻璃桌面主题   v' + $VER,
        '',
        '把 Windows 桌面统一成「乳白 / 深色磨砂玻璃圆角底板 + 彩色玻璃徽标」风格：',
        '· 快捷方式图标：' + $darkCount + ' 个程序（深浅各一套，共 ' + (Get-ChildItem (Join-Path $PACK 'icons') -Filter *.ico).Count + ' 枚图标）',
        '· 壁纸：深色 ' + $cfg.wallpapers.Count + ' 张 / 浅色 ' + $cfg.wallpapers_light.Count + ' 张（各含 2K 高清版）',
        '· 系统图标：此电脑 / 网络 / 回收站 / 用户文件夹',
        '· 文件夹蒙版 + 快捷方式小箭头隐藏',
        '',
        '用法：',
        '1) 首次使用点「一键安装」：图标 + 文件夹蒙版 + 去小箭头 + 壁纸一次装好',
        '2) 日常切换点「深色风格 / 浅色风格」：图标、系统图标、文件夹图标、壁纸立即整套切换',
        '3) 想回到系统原样点「一键还原」：快捷方式、系统图标、文件夹、小箭头全部恢复',
        '',
        '实现方式：纯本地脚本 + 图标库，不联网、不改系统文件，',
        '所有改动集中在快捷方式、HKCU 图标项与 HKLM 的 Shell Icons 三个位置，',
        '「一键还原」可完全回退。适用 Windows 10 / 11。',
        '',
        '版本 ' + $VER + '　·　打包于 ' + $BUILD_DATE,
        '',
        '本程序已开源（MIT License）：',
        $REPO_URL
    ) -join "`r`n"
    $r = [System.Windows.Forms.MessageBox]::Show($txt, '关于 GlassDesk v' + $VER, 'YesNo', 'Information')
    if ($r -eq 'Yes') { Start-Process $REPO_URL }
}

$logTitle = New-Object System.Windows.Forms.Label
$logTitle.Text = '运行日志'
$logTitle.ForeColor = $COL_TEXT
$logTitle.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 9, [System.Drawing.FontStyle]::Bold)
$logTitle.Location = New-Object System.Drawing.Point(24, 400)
$logTitle.Size = New-Object System.Drawing.Size(120, 20)
$form.Controls.Add($logTitle)

Show-Preview $cfg.default_wallpaper
Log ('图标库：' + $PACK)
Log ('覆盖程序 ' + $darkCount + ' 个 · 壁纸 ' + $cfg.wallpapers.Count + ' 张')
Log ('浅色图标库 ' + $lightCount + ' 个 · 浅色壁纸 ' + $cfg.wallpapers_light.Count + ' 张（点「浅色风格」启用）')
Log 'Win10 LTSC 2021：文件夹蒙版与小箭头走 HKLM Shell Icons，需一次 UAC 授权'
$script:darkBtn.BackColor  = $COL_BLUE
$script:lightBtn.BackColor = $COL_PANEL
# endregion

[void]$form.ShowDialog()


