"""小安虚拟保险顾问 - 主入口

整合人设、状态、流程、能力、知识库，提供完整的销售顾问能力
"""

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from nanobot.agent.sales_advisor.persona import XiaoAnPersona
from nanobot.agent.sales_advisor.state import (
    ConversationState,
    CustomerProfile,
    SalesStage,
    StateManager,
)
from nanobot.agent.sales_advisor.flow import SalesFlowManager
from nanobot.agent.sales_advisor.capabilities import CapabilityModule
from nanobot.agent.sales_advisor.knowledge import SalesKnowledge

if TYPE_CHECKING:
    from nanobot.providers.base import LLMProvider
    from nanobot.session import Session


@dataclass
class SalesContext:
    """销售上下文"""
    session_key: str = ""
    customer: CustomerProfile = field(default_factory=CustomerProfile)
    current_stage: str = SalesStage.OPENING
    stage_history: list[str] = field(default_factory=list)
    last_product_mentioned: str = ""
    current_topic: str = ""
    turn_count: int = 0

    def to_context(self) -> str:
        """转换为上下文字符串"""
        parts = []
        parts.append(f"客户: {self.customer.to_context()}")
        parts.append(f"阶段: {self.current_stage}")
        if self.last_product_mentioned:
            parts.append(f"产品: {self.last_product_mentioned}")
        return "\n".join(parts)


@dataclass
class AdvisorConfig:
    """顾问配置"""
    use_llm_stage_detection: bool = False  # 是否使用LLM检测阶段
    use_llm_capabilities: bool = False  # 是否使用LLM能力处理
    min_stage_advance_turns: int = 2  # 最少对话轮次才推进阶段


