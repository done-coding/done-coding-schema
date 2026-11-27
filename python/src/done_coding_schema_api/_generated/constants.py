# 本文件由 scripts/generate.mjs 依据 schemas/ 的定义生成，勿手改。
# 改了定义后在仓根运行 pnpm gen；pnpm check:generated 会核对本文件与定义一致。
from types import MappingProxyType
from typing import Final, Literal


SUCCESS_CODES: Final = MappingProxyType({"OK": "OK"})
"""成功码。成功外壳的 code 只能是这一组里的值。"""
SuccessCode = Literal["OK"]
