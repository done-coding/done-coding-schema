"""构建 Python 包并核对产物：wheel 与 sdist 里的定义文件齐全，且与仓根 schemas/ 逐字节一致。

    uv run --project python --frozen python scripts/check-python-dist.py

只用标准库；构建到临时目录，不动 python/dist。任一项不符时退出码 1。
"""

import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "done_coding_schema_api"
EXPECTED = {
    path.name: path.read_bytes() for path in (ROOT / "schemas").glob("*.schema.json")
}


def _compare(label: str, shipped: dict[str, bytes]) -> list[str]:
    problems = [f"{label} 缺少 {name}" for name in sorted(EXPECTED.keys() - shipped)]
    problems += [f"{label} 多出 {name}" for name in sorted(shipped.keys() - EXPECTED)]
    problems += [
        f"{label} 的 {name} 与仓根不一致"
        for name in sorted(EXPECTED.keys() & shipped.keys())
        if shipped[name] != EXPECTED[name]
    ]
    return problems


def _wheel(path: Path) -> list[str]:
    prefix = f"{PACKAGE}/schemas/"
    with zipfile.ZipFile(path) as wheel:
        names = wheel.namelist()
        shipped = {
            name.removeprefix(prefix): wheel.read(name)
            for name in names
            if name.startswith(prefix) and name.endswith(".json")
        }
        has_license = any(
            name.endswith(".dist-info/licenses/LICENSE") for name in names
        )
    problems = _compare(f"wheel {path.name}", shipped)
    return problems + ([] if has_license else [f"wheel {path.name} 缺少 LICENSE"])


def _sdist(path: Path) -> list[str]:
    with tarfile.open(path) as sdist:
        members = {member.name: member for member in sdist.getmembers()}
        base = path.name.removesuffix(".tar.gz")
        prefix = f"{base}/src/{PACKAGE}/schemas/"
        shipped = {}
        for name, member in members.items():
            if name.startswith(prefix) and name.endswith(".json"):
                file = sdist.extractfile(member)
                shipped[name.removeprefix(prefix)] = file.read() if file else b""
    problems = _compare(f"sdist {path.name}", shipped)
    has_license = f"{base}/LICENSE" in members
    return problems + ([] if has_license else [f"sdist {path.name} 缺少 LICENSE"])


def main() -> int:
    with tempfile.TemporaryDirectory() as out:
        subprocess.run(
            ["uv", "build", "--project", str(ROOT / "python"), "-q", "--out-dir", out],
            check=True,
        )
        wheels = sorted(Path(out).glob("*.whl"))
        sdists = sorted(Path(out).glob("*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            print(f"应各有 1 个 wheel 与 sdist，实际 {len(wheels)} / {len(sdists)}")
            return 1
        problems = _wheel(wheels[0]) + _sdist(sdists[0])
    if problems:
        print("Python 包产物与定义不一致：", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print("在仓根运行 pnpm gen 后重新构建。", file=sys.stderr)
        return 1
    print(
        f"Python 包产物检查通过（wheel 与 sdist 各含 {len(EXPECTED)} 份定义文件与 LICENSE）。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
