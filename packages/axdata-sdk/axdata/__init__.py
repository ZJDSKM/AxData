"""AxData Python SDK."""

from .client import AxDataClient, AxDataError, Client, connect, pro_api

# 08-11 修复：cache.download/get 是未实现的占位符（直接 NotImplementedError），
# 从公共导出移除避免用户误调；cache 模块保留供未来实现
__all__ = [
    "AxDataClient",
    "AxDataError",
    "Client",
    "connect",
    "pro_api",
]

__version__ = "0.1.4"
