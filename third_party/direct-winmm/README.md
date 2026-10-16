The optional `audio/winmm.dll` is built from [Direct-WinMM](https://github.com/Jione/Direct-WinMM)
commit `dfd242ffd741e4cd2b8e000fafeefb47a76a0122` (CC0-1.0). Its
`THIRD-PARTY-NOTICES` ships beside the DLL. `vc2vr.patch` makes `PROJECT`
prefer `../MUSIC/TrackNN` and keeps Direct-WinMM's existing local `Music`
search as fallback. It also uses the current Windows SDK for x86 builds.

From this repository's root, rebuild in a Visual Studio Developer PowerShell:

```powershell
git clone --recursive https://github.com/Jione/Direct-WinMM.git direct-winmm
git -C direct-winmm checkout dfd242ffd741e4cd2b8e000fafeefb47a76a0122
git -C direct-winmm submodule update --init --recursive
git -C direct-winmm apply ../third_party/direct-winmm/vc2vr.patch
MSBuild.exe direct-winmm/DirectWinMM.sln /t:WinmmStubs /p:Configuration=Release /p:Platform=x86 /p:PlatformToolset=v145
```

The output is `direct-winmm/Release/winmm.dll`.
