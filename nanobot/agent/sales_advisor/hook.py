"""Sales Advisor Hook - 集成到 Nanobot Agent 框架

通过 AgentHook 接口将小安销售顾问能力嵌入到 Nanobot 的对话流程中。
"""

from dataclasses import dataclass, field
from typing import Any

from nanobot.agent.hook import AgentHook, AgentHookContext
from nanobot.agent.sales_advisor.advisor import XiaoAnAdvisor, SalesContext, AdvisorConfig
from nanobot.agent.sales_advisor.state import StateManager, ConversationState
from nanobot.agent.sales_advisor.flow import SalesStage


@dataclass
class SalesAdvisorHookConfig:
    """销售顾问钩子配置"""
    enabled: bool = True  # 是否启用销售顾问模式
    use_llm_stage_detection: bool = False  # 是否使用LLM检测阶段
    min_stage_advance_turns: int = 2  # 最少轮次才推进阶段

    # 自动注入到 system prompt 的内容
    inject_sales_context: bool = True  # 注入销售上下文
    inject_product_knowledge: bool = True  # 注入产品知识
    inject_stage_guidance: bool = True  # 注入阶段指导


@dataclass
class SalesAdvisorHook(AgentHook):
    """
    销售顾问钩子

    集成到 Nanobot 的生命周期中，提供：
    1. 在 before_iteration 中准备销售上下文
    2. 在 finalize_content 中注入销售相关内容
    3. 管理会话状态中的销售状态
    """

    config: SalesAdvisorHookConfig = field(default_factory=SalesAdvisorHookConfig)
    _advisor: XiaoAnAdvisor | None = field(default=None, init=False, repr=False)
    _session_key: str = field(default="", init=False, repr=False)
    _current_context: SalesContext | None = field(default=None, init=False, repr=False)

    def __post_init__(self):
        if not self._advisor:
            config = AdvisorConfig(
                use_llm_stage_detection=self.config.use_llm_stage_detection,
                min_stage_advance_turns=self.config.min_stage_advance_turns,
            )
            self._advisor = XiaoAnAdvisor(config=config)

    @property
    def advisor(self) -> XiaoAnAdvisor:
        """获取顾问实例"""
        return self._advisor

    def wants_streaming(self) -> bool:
        """不干预流式输出"""
        return False

    async def before_iteration(self, context: AgentHookContext) -> None:
        """
        在每次迭代前调用

        从 session metadata 恢复销售状态
        """
        if not self.config.enabled:
            return

        # session_key 从 context 中获取（如果可用）
        # 这里主要是标记需要检查状态
        pass

    async def on_stream(self, context: AgentHookContext, delta: str) -> None:
        """流式输出回调（不干预）"""
        pass

    async def on_stream_end(self, context: AgentHookContext, *, resuming: bool) -> None:
        """流式结束时调用"""
        pass

    async def before_execute_tools(self, context: AgentHookContext) -> None:
        """执行工具前调用"""
        pass

    async def after_iteration(self, context: AgentHookContext) -> None:
        """
        每次迭代后调用

        更新销售状态到 session metadata
        """
        if not self.config.enabled:
            return

        if self._current_context and self._session_key:
            self._advisor.save_context(self._current_context)

    def finalize_content(self, context: AgentHookContext, content: str | None) -> str | None:
        """
        最终化内容时调用

        在回复内容后面追加销售相关信息（如当前阶段、推荐产品等）
        """
        if not self.config.enabled or not content:
            return content

        if not self.config.inject_sales_context or not self._current_context:
            return content

        # 可以在这里添加一些隐式的上下文标记
        # 但不直接修改用户可见的内容，保持对话自然

        return content

    def set_session_key(self, session_key: str) -> None:
        """设置会话标识"""
        self._session_key = session_key
        if self._advisor and self._advisor.state_manager:
            self._advisor.state_manager.session.key = session_key

    def set_session(self, session: Any) -> None:
        """
        设置会话对象

        Args:
            session: Session 对象
        """
        if self._advisor:
            self._advisor.state_manager.session = session
            self._session_key = session.key

    def get_current_stage(self) -> str:
        """获取当前销售阶段"""
        if self._current_context:
            return self._current_context.current_stage
        return SalesStage.OPENING

    def get_stage_progress(self) -> str:
        """获取销售进度"""
        if self._advisor and self._current_context:
            return self._advisor.get_stage_progress(self._current_context)
        return "开场 (1/8)"

    def get_export_data(self) -> dict[str, Any] | None:
        """导出销售数据"""
        if self._advisor and self._current_context:
            return self._advisor.export_context(self._current_context)
        return None

    def reset_sales_state(self) -> None:
        """重置销售状态"""
        if self._advisor:
            self._advisor.reset(self._session_key)
        self._current_context = None

    def get_product_info(self, product_name: str) -> str:
        """获取产品信息"""
        if self._advisor:
            return self._advisor.get_product_info(product_name)
        return ""

    def get_policy_info(self, policy_key: str) -> str:
        """获取条款信息"""
        if self._advisor:
            return self._advisor.get_policy_info(policy_key)
        return ""

    def get_objection_response(self, objection_type: str, **kwargs) -> str:
        """获取异议处理话术"""
        if self._advisor:
            return self._advisor.get_objection_response(objection_type, kwargs)
        return ""


