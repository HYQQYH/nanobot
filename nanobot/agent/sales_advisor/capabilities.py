"""能力模块 - 小安的内部能力（用户无感知）"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nanobot.providers.base import LLMProvider


@dataclass
class Capability:
    """能力定义"""
    id: str
    name: str
    description: str
    trigger_keywords: list[str]  # 触发该能力的关键词
    stage_affinity: list[str]  # 关联的销售阶段


@dataclass
class CapabilityModule:
    """
    能力模块

    内部包含多种能力，用于回答不同类型的问题
    用户无感知，小安在回答时会自然整合这些能力
    """

    llm: Any = field(default=None)

    # 能力定义
    capabilities: list[Capability] = field(default_factory=list)

    def __post_init__(self):
        if not self.capabilities:
            self._init_capabilities()

    def _init_capabilities(self) -> None:
        """初始化能力列表"""
        self.capabilities = [
            Capability(
                id="ice_breaking",
                name="开场破冰",
                description="建立信任，消除顾虑",
                trigger_keywords=["你好", "在吗", "怕被坑", "水太深", "担心"],
                stage_affinity=["opening", "empathy"],
            ),
            Capability(
                id="needs_discovery",
                name="需求挖掘",
                description="通过提问了解客户需求",
                trigger_keywords=["担心", "家庭", "收入", "房贷", "孩子"],
                stage_affinity=["empathy", "needs_discovery"],
            ),
            Capability(
                id="product_explanation",
                name="产品讲解",
                description="介绍产品特点和优势",
                trigger_keywords=["产品", "推荐", "保什么", "保障", "安家守护"],
                stage_affinity=["product_intro", "policy_detail"],
            ),
            Capability(
                id="policy_interpretation",
                name="条款解读",
                description="解释保险条款和细则",
                trigger_keywords=["条款", "失能", "赔付", "保额", "理赔", "免责", "保费"],
                stage_affinity=["policy_detail", "objection_handling"],
            ),
            Capability(
                id="objection_handling",
                name="异议处理",
                description="处理客户质疑和顾虑",
                trigger_keywords=["太贵", "通胀", "理赔麻烦", "听说", "但是", "不信任"],
                stage_affinity=["objection_handling", "closing"],
            ),
            Capability(
                id="closing",
                name="促成交易",
                description="推动客户做决定",
                trigger_keywords=["价格", "确认", "下单", "购买", "投保", "附加"],
                stage_affinity=["closing", "after_sales"],
            ),
            Capability(
                id="empathy",
                name="共情表达",
                description="表达理解和关心",
                trigger_keywords=["理解", "明白", "确实", "我懂"],
                stage_affinity=["empathy", "objection_handling"],
            ),
        ]

    def detect_capabilities(
        self,
        user_message: str,
        stage: str,
        context: dict[str, Any],
    ) -> list[Capability]:
        """
        检测需要的能力

        Args:
            user_message: 用户消息
            stage: 当前销售阶段
            context: 上下文信息

        Returns:
            需要的能力列表（按相关性排序）
        """
        content = user_message.lower()
        scored = []

        for cap in self.capabilities:
            score = 0

            # 关键词匹配
            for keyword in cap.trigger_keywords:
                if keyword in content:
                    score += 2

            # 阶段关联
            if stage in cap.stage_affinity:
                score += 1

            if score > 0:
                scored.append((score, cap))

        # 按分数排序
        scored.sort(key=lambda x: x[0], reverse=True)
        return [cap for _, cap in scored]

    async def process(
        self,
        user_message: str,
        stage: str,
        context: dict[str, Any],
        history: list[dict[str, Any]],
    ) -> str:
        """
        处理用户消息 - 整合多能力生成回答

        这个方法通过prompt让小安自然地调用各种能力

        Args:
            user_message: 用户消息
            stage: 当前阶段
            context: 上下文
            history: 对话历史

        Returns:
            小安的回答
        """
        if not self.llm:
            return "小安暂时无法回答，请稍后再试。"

        # 检测相关能力
        capabilities = self.detect_capabilities(user_message, stage, context)
        capability_names = [c.name for c in capabilities[:3]]  # 最多3个

        # 构建prompt
        prompt = self._build_prompt(user_message, stage, context, history, capability_names)

        # 调用LLM
        response = await self.llm.chat(prompt)

        return response

    def _build_prompt(
        self,
        user_message: str,
        stage: str,
        context: dict[str, Any],
        history: list[dict[str, Any]],
        capability_names: list[str],
    ) -> list[dict[str, str]]:
        """
        构建给LLM的prompt

        Args:
            user_message: 用户消息
            stage: 当前阶段
            context: 上下文
            history: 对话历史
            capability_names: 检测到的能力名称

        Returns:
            消息列表
        """
        # 获取客户信息
        customer_info = context.get("customer_context", "新客户")
        stage_progress = context.get("stage_progress", "")

        capability_hint = ""
        if capability_names:
            capability_hint = f"（当前可用的专业知识：{'、'.join(capability_names)}）"

        system_prompt = f"""你是小安，一个专业、热情、有经验的保险顾问。

当前销售阶段: {stage}
{capability_hint}
客户信息: {customer_info}
销售进度: {stage_progress}

你的任务：
1. 根据客户的问题，以小安的身份自然回答
2. 灵活运用你的专业知识（产品知识、条款知识、销售技巧）
3. 记住客户之前告诉你的信息，自然地使用
4. 永远保持"小安"这个角色，像一个真实的销售顾问

重要规则：
- 使用第一人称"我"回答
- 不要提及你是AI或机器人
- 不要突然切换人格
- 回答要自然流畅，不要像在背诵

客户现在说: "{user_message}"

请以小安的身份回答："""

        messages = [{"role": "system", "content": system_prompt}]

        # 添加最近的历史（最近3轮）
        if history:
            for msg in history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        return messages

    def get_capability_hint(self, capability_id: str) -> str:
        """
        获取能力的提示信息

        Args:
            capability_id: 能力ID

        Returns:
            能力提示
        """
        hints = {
            "ice_breaking": "开场时先建立信任，不要急于介绍产品",
            "needs_discovery": "通过提问了解客户需求，不要主观臆断",
            "product_explanation": "根据客户需求介绍产品，不要死板背诵产品资料",
            "policy_interpretation": "用通俗语言解释条款，可以举例说明",
            "objection_handling": "先认可客户顾虑，再用数据和案例回应",
            "closing": "适时促成，给客户台阶下，不强迫",
            "empathy": "真诚表达理解和关心，不要敷衍",
        }
        return hints.get(capability_id, "")