@dataclass
class XiaoAnAdvisor:
    """
    小安虚拟保险顾问

    整合所有模块，提供完整的销售顾问能力

    使用方式:
        advisor = XiaoAnAdvisor(session, llm_provider)
        response = await advisor.chat(user_message)
    """

    session: Any = field(default=None)
    llm: Any = field(default=None)
    config: AdvisorConfig = field(default_factory=AdvisorConfig)

    # 子模块
    persona: XiaoAnPersona = field(default_factory=XiaoAnPersona)
    flow_manager: SalesFlowManager = field(default_factory=SalesFlowManager)
    capability_module: CapabilityModule = field(default_factory=CapabilityModule)
    knowledge: SalesKnowledge = field(default_factory=SalesKnowledge)

    # 状态
    _initialized: bool = field(default=False, repr=False)
    _turn_count: int = field(default=0, repr=False)

    def __post_init__(self):
        if not self._initialized:
            self._init_modules()
            self._initialized = True

    def _init_modules(self) -> None:
        """初始化子模块"""
        # 知识库初始化
        if not hasattr(self.knowledge, '_initialized') or not self.knowledge._initialized:
            self.knowledge = SalesKnowledge()

    @property
    def state_manager(self) -> StateManager | None:
        """获取状态管理器"""
        if self.session:
            return StateManager(self.session)
        return None

    def get_system_prompt(self, context: SalesContext | None = None) -> str:
        """
        获取系统提示词

        Args:
            context: 销售上下文

        Returns:
            系统提示词字符串
        """
        prompt_parts = []

        # 基础人设
        prompt_parts.append(self.persona.get_system_prompt())

        # 当前阶段指导
        if context:
            stage_prompt = self.flow_manager.get_stage_prompt(context.current_stage)
            if stage_prompt:
                prompt_parts.append(stage_prompt)

            # 客户信息
            prompt_parts.append(f"\n客户背景: {context.customer.to_context()}")

            # 最近讨论的产品
            if context.last_product_mentioned:
                product = self.knowledge.products.get_product(context.last_product_mentioned)
                if product:
                    prompt_parts.append(f"\n产品信息: {self.knowledge.products.format_product_intro(product)}")

        return "\n\n".join(prompt_parts)

    async def chat(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
        session_key: str = "",
    ) -> dict[str, Any]:
        """
        处理用户消息

        Args:
            user_message: 用户消息
            history: 对话历史
            session_key: 会话标识

        Returns:
            {
                "response": str,  # 小安的回答
                "context": SalesContext,  # 更新后的上下文
                "stage_changed": bool,  # 阶段是否变化
                "new_stage": str | None,  # 新阶段
            }
        """
        self._turn_count += 1

        # 获取或创建上下文
        context = self._get_or_create_context(session_key)

        # 分析是否需要推进阶段
        agent_response = ""
        stage_changed = False
        new_stage = None

        if history and len(history) > 0:
            last_msg = history[-1]
            agent_response = last_msg.get("content", "")

        # 检测阶段变化
        detected_stage = self.flow_manager.detect_stage_from_message(user_message, agent_response)
        if detected_stage and detected_stage != context.current_stage:
            # 检查是否满足最小轮次要求
            if self._can_advance_stage(context):
                stage_changed = True
                new_stage = detected_stage
                context.stage_history.append(context.current_stage)
                context.current_stage = new_stage

        # 构建prompt
        messages = self._build_messages(user_message, context, history)

        # 调用LLM
        if self.llm:
            response = await self.llm.chat(messages)
        else:
            response = "小安暂时无法回答，请稍后再试。"

        # 验证回答
        is_valid, error_msg = self.persona.validate_response(response)
        if not is_valid:
            # 重新生成或修正
            response = await self._regenerate_response(user_message, context, history, error_msg)

        # 更新上下文
        context.turn_count = self._turn_count
        context.current_topic = self._extract_topic(user_message)

        # 从用户消息提取客户信息
        context.customer.update_from_message(user_message, "user")

        # 检测提到的产品
        mentioned_product = self._extract_product(user_message)
        if mentioned_product:
            context.last_product_mentioned = mentioned_product
            if mentioned_product not in context.customer.discussed_products:
                context.customer.discussed_products.append(mentioned_product)

        return {
            "response": response,
            "context": context,
            "stage_changed": stage_changed,
            "new_stage": new_stage,
        }

    def _get_or_create_context(self, session_key: str) -> SalesContext:
        """获取或创建上下文"""
        if self.state_manager:
            state = self.state_manager.get_or_create(session_key)
            return self._state_to_context(state)

        return SalesContext(session_key=session_key)

    def _state_to_context(self, state: ConversationState) -> SalesContext:
        """ConversationState -> SalesContext"""
        return SalesContext(
            session_key=state.session_key,
            customer=state.customer,
            current_stage=state.current_stage,
            stage_history=state.stage_history.copy(),
            last_product_mentioned=state.last_product_mentioned,
            current_topic=state.current_topic,
            turn_count=state.turn_count,
        )

    def _context_to_state(self, context: SalesContext, state: ConversationState) -> None:
        """SalesContext -> ConversationState"""
        state.current_stage = context.current_stage
        state.stage_history = context.stage_history
        state.last_product_mentioned = context.last_product_mentioned
        state.current_topic = context.current_topic
        state.turn_count = context.turn_count

    def save_context(self, context: SalesContext) -> None:
        """保存上下文到Session"""
        if self.state_manager:
            state = self.state_manager.get_or_create(context.session_key)
            self._context_to_state(context, state)
            self.state_manager.save_state(state)

    def _can_advance_stage(self, context: SalesContext) -> bool:
        """检查是否可以推进阶段"""
        return context.turn_count >= self.config.min_stage_advance_turns

    def _build_messages(
        self,
        user_message: str,
        context: SalesContext,
        history: list[dict[str, Any]] | None,
    ) -> list[dict[str, str]]:
        """构建消息列表"""
        messages = []

        # System prompt
        system_prompt = self.get_system_prompt(context)
        messages.append({"role": "system", "content": system_prompt})

        # History (recent 6 messages)
        if history:
            for msg in history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    messages.append({"role": role, "content": content})

        # Current message
        messages.append({"role": "user", "content": user_message})

        return messages

    async def _regenerate_response(
        self,
        user_message: str,
        context: SalesContext,
        history: list[dict[str, Any]] | None,
        error_hint: str,
    ) -> str:
        """重新生成回答"""
        messages = self._build_messages(user_message, context, history)

        # 添加错误提示
        if messages[0]["role"] == "system":
            messages[0]["content"] += f"\n\n注意: {error_hint}"

        if self.llm:
            return await self.llm.chat(messages)
        return "小安暂时无法回答，请稍后再试。"

    def _extract_topic(self, message: str) -> str:
        """从消息中提取话题"""
        message_lower = message.lower()

        topics = {
            "条款咨询": ["条款", "保什么", "赔付", "理赔", "免责"],
            "保费咨询": ["保费", "价格", "多少钱", "预算"],
            "购买意向": ["购买", "投保", "下单", "决定"],
            "理赔咨询": ["理赔", "怎么赔", "赔付"],
            "产品咨询": ["产品", "推荐", "哪个好"],
            "核保咨询": ["健康", "告知", "脂肪肝", "既往症"],
        }

        for topic, keywords in topics.items():
            for kw in keywords:
                if kw in message_lower:
                    return topic

        return context.current_topic if hasattr(self, '_last_topic') else ""

    def _extract_product(self, message: str) -> str | None:
        """从消息中提取产品名称"""
        # 安家守护
        if "安家守护" in message:
            return "安家守护"

        # 其他产品可以继续扩展
        products = self.knowledge.products.get_all_products()
        for product in products:
            if product.name in message or product.id in message:
                return product.name

        return None

    def get_product_info(self, product_name: str) -> str:
        """
        获取产品信息

        Args:
            product_name: 产品名称

        Returns:
            格式化的产品介绍
        """
        product = self.knowledge.products.get_product(product_name)
        if not product:
            return f"未找到产品: {product_name}"

        return self.knowledge.products.format_product_intro(product)

    def get_policy_info(self, policy_key: str) -> str:
        """
        获取条款信息

        Args:
            policy_key: 条款关键词

        Returns:
            格式化的条款信息
        """
        policy = self.knowledge.policies.get_policy(policy_key)
        if not policy:
            return f"未找到条款: {policy_key}"

        return self.knowledge.policies.format_policy(policy)

    def get_objection_response(self, objection_type: str, context: dict[str, Any]) -> str:
        """
        获取异议处理话术

        Args:
            objection_type: 异议类型
            context: 上下文信息

        Returns:
            处理话术
        """
        return self.knowledge.get_objection_response(objection_type, context)

    def get_stage_progress(self, context: SalesContext) -> str:
        """
        获取销售进度

        Args:
            context: 销售上下文

        Returns:
            进度描述
        """
        stages = SalesStage.stage_order()
        try:
            current_idx = stages.index(context.current_stage)
        except ValueError:
            current_idx = 0

        total = len(stages)
        percentage = int((current_idx / total) * 100)

        stage_name = self.flow_manager.get_stage_name(context.current_stage)

        return f"{stage_name} ({current_idx + 1}/{total})"

    def reset(self, session_key: str = "") -> None:
        """
        重置顾问状态

        Args:
            session_key: 会话标识
        """
        self._turn_count = 0
        self.flow_manager.reset()

        if self.state_manager:
            self.state_manager.clear_state()

    def export_context(self, context: SalesContext) -> dict[str, Any]:
        """
        导出上下文为字典

        Args:
            context: 销售上下文

        Returns:
            字典
        """
        return {
            "session_key": context.session_key,
            "customer": {
                "name": context.customer.name,
                "age": context.customer.age,
                "gender": context.customer.gender,
                "family": context.customer.family,
                "has_children": context.customer.has_children,
                "children_age": context.customer.children_age,
                "has_mortgage": context.customer.has_mortgage,
                "income_annual": context.customer.income_annual,
                "budget": context.customer.budget,
                "concerns": context.customer.concerns,
                "needs": context.customer.needs,
                "discussed_products": context.customer.discussed_products,
                "expressed_objections": context.customer.expressed_objections,
            },
            "current_stage": context.current_stage,
            "stage_history": context.stage_history,
            "stage_progress": self.get_stage_progress(context),
            "last_product_mentioned": context.last_product_mentioned,
            "current_topic": context.current_topic,
            "turn_count": context.turn_count,
        }
