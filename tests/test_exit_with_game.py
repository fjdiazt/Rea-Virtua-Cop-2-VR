"""Run with: python tests/test_exit_with_game.py VC2VR.exe fake_game.exe"""

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def wait_for_log(path, text, process, seconds=12):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        output = path.read_text(errors="replace") if path.exists() else ""
        if text in output:
            return output
        if process.poll() is not None:
            raise AssertionError(f"process exited before {text!r}:\n{output}")
        time.sleep(0.05)
    raise AssertionError(f"timed out waiting for {text!r}:\n{output}")


def run_case(root, name, vc2vr, fake_game, enabled, args=(), launch=False, menu=False):
    folder = root / name
    vr, project = folder / "VR", folder / "PROJECT"
    vr.mkdir(parents=True)
    project.mkdir()
    exe, game = vr / "VC2VR.exe", project / "PPJ2DD.EXE"
    shutil.copy2(vc2vr, exe)
    shutil.copy2(fake_game, game)
    (vr / "VC2VR.ini").write_text(
        f"[vr]\nwindow=1\nmenu={int(menu)}\nexitwithgame={int(enabled)}\n"
        f"gameexe={game if launch else project / 'missing.exe'}\n"
        "setdevice=0\nnopause=0\n", encoding="ascii"
    )
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    fake = None
    wrapper = None
    log = folder / "wrapper.log"
    try:
        if not launch:
            fake = subprocess.Popen([str(game)], cwd=project, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    creationflags=flags)
        with log.open("w") as output:
            wrapper = subprocess.Popen([str(exe), *args], cwd=vr,
                                       stdin=subprocess.PIPE if menu else subprocess.DEVNULL,
                                       stdout=output,
                                       stderr=subprocess.STDOUT, creationflags=flags)
            if menu:
                wrapper.stdin.write(b"5\n4\n0\n1\n")
                wrapper.stdin.close()
            wait_for_log(log, "reading the live projection", wrapper)
            wait_for_log(log, "window mode", wrapper)
            (project / "exit.now").touch()
            if fake:
                assert fake.wait(timeout=5) == 0, "fake game failed"
            if enabled or menu or "--exit-with-game" in args:
                assert wrapper.wait(timeout=5) == 0, log.read_text(errors="replace")
                assert "exitwithgame: game process exited" in log.read_text(errors="replace")
            else:
                time.sleep(1)
                assert wrapper.poll() is None, "disabled option closed VC2VR"
    finally:
        (project / "exit.now").touch()
        if fake and fake.poll() is None:
            fake.wait(timeout=5)
        if wrapper and wrapper.poll() is None:
            wrapper.terminate()
            wrapper.wait(timeout=5)


def main():
    vc2vr, fake_game = (Path(arg).resolve() for arg in sys.argv[1:3])
    with tempfile.TemporaryDirectory(prefix="vc2vr-exit-") as temp:
        root = Path(temp)
        vr = root / "initial-wait"
        vr.mkdir()
        exe = vr / "VC2VR.exe"
        shutil.copy2(vc2vr, exe)
        (vr / "VC2VR.ini").write_text(
            "[vr]\nwindow=1\nexitwithgame=1\ngameexe=missing.exe\n", encoding="ascii"
        )
        with (vr / "wrapper.log").open("w") as output:
            waiting = subprocess.Popen([str(exe)], cwd=vr, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                wait_for_log(vr / "wrapper.log", "waiting for the game", waiting)
                time.sleep(1)
                assert waiting.poll() is None, "exited before connecting"
            finally:
                waiting.terminate()
                waiting.wait(timeout=5)

        run_case(root, "launched", vc2vr, fake_game, True, launch=True)
        run_case(root, "attached", vc2vr, fake_game, True)
        run_case(root, "menu-toggle", vc2vr, fake_game, False, menu=True)
        run_case(root, "disabled", vc2vr, fake_game, False)
        run_case(root, "cli-cheats", vc2vr, fake_game, False,
                 args=("--exit-with-game", "--infinite-ammo"))

    print("exit-with-game checks passed")


if __name__ == "__main__":
    main()
