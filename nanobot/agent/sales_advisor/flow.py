"""销售流程管理器 - 管理销售阶段的自动推进"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nanobot.providers.base import LLMProvider


# 销售阶段定义
@dataclass
class StageDefinition:
    """阶段定义"""
    id: str
    name: str
    description: str
    goals: list[str]
    keywords: list[str]
    next_stage_hints: list[str]


class SalesStage:
    """销售阶段枚举"""
    OPENING = "opening"
    EMPATHY = "empathy"
    NEEDS_DISCOVERY = "needs_discovery"
    PRODUCT_INTRO = "product_intro"
    POLICY_DETAIL = "policy_detail"
    OBJECTION = "objection_handling"
    CLOSING = "closing"
    AFTER_SALES = "after_sales"
    COMPLETED = "completed"

    @classmethod
    def all_stages(cls) -> list[str]:
        return [
            cls.OPENING,
            cls.EMPATHY,
            cls.NEEDS_DISCOVERY,
            cls.PRODUCT_INTRO,
            cls.POLICY_DETAIL,
            cls.OBJECTION,
            cls.CLOSING,
            cls.AFTER_SALES,
            cls.COMPLETED,
        ]

    @classmethod
    def stage_order(cls) -> list[str]:
        return [
            cls.OPENING,
            cls.EMPATHY,
            cls.NEEDS_DISCOVERY,
            cls.PRODUCT_INTRO,
            cls.POLICY_DETAIL,
            cls.OBJECTION,
            cls.CLOSING,
            cls.AFTER_SALES,
        ]

    @classmethod
    def next_stage(cls, current: str) -> str | None:
        stages = cls.stage_order()
        try:
            idx = stages.index(current)
            if idx < len(stages) - 1:
                return stages[idx + 1]
        except ValueError:
            pass
        return None

    @classmethod
    def stage_index(cls, stage: str) -> int:
        stages = cls.stage_order()
        try:
            return stages.index(stage)
        except ValueError:
            return 0


STAGE_DEFINITIONS: dict[str, StageDefinition] = {
    SalesStage.OPENING: StageDefinition(
        id=SalesStage.OPENING,
        name="开场破冰",
        description="建立专业信任，消除客户防备心理",
        goals=["友好问候", "表明身份和来意", "建立信任"],
        keywords=["你好", "在吗", "咨询", "了解", "怕被坑", "水太深"],
        next_stage_hints=["担忧", "担心", "怕", "家庭", "责任"],
    ),
    SalesStage.EMPATHY: StageDefinition(
        id=SalesStage.EMPATHY,
        name="共情客户",
        description="理解客户担忧，引导需求表达",
        goals=["共情", "引导客户说出担忧", "收集家庭信息"],
        keywords=["家庭", "老婆", "老公", "孩子", "房贷", "收入", "万一"],
        next_stage_hints=["算账", "风险", "缺口", "怎么", "哪个靠谱"],
    ),
    SalesStage.NEEDS_DISCOVERY: StageDefinition(
        id=SalesStage.NEEDS_DISCOVERY,
        name="需求挖掘",
        description="量化风险场景，强化需求紧迫性",
        goals=["了解收入", "量化风险", "强化紧迫感"],
        keywords=["算账", "风险", "缺口", "万", "收入", "花费"],
        next_stage_hints=["推荐", "产品", "哪个好", "靠谱", "怎么选"],
    ),
    SalesStage.PRODUCT_INTRO: StageDefinition(
        id=SalesStage.PRODUCT_INTRO,
        name="产品介绍",
        description="根据需求推荐产品",
        goals=["匹配需求", "介绍卖点", "差异化优势"],
        keywords=["推荐", "产品", "安家守护", "具体保什么"],
        next_stage_hints=["条款", "保什么", "赔付", "怎么赔", "保额"],
    ),
    SalesStage.POLICY_DETAIL: StageDefinition(
        id=SalesStage.POLICY_DETAIL,
        name="条款解读",
        description="详解保险条款，解答疑惑",
        goals=["解释条款", "用案例说明", "消除疑虑"],
        keywords=["条款", "失能", "界定", "赔付", "保费", "保额", "理赔", "脂肪肝"],
        next_stage_hints=["价格", "预算", "决定", "下单", "购买", "太贵"],
    ),
    SalesStage.OBJECTION: StageDefinition(
        id=SalesStage.OBJECTION,
        name="异议处理",
        description="处理客户质疑和顾虑",
        goals=["回应担忧", "用数据", "用案例"],
        keywords=["通胀", "太贵", "理赔", "麻烦", "担心", "怕", "听说"],
        next_stage_hints=["可以", "行", "好的", "价格", "确认", "下单"],
    ),
    SalesStage.CLOSING: StageDefinition(
        id=SalesStage.CLOSING,
        name="促成交易",
        description="推动客户做决定",
        goals=["限时优惠", "推动决定", "处理临门一脚"],
        keywords=["价格", "确认", "下单", "购买", "投保", "附加", "生效"],
        next_stage_hints=["好的", "行", "办", "受益人", "辛苦", "谢谢"],
    ),
    SalesStage.AFTER_SALES: StageDefinition(
        id=SalesStage.AFTER_SALES,
        name="售后确认",
        description="确认细节，完成成交",
        goals=["确认受益人", "说明生效", "服务承诺"],
        keywords=["受益人", "生效", "后续", "问题", "谢谢", "辛苦"],
        next_stage_hints=[],
    ),
}


@dataclass
class StageTransition:
    """阶段转换记录"""
    from_stage: str
    to_stage: str
    trigger: str
    user_message: str
    agent_response: str


@dataclass
class SalesFlowManager:
    """
    销售流程管理器
    """

    llm: Any = field(default=None)
    current_stage: str = SalesStage.OPENING
    stage_history: list[StageTransition] = field(default_factory=list)
    _llm_class: Any = field(default=None, repr=False)

    @property
    def provider(self):
        return self.llm

    def get_stage_definition(self, stage: str) -> StageDefinition | None:
        return STAGE_DEFINITIONS.get(stage)

    def get_stage_name(self, stage: str) -> str:
        definition = self.get_stage_definition(stage)
        if definition:
            return definition.name
        return stage

    def detect_stage_from_message(self, user_message: str, agent_response: str = "") -> str | None:
        content = (user_message + " " + agent_response).lower()

        stages = SalesStage.stage_order()
        for stage in stages:
            if stage == self.current_stage:
                continue

            definition = self.get_stage_definition(stage)
            if not definition:
                continue

            for keyword in definition.keywords:
                if keyword in content:
                    return stage

        return None

    async def analyze_and_advance(
        self,
        user_message: str,
        agent_response: str,
        current_stage: str,
        use_llm: bool = True,
    ) -> tuple[str, str, str]:
        self.current_stage = current_stage

        detected_stage = self.detect_stage_from_message(user_message, agent_response)

        if detected_stage and detected_stage != current_stage:
            reason = f"detected {detected_stage}"
            hints = self._get_stage_hints(detected_stage)
            self._record_transition(current_stage, detected_stage, reason, user_message, agent_response)
            return detected_stage, hints, reason

        if use_llm and self.llm:
            return await self._llm_analyze(user_message, agent_response, current_stage)

        return current_stage, "", "no signal"

    async def _llm_analyze(
        self,
        user_message: str,
        agent_response: str,
        current_stage: str,
    ) -> tuple[str, str, str]:
        prompt = f"""Analyze this insurance sales conversation and determine if we should advance to a new stage.

