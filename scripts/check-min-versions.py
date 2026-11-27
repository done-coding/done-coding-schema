"""在最低支持版本上跑全部 Python 测试：装本机构建的 wheel，而不是源码目录。

    uv run --project python --frozen python scripts/check-min-versions.py

最低版本只有一个来源——python/pyproject.toml：

- Python：``requires-python`` 的下界（如 ``>=3.10`` → 3.10）；
- 运行时依赖：``dependencies`` 里每一项的下界，装该次版本的最新修订版
  （如 ``pydantic>=2.11,<3`` → ``pydantic~=2.11.0``）；
- 测试工具：``dependency-groups.dev`` 里锁定的 pytest 与 jsonschema；
- FastAPI 不是运行时依赖，pyproject 里没有它的支持下界；README 写明支持到的最低版本
  就是这里的 ``FASTAPI_MINIMUM``。

步骤：构建 wheel → 建临时虚拟环境 → 装 wheel 与上面这些版本 → 把测试与样例拷到临时目录
（测试按相对位置找 schemas/examples）→ 跑 pytest，并核对导入的是装好的包 → 清理。
要联网装包，耗时较长，不并进 pnpm check；发布前必做，见 docs/release.md。
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "python"
PACKAGE = "done_coding_schema_api"
FASTAPI_MINIMUM = "0.140.7"
TEST_TOOLS = ("pytest", "jsonschema")
# 打印装到的版本，并确认导入的是装好的 wheel，不是源码目录。
SHOW_VERSIONS = (
    "import sys, pydantic, fastapi, done_coding_schema_api as m;"
    "print('Python', sys.version.split()[0], '| pydantic', pydantic.VERSION,"
    " '| FastAPI', fastapi.__version__);"
    "assert 'site-packages' in m.__file__, m.__file__"
)

LOWER_BOUND = re.compile(r">=\s*(\d+)\.(\d+)")
NAME = re.compile(r"^[A-Za-z0-9._-]+")


def _lower_bound(spec: str, what: str) -> tuple[str, str]:
    match = LOWER_BOUND.search(spec)
    if not match:
        raise SystemExit(f"{what} 没有写成「>=主.次」形式的下界：{spec!r}")
    return match.group(1), match.group(2)


def requirements() -> tuple[str, list[str]]:
    """(最低 Python, 要装的依赖)，全部取自 pyproject.toml。"""
    project = tomllib.loads((PROJECT / "pyproject.toml").read_text(encoding="utf-8"))
    major, minor = _lower_bound(
        project["project"]["requires-python"], "requires-python"
    )
    python = f"{major}.{minor}"
    packages = []
    for spec in project["project"]["dependencies"]:
        name = NAME.match(spec).group(0)  # type: ignore[union-attr]
        major, minor = _lower_bound(spec, f"依赖 {name}")
        packages.append(f"{name}~={major}.{minor}.0")
    dev = {
        NAME.match(spec).group(0): spec for spec in project["dependency-groups"]["dev"]
    }  # type: ignore[union-attr]
    for tool in TEST_TOOLS:
        if "==" not in dev.get(tool, ""):
            raise SystemExit(f"dependency-groups.dev 里没有锁定版本的 {tool}")
        packages.append(dev[tool])
    packages.append(f"fastapi=={FASTAPI_MINIMUM}")
    return python, packages


def run(command: list[str], **kwargs: object) -> None:
    print("$", " ".join(command), flush=True)
    subprocess.run(command, check=True, **kwargs)  # type: ignore[call-overload]


def main() -> None:
    python, packages = requirements()
    with tempfile.TemporaryDirectory(prefix="schema-min-versions-") as tmp:
        work = Path(tmp)
        dist = work / "dist"
        run(
            [
                "uv",
                "build",
                "--project",
                str(PROJECT),
                "--wheel",
                "--out-dir",
                str(dist),
            ]
        )
        [wheel] = dist.glob("*.whl")
        venv = work / "venv"
        run(["uv", "venv", "--quiet", "--python", python, str(venv)])
        interpreter = venv / (
            "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
        )
        run(
            [
                "uv",
                "pip",
                "install",
                "--quiet",
                "--python",
                str(interpreter),
                str(wheel),
                *packages,
            ]
        )
        # 测试按相对位置找仓根的 schemas/：保持 python/tests 与 schemas 的相对布局。
        layout = work / "repo"
        shutil.copytree(
            PROJECT / "tests",
            layout / "python" / "tests",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        shutil.copytree(ROOT / "schemas", layout / "schemas")
        tests = layout / "python"
        run([str(interpreter), "-c", SHOW_VERSIONS], cwd=tests)
        run(
            [str(interpreter), "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
            cwd=tests,
        )
    print(f"最低支持版本测试通过（Python {python}；{'、'.join(packages)}）。")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(
            f"最低支持版本测试失败：{' '.join(map(str, error.cmd))} 退出码 {error.returncode}"
        )
        sys.exit(1)