class SalesContextMixin:
    """
    销售上下文混入

    为 ContextBuilder 或其他地方提供销售上下文扩展
    """

    def __init__(self, hook: SalesAdvisorHook | None = None):
        self._hook = hook

    def attach_hook(self, hook: SalesAdvisorHook) -> None:
        """附加钩子"""
        self._hook = hook

    def get_sales_context_for_prompt(self) -> str:
        """
        获取要注入到 prompt 的销售上下文

        格式化为字符串，追加到 system prompt 末尾
        """
        if not self._hook or not self._hook._current_context:
            return ""

        ctx = self._hook._current_context
        parts = []

        # 当前阶段
        stage_name = self._hook.get_stage_progress()
        parts.append(f"[销售进度: {stage_name}]")

        # 客户信息
        customer = ctx.customer
        if customer.name or customer.age > 0:
            info = []
            if customer.name:
                info.append(f"客户: {customer.name}")
            if customer.age > 0:
                info.append(f"年龄: {customer.age}岁")
            if customer.budget:
                info.append(f"预算: {customer.budget}")
            if info:
                parts.append(" | ".join(info))

        # 最近讨论的产品
        if ctx.last_product_mentioned:
            parts.append(f"已推荐: {ctx.last_product_mentioned}")

        # 当前话题
        if ctx.current_topic:
            parts.append(f"话题: {ctx.current_topic}")

        if not parts:
            return ""

        return "\n\n[销售顾问上下文]\n" + "\n".join(parts)

    def should_inject_knowledge(self, message: str) -> bool:
        """
        判断是否应该注入知识库内容

        Args:
            message: 用户消息

        Returns:
            是否注入
        """
        keywords = ["条款", "保什么", "理赔", "赔付", "保费", "失能", "等待期", "犹豫期", "核保"]
        return any(kw in message for kw in keywords)

    def get_relevant_knowledge(self, message: str) -> str:
        """
        获取与当前消息相关的知识

        Args:
            message: 用户消息

        Returns:
            格式化的知识内容
        """
        if not self._hook or not self._hook.advisor:
            return ""

        knowledge_parts = []
        advisor = self._hook.advisor

        # 检查是否询问条款
        if any(kw in message for kw in ["条款", "保什么", "保障"]):
            product_info = advisor.get_product_info("安家守护")
            if product_info:
                knowledge_parts.append(product_info)

        # 检查是否询问理赔
        if any(kw in message for kw in ["理赔", "赔付", "怎么赔"]):
            policy_info = advisor.get_policy_info("理赔")
            if policy_info:
                knowledge_parts.append(policy_info)

        # 检查是否询问失能
        if "失能" in message:
            policy_info = advisor.get_policy_info("失能")
            if policy_info:
                knowledge_parts.append(policy_info)

        if not knowledge_parts:
            return ""

        return "\n\n[相关产品/条款知识]\n" + "\n---\n".join(knowledge_parts)
