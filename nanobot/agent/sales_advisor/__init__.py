"""Sales Advisor Module - 小安虚拟保险顾问"""

from nanobot.agent.sales_advisor.persona import XiaoAnPersona
from nanobot.agent.sales_advisor.state import (
    ConversationState,
    CustomerProfile,
    SalesStage,
    StateManager,
)
from nanobot.agent.sales_advisor.flow import SalesFlowManager
from nanobot.agent.sales_advisor.capabilities import CapabilityModule
from nanobot.agent.sales_advisor.knowledge import (
    ProductKnowledge,
    PolicyDatabase,
    SalesKnowledge,
)

__all__ = [
    # 人设
    "XiaoAnPersona",
    # 状态
    "ConversationState",
    "CustomerProfile",
    "SalesStage",
    "StateManager",
    # 流程
    "SalesFlowManager",
    # 能力
    "CapabilityModule",
    # 知识
    "ProductKnowledge",
    "PolicyDatabase",
    "SalesKnowledge",
]
