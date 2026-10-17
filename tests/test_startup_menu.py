"""Run with: python tests/test_startup_menu.py path/to/VC2VR.exe"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def setup(root, name, source, vr_settings, view_settings=""):
    folder = root / name
    vr, project = folder / "VR", folder / "PROJECT"
    vr.mkdir(parents=True)
    project.mkdir()
    exe = vr / "VC2VR.exe"
    shutil.copy2(source, exe)
    vr_ini = vr / "VC2VR.ini"
    view_ini = project / "HGL_VIEW.ini"
    vr_ini.write_text(
        f"[vr]\ngameexe = {project / 'PPJ2DD.EXE'}\n" + vr_settings,
        encoding="ascii",
    )
    view_ini.write_text("[view]\n" + view_settings, encoding="ascii")
    return exe, vr_ini, view_ini


def launch(exe, args=(), choices="0\n"):
    result = subprocess.run(
        [str(exe), *args],
        input=choices,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=3,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert result.returncode == 0, result.stdout
    return result.stdout


def main():
    source = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="vc2vr-menu-") as temp:
        root = Path(temp)

        exe, vr_ini, view_ini = setup(root, "cli", source, "menu = 0\n")
        before = vr_ini.read_bytes()
        output = launch(exe, ("--menu",))
        assert "Cheats" in output and "Display" in output, output
        assert vr_ini.read_bytes() == before, "opening menu changed INI"
        assert not list(vr_ini.parent.glob("*.menu-*.bak"))

        exe, vr_ini, view_ini = setup(
            root, "ini", source, "menu = 1\nwindow = 1\ninfinite_ammo = 1\n",
        )
        output = launch(exe, choices="2\n1\n0\n3\n0\n0\n")
        assert "Infinite ammo: ON" in output and "Infinite ammo: OFF" in output, output
        assert "Mode: Window" in output, output
        assert "AMMO ON" in output and "AMMO OFF" in output, output
        assert "\x1b" not in output, "console colors leaked into redirected output"
        assert "infinite_ammo=0" in vr_ini.read_text().replace(" ", ""), vr_ini.read_text()
        assert list(vr_ini.parent.glob("*.menu-*.bak")), "missing VR INI backup"

        exe, vr_ini, view_ini = setup(root, "override", source, "menu = 0\nwindow = 1\n")
        before = vr_ini.read_bytes()
        output = launch(
            exe, ("--menu", "--stereo", "--infinite-lives"),
            "2\n0\n3\n0\n0\n",
        )
        assert "Infinite lives: ON" in output and "Mode: Stereo" in output, output
        assert vr_ini.read_bytes() == before, "CLI-only choices were saved"

        exe, vr_ini, view_ini = setup(
            root, "view", source, "; keep VR comment\nmenu = 1\nakimbo = 1\n",
            "; keep view comment\nwindow = 1\nakimbo = 1\ntexgain = 100\n",
        )
        vr_before, view_before = vr_ini.read_bytes(), view_ini.read_bytes()
        output = launch(exe, choices="3\n5\n0\n4\n1\n0\n5\n3\n150\n0\n0\n")
        assert "Monitor window: ON" in output and "Brightness: 150%" in output, output
        view = view_ini.read_text().replace(" ", "")
        assert "window=0" in view and "akimbo=0" in view and "texgain=150" in view, view
        assert "akimbo=0" in vr_ini.read_text().replace(" ", ""), vr_ini.read_text()
        assert "; keep VR comment" in vr_ini.read_text()
        assert "; keep view comment" in view_ini.read_text()
        assert next(vr_ini.parent.glob("*.menu-*.bak")).read_bytes() == vr_before
        assert next(view_ini.parent.glob("*.menu-*.bak")).read_bytes() == view_before

        exe, vr_ini, _ = setup(
            root, "exit-toggle", source, "menu = 1\nexitwithgame = 0\n",
        )
        before = vr_ini.read_bytes()
        output = launch(exe, choices="5\n4\n0\n0\n")
        assert "Exit with game: OFF" in output and "Exit with game: ON" in output
        assert "exitwithgame=1" in vr_ini.read_text().replace(" ", "")
        assert next(vr_ini.parent.glob("*.menu-*.bak")).read_bytes() == before

        exe, vr_ini, _ = setup(root, "exit-cli", source, "menu = 0\nexitwithgame = 0\n")
        before = vr_ini.read_bytes()
        output = launch(
            exe, ("--menu", "--exit-with-game", "--infinite-ammo"),
            "5\n0\n2\n0\n0\n",
        )
        assert "Exit with game: ON" in output and "Infinite ammo: ON" in output
        assert vr_ini.read_bytes() == before, "CLI-only choices were saved"

    print("startup menu checks passed")


if __name__ == "__main__":
    main()