Current stage: {self.get_stage_name(current_stage)}
Stages: opening -> empathy -> needs_discovery -> product_intro -> policy_detail -> objection -> closing -> after_sales

User said: "{user_message}"
XiaoAn replied: "{agent_response[:200] if agent_response else 'first turn'}..."

Respond with JSON: {{"new_stage": "stage or current", "reason": "why", "hints": "optional advice"}}
"""

        try:
            response = await self.llm.chat([{"role": "user", "content": prompt}])
            import json, re
            match = re.search(r"\{[^}]+\}", response, re.DOTALL)
            if match:
                result = json.loads(match.group())
                new_stage = result.get("new_stage", current_stage)
                reason = result.get("reason", "")
                hints = result.get("hints", "")

                if new_stage not in SalesStage.all_stages():
                    new_stage = current_stage

                if new_stage != current_stage:
                    self._record_transition(current_stage, new_stage, reason, user_message, agent_response)

                return new_stage, hints, reason
        except Exception:
            pass

        return current_stage, "", "llm failed"

    def _record_transition(
        self,
        from_stage: str,
        to_stage: str,
        reason: str,
        user_message: str,
        agent_response: str,
    ) -> None:
        transition = StageTransition(
            from_stage=from_stage,
            to_stage=to_stage,
            trigger=reason,
            user_message=user_message[:100],
            agent_response=agent_response[:100] if agent_response else "",
        )
        self.stage_history.append(transition)

    def _get_stage_hints(self, stage: str) -> str:
        hints = {
            SalesStage.OPENING: "customer may have concerns",
            SalesStage.EMPATHY: "customer starting to share concerns",
            SalesStage.NEEDS_DISCOVERY: "quantify risk for customer",
            SalesStage.PRODUCT_INTRO: "ready to introduce product",
            SalesStage.POLICY_DETAIL: "customer asking about details",
            SalesStage.OBJECTION: "customer has objections",
            SalesStage.CLOSING: "customer ready to decide",
            SalesStage.AFTER_SALES: "deal completed",
        }
        return hints.get(stage, "")

    def get_stage_prompt(self, stage: str) -> str:
        definition = self.get_stage_definition(stage)
        if not definition:
            return ""

        goals_text = "\n".join([f"- {g}" for g in definition.goals])
        hints = self._get_stage_hints(stage)

        lines = [
            f"[Current Stage: {definition.name}]",
            f"Goal: {definition.description}",
            f"Objectives: {goals_text}",
            f"Hint: {hints}",
            "",
            "Answer as XiaoAn naturally.",
        ]
        return "\n".join(lines)

    def get_next_stage_prompt(self, from_stage: str, to_stage: str) -> str:
        transitions = {
            (SalesStage.OPENING, SalesStage.EMPATHY): "transition to empathy",
            (SalesStage.EMPATHY, SalesStage.NEEDS_DISCOVERY): "guide through calculation",
            (SalesStage.NEEDS_DISCOVERY, SalesStage.PRODUCT_INTRO): "introduce product",
            (SalesStage.PRODUCT_INTRO, SalesStage.POLICY_DETAIL): "detail policy",
            (SalesStage.POLICY_DETAIL, SalesStage.OBJECTION): "handle objections",
            (SalesStage.OBJECTION, SalesStage.CLOSING): "close deal",
            (SalesStage.CLOSING, SalesStage.AFTER_SALES): "confirm details",
        }
        key = (from_stage, to_stage)
        return transitions.get(key, "")

    def should_force_stage(self, user_message: str) -> str | None:
        content = user_message.lower()

        if "我要购买" in content or "我要投保" in content or "我决定了" in content:
            return SalesStage.CLOSING
        if "具体条款" in content or "详细说说" in content:
            return SalesStage.POLICY_DETAIL
        if "有没有别的" in content or "换产品" in content:
            return SalesStage.PRODUCT_INTRO

        return None

    def get_progress_summary(self) -> str:
        if not self.stage_history:
            return "just started"

        parts = []
        for t in self.stage_history[-3:]:
            parts.append(f"{self.get_stage_name(t.from_stage)} -> {self.get_stage_name(t.to_stage)}")

        return " -> ".join(parts) if parts else "just started"

    def reset(self) -> None:
        self.current_stage = SalesStage.OPENING
        self.stage_history.clear()
