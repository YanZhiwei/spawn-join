"""个人助理宿主应用的稳定错误分类。"""

from __future__ import annotations


class HostError(Exception):
    """宿主应用稳定错误的基类。

    宿主错误描述宿主侧哪个关注点失败（配置、存储、调度、审批）；它们
    有意不包装模型 Provider 或框架错误——后者的错误分类保留在各自的
    拥有包中。
    """


class HostConfigError(HostError):
    """应用配置缺失、格式非法或取值无效。"""


class HostStoreError(HostError):
    """工作项或审批持久化失败。"""


class WorkTransitionError(HostStoreError):
    """工作项状态迁移未被状态机允许。"""


class HostSchedulingError(HostError):
    """调度器无法启动或约束某个工作项。"""


class HostApprovalError(HostError):
    """审批记账或恢复执行失败。"""
