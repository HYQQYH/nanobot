"""对话状态管理 - 管理销售对话中的所有状态信息"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# 销售阶段常量
class SalesStage:
    """销售阶段枚举"""
    OPENING = "opening"           # 开场破冰
    EMPATHY = "empathy"          # 共情客户
    NEEDS_DISCOVERY = "needs_discovery"  # 需求挖掘
    PRODUCT_INTRO = "product_intro"  # 产品介绍
    POLICY_DETAIL = "policy_detail"  # 条款解读
    OBJECTION = "objection_handling"  # 异议处理
    CLOSING = "closing"          # 促成交易
    AFTER_SALES = "after_sales"  # 售后确认
    COMPLETED = "completed"      # 交易完成

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
    def next_stage(cls, current: str) -> str | None:
        """获取下一阶段"""
        stages = cls.all_stages()
        try:
            idx = stages.index(current)
            if idx < len(stages) - 1:
                return stages[idx + 1]
        except ValueError:
            pass
        return None

    @classmethod
    def stage_order(cls) -> list[str]:
        """获取阶段的执行顺序（不含completed）"""
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
    def stage_index(cls, stage: str) -> int:
        """获取阶段的索引"""
        stages = cls.stage_order()
        try:
            return stages.index(stage)
        except ValueError:
            return 0


@dataclass
class CustomerProfile:
    """
    客户画像

    存储客户的所有相关信息
    """

    # 基本信息
    name: str = ""           # 客户昵称/称呼
    age: int = 0             # 年龄
    gender: str = ""         # 性别

    # 家庭状况
    family: str = ""         # 家庭状况描述
    has_children: bool = False  # 是否有孩子
    children_age: str = ""  # 孩子年龄
    has_mortgage: bool = False  # 是否有房贷
    mortgage_monthly: int = 0  # 月供金额

    # 财务状况
    income_annual: int = 0  # 年收入
    budget: str = ""        # 预算描述（如"年交6000以内"）

    # 担忧和需求
    concerns: list[str] = field(default_factory=list)  # 担忧点列表
    needs: list[str] = field(default_factory=list)  # 需求列表

    # 健康状况
    health: str = ""        # 健康状况描述
    has_pre_existing: bool = False  # 是否有既往症
    pre_existing_detail: str = ""  # 既往症详情

    # 保险认知
    has_insurance_knowledge: bool = False  # 是否有保险基础认知
    insurance_concerns: str = ""  # 对保险的顾虑

    # 沟通过程中收集的信息
    discussed_products: list[str] = field(default_factory=list)  # 讨论过的产品
    expressed_objections: list[str] = field(default_factory=list)  # 表达过的异议
    confirmed_needs: list[str] = field(default_factory=list)  # 确认过的需求

    def to_context(self) -> str:
        """
        转换为给LLM的上下文字符串

        用于在prompt中向小安提供客户信息
        """
        parts = []

        # 基本信息
        basic = []
        if self.name:
            basic.append(f"昵称: {self.name}")
        if self.age > 0:
            basic.append(f"年龄: {self.age}岁")
        if self.gender:
            basic.append(f"性别: {self.gender}")
        if basic:
            parts.append("、".join(basic))

        # 家庭状况
        if self.family:
            parts.append(f"家庭: {self.family}")
        if self.has_children and self.children_age:
            parts.append(f"孩子: {self.children_age}岁")
        if self.has_mortgage and self.mortgage_monthly > 0:
            parts.append(f"房贷: 月供{self.mortgage_monthly}元")

        # 财务
        if self.income_annual > 0:
            parts.append(f"年收入: {self.income_annual}元")
        if self.budget:
            parts.append(f"预算: {self.budget}")

        # 担忧
        if self.concerns:
            parts.append(f"担忧: {', '.join(self.concerns)}")

        # 健康
        if self.health:
            parts.append(f"健康: {self.health}")
        if self.pre_existing_detail:
            parts.append(f"既往症: {self.pre_existing_detail}")

        # 讨论过的
        if self.discussed_products:
            parts.append(f"已讨论产品: {', '.join(self.discussed_products)}")

        if not parts:
            return "新客户，暂无背景信息"

        return "； ".join(parts)

    def update_from_message(self, content: str, role: str) -> None:
        """
        从消息中提取并更新客户信息

        Args:
            content: 消息内容
            role: 角色 ("user" 或 "assistant")
        """
        content_lower = content.lower()

        # 从用户消息中提取
        if role == "user":
            # 基本信息提取（简化版，实际可用NER）
            if "老婆" in content or "丈夫" in content or "老公" in content:
                self.family = self.family or "已婚"
            if "孩子" in content or "女儿" in content or "儿子" in content:
                self.has_children = True
                if "2岁" in content or "两岁" in content:
                    self.children_age = "2"
            if "房贷" in content or "月供" in content:
                self.has_mortgage = True
                # 尝试提取金额
                import re
                match = re.search(r"(\d+)\s*万", content)
                if match:
                    self.mortgage_monthly = int(match.group(1)) * 10000 // 12
            if "预算" in content or "年交" in content:
                import re
                match = re.search(r"(\d+)\s*万", content)
                if match:
                    self.income_annual = int(match.group(1)) * 10000
                match = re.search(r"(\d+)\s*元", content)
                if match:
                    self.budget = f"年交{match.group(1)}元"
            if "担心" in content or "怕" in content or "万一" in content:
                self.concerns.append(content[:50])

        # 从助手消息中提取确认的信息
        elif role == "assistant":
            if "确认" in content or "太好了" in content:
                # 可以标记某些信息已被确认
                pass


@dataclass
class ConversationState:
    """
    对话状态

    包含客户信息和销售进度
    """

    session_key: str  # 会话标识

    # 客户信息
    customer: CustomerProfile = field(default_factory=CustomerProfile)

    # 销售进度
    current_stage: str = SalesStage.OPENING
    stage_history: list[str] = field(default_factory=list)  # 阶段历史
    stage_enter_time: str = ""  # 进入当前阶段的时间

    # 对话关键信息
    collected_key_info: dict[str, Any] = field(default_factory=dict)  # 收集的关键信息
    last_product_mentioned: str = ""  # 最近提到的产品
    current_topic: str = ""  # 当前话题

    # 元数据
    created_at: str = ""  # 创建时间
    updated_at: str = ""  # 更新时间
    turn_count: int = 0  # 对话轮次

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    def to_llm_context(self) -> str:
        """
        构建给LLM的上下文字符串

        用于在每次回答时向小安提供当前状态
        """
        parts = []

        # 客户信息
        parts.append(f"客户信息: {self.customer.to_context()}")

        # 当前阶段
        parts.append(f"当前阶段: {self._get_stage_name(self.current_stage)}")
        if self.stage_history:
            parts.append(f"销售进度: {' → '.join(self.stage_history)}")

        # 最近讨论的产品
        if self.last_product_mentioned:
            parts.append(f"最近推荐产品: {self.last_product_mentioned}")

        # 当前话题
        if self.current_topic:
            parts.append(f"当前话题: {self.current_topic}")

        return "\n".join(parts)

    def _get_stage_name(self, stage: str) -> str:
        """获取阶段的中文名称"""
        names = {
            SalesStage.OPENING: "开场破冰",
            SalesStage.EMPATHY: "共情客户",
            SalesStage.NEEDS_DISCOVERY: "需求挖掘",
            SalesStage.PRODUCT_INTRO: "产品介绍",
            SalesStage.POLICY_DETAIL: "条款解读",
            SalesStage.OBJECTION: "异议处理",
            SalesStage.CLOSING: "促成交易",
            SalesStage.AFTER_SALES: "售后确认",
            SalesStage.COMPLETED: "已完成",
        }
        return names.get(stage, stage)

    def advance_stage(self, new_stage: str) -> None:
        """
        推进到新阶段

        Args:
            new_stage: 新阶段
        """
        if new_stage != self.current_stage:
            if new_stage not in self.stage_history:
                self.stage_history.append(self.current_stage)
            self.current_stage = new_stage
            self.stage_enter_time = datetime.now().isoformat()
            self.updated_at = self.stage_enter_time

    def update_from_message(self, role: str, content: str) -> None:
        """
        从消息更新状态

        Args:
            role: 消息角色 ("user" 或 "assistant")
            content: 消息内容
        """
        self.turn_count += 1
        self.updated_at = datetime.now().isoformat()

        # 更新客户信息
        self.customer.update_from_message(content, role)

        # 更新当前话题
        self._update_current_topic(content, role)

    def _update_current_topic(self, content: str, role: str) -> None:
        """根据消息内容更新当前话题"""
        # 简化的话题判断
        if "条款" in content or "保什么" in content or "赔付" in content:
            self.current_topic = "条款咨询"
        elif "保费" in content or "价格" in content or "预算" in content:
            self.current_topic = "保费咨询"
        elif "购买" in content or "投保" in content or "下单" in content:
            self.current_topic = "购买意向"
        elif "理赔" in content or "怎么赔" in content:
            self.current_topic = "理赔咨询"

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "session_key": self.session_key,
            "customer": {
                "name": self.customer.name,
                "age": self.customer.age,
                "gender": self.customer.gender,
                "family": self.customer.family,
                "has_children": self.customer.has_children,
                "children_age": self.customer.children_age,
                "has_mortgage": self.customer.has_mortgage,
                "mortgage_monthly": self.customer.mortgage_monthly,
                "income_annual": self.customer.income_annual,
                "budget": self.customer.budget,
                "concerns": self.customer.concerns,
                "needs": self.customer.needs,
                "health": self.customer.health,
                "has_pre_existing": self.customer.has_pre_existing,
                "pre_existing_detail": self.customer.pre_existing_detail,
                "discussed_products": self.customer.discussed_products,
                "expressed_objections": self.customer.expressed_objections,
                "confirmed_needs": self.customer.confirmed_needs,
            },
            "current_stage": self.current_stage,
            "stage_history": self.stage_history,
            "stage_enter_time": self.stage_enter_time,
            "collected_key_info": self.collected_key_info,
            "last_product_mentioned": self.last_product_mentioned,
            "current_topic": self.current_topic,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "turn_count": self.turn_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationState":
        """从字典反序列化"""
        customer_data = data.get("customer", {})
        customer = CustomerProfile(
            name=customer_data.get("name", ""),
            age=customer_data.get("age", 0),
            gender=customer_data.get("gender", ""),
            family=customer_data.get("family", ""),
            has_children=customer_data.get("has_children", False),
            children_age=customer_data.get("children_age", ""),
            has_mortgage=customer_data.get("has_mortgage", False),
            mortgage_monthly=customer_data.get("mortgage_monthly", 0),
            income_annual=customer_data.get("income_annual", 0),
            budget=customer_data.get("budget", ""),
            concerns=customer_data.get("concerns", []),
            needs=customer_data.get("needs", []),
            health=customer_data.get("health", ""),
            has_pre_existing=customer_data.get("has_pre_existing", False),
            pre_existing_detail=customer_data.get("pre_existing_detail", ""),
            discussed_products=customer_data.get("discussed_products", []),
            expressed_objections=customer_data.get("expressed_objections", []),
            confirmed_needs=customer_data.get("confirmed_needs", []),
        )

        return cls(
            session_key=data.get("session_key", ""),
            customer=customer,
            current_stage=data.get("current_stage", SalesStage.OPENING),
            stage_history=data.get("stage_history", []),
            stage_enter_time=data.get("stage_enter_time", ""),
            collected_key_info=data.get("collected_key_info", {}),
            last_product_mentioned=data.get("last_product_mentioned", ""),
            current_topic=data.get("current_topic", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            turn_count=data.get("turn_count", 0),
        )


class StateManager:
    """
    状态管理器

    负责状态的读取、写入和持久化
    """

    # Session metadata中的key
    METADATA_KEY = "sales_state"

    def __init__(self, session: Any):
        """
        初始化状态管理器

        Args:
            session: Session对象
        """
        self.session = session

    def get_state(self) -> ConversationState | None:
        """
        从Session获取销售状态

        Returns:
            ConversationState或None
        """
        sales_state = self.session.metadata.get(self.METADATA_KEY)
        if sales_state:
            return ConversationState.from_dict(sales_state)
        return None

    def save_state(self, state: ConversationState) -> None:
        """
        保存销售状态到Session

        Args:
            state: ConversationState
        """
        self.session.metadata[self.METADATA_KEY] = state.to_dict()

    def get_or_create(self, session_key: str) -> ConversationState:
        """
        获取或创建状态

        Args:
            session_key: 会话标识

        Returns:
            ConversationState
        """
        existing = self.get_state()
        if existing:
            return existing

        new_state = ConversationState(session_key=session_key)
        self.save_state(new_state)
        return new_state

    def clear_state(self) -> None:
        """清除销售状态"""
        if self.METADATA_KEY in self.session.metadata:
            del self.session.metadata[self.METADATA_KEY]
