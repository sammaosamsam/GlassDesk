# Apply icon set. dark -> <slug>.ico, light -> l_<slug>.ico (same folder)
param([string]$Set = "dark")

$root = 'C:\Users\Administrator\AppData\Local\DesktopIconTheme'
$icons = Join-Path $root 'pack\icons'
$cfgPath = Join-Path $root 'pack\install_config.json'
$cfg = Get-Content $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json

if ($Set -eq "dark") { $wp = Join-Path $root ('pack\wallpapers\' + $cfg.default_wallpaper); $folderIco = $cfg.folder_icon }
else { $wp = Join-Path $root ('pack\wallpapers\' + $cfg.default_wallpaper_light); $folderIco = $cfg.folder_icon_light }

function Target($path) {
  if (-not $path) { return $null }
  $leaf = Split-Path $path -Leaf
  if ($leaf -eq '') { return $null }
  if ($Set -eq "dark") {
    if ($leaf -like 'l_*') { $leaf = $leaf.Substring(2) }
  } else {
    if ($leaf -notlike 'l_*') { $leaf = 'l_' + $leaf }
  }
  $p = Join-Path $icons $leaf
  if (Test-Path $p) { return "$p,0" }
  return $null
}

$sh = New-Object -ComObject WScript.Shell
foreach ($d in @("$env:USERPROFILE\Desktop", "$env:PUBLIC\Desktop")) {
  Get-ChildItem $d -Filter *.lnk | ForEach-Object {
    $s = $sh.CreateShortcut($_.FullName)
    $cur = ($s.IconLocation -split ',')[0]
    $t = Target $cur
    if (-not $t) {
      $exe = ''
      if ($s.TargetPath) { $exe = Split-Path $s.TargetPath -Leaf }
      $map = if ($Set -eq "dark") { $cfg.icons } else { $cfg.icons_light }
      $hit = $map.PSObject.Properties | Where-Object { $_.Name.ToLower() -eq $exe.ToLower() } | Select-Object -First 1
      if ($hit) {
        $p = Join-Path $icons $hit.Value
        if (Test-Path $p) { $t = "$p,0" }
      }
    }
    if ($t) { $s.IconLocation = $t; $s.Save() }
  }
}

# system icons via HKCU CLSID DefaultIcon
$sysMap = @{
  '{20D04FE0-3AEA-1069-A2D8-08002B30309D}' = 'sys_pc.ico'
  '{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}' = 'sys_network.ico'
  '{645FF040-5081-101B-9F08-00AA002F954E}' = 'sys_bin.ico'
  '{59031A47-3F72-44A7-89C5-5595FE6B30EE}' = 'sys_user.ico'
}
if ($Set -eq "light" -and $cfg.system_icons_light) {
  foreach ($g in $cfg.system_icons_light.PSObject.Properties.Name) { $sysMap[$g] = $cfg.system_icons_light.$g }
}
foreach ($g in $sysMap.Keys) {
  $p = Join-Path $icons $sysMap[$g]
  if (-not (Test-Path $p)) { continue }
  $v = "$p,0"
  foreach ($base in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\CLSID',
                      'HKCU:\Software\Classes\CLSID')) {
    $kk = Join-Path (Join-Path $base $g) 'DefaultIcon'
    if (-not (Test-Path $kk)) { New-Item -Path $kk -Force | Out-Null }
    Set-ItemProperty -Path $kk -Name '(default)' -Value $v
    if ($g -eq '{645FF040-5081-101B-9F08-00AA002F954E}') {
      Set-ItemProperty -Path $kk -Name 'Empty' -Value $v
      Set-ItemProperty -Path $kk -Name 'Full' -Value $v
    }
  }
}

$k = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Icons'
# desktop.ini custom folder icons follow theme
foreach ($d in @("$env:USERPROFILE\Desktop", "$env:PUBLIC\Desktop")) {
  Get-ChildItem $d -Directory -Force | ForEach-Object {
    $ini = Join-Path $_.FullName 'desktop.ini'
    if (Test-Path $ini) {
      $txt = Get-Content $ini -Raw -ErrorAction SilentlyContinue
      if ($txt -and $txt.Contains('pack\icons')) {
        $leaf = if ($Set -eq 'light') { $cfg.folder_icon_light } else { $cfg.folder_icon }
        $p = Join-Path $icons $leaf
        $new = [regex]::Replace($txt, 'pack\\icons\\[^,]+\.ico', ('pack\icons\' + $leaf))
        Set-Content $ini $new -Encoding UTF8
      }
    }
  }
}
$fi = Join-Path $icons $folderIco
Set-ItemProperty $k -Name '3' -Value "$fi,0" -ErrorAction SilentlyContinue
Set-ItemProperty $k -Name '4' -Value "$fi,0" -ErrorAction SilentlyContinue

Add-Type -Namespace W -Name D -MemberDefinition '[DllImport("user32.dll")] public static extern int SystemParametersInfo(int a,int b,string c,int d);'
[W.D]::SystemParametersInfo(20, 0, $wp, 3) | Out-Null
Set-ItemProperty 'HKCU:\Control Panel\Desktop' -Name Wallpaper -Value $wp
Set-ItemProperty 'HKCU:\Control Panel\Desktop' -Name WallpaperStyle -Value '10'
Set-ItemProperty 'HKCU:\Control Panel\Desktop' -Name TileWallpaper -Value '0'
Write-Output ("OK " + $Set)
