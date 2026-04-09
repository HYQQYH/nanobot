"""知识库 - 产品信息和条款数据"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Product:
    """产品信息"""
    id: str
    name: str
    target_audience: str  # 目标人群
    coverage: list[str]  # 保障内容
    premium_example: str  # 保费示例
    features: list[str]  # 特色功能
    min_coverage: int = 50  # 最低保额（万）
    max_coverage: int = 200  # 最高保额（万）


@dataclass
class PolicyDetail:
    """条款详情"""
    key: str  # 条款关键词
    title: str  # 条款标题
    content: str  # 条款内容
    example: str = ""  # 示例说明


@dataclass
class ProductKnowledge:
    """
    产品知识库

    存储和管理保险产品信息
    """

    products: dict[str, Product] = field(default_factory=dict)
    _initialized: bool = field(default=False, repr=False)

    def __post_init__(self):
        if not self._initialized:
            self._init_products()
            self._initialized = True

    def _init_products(self) -> None:
        """初始化产品数据"""
        # 安家守护综合保障计划
        self.products["安家守护"] = Product(
            id="anjia",
            name="安家守护综合保障计划",
            target_audience="30-45岁家庭顶梁柱",
            coverage=[
                "120种重疾（含轻症/中奖多次赔付）",
                "50种轻症（最高赔3次）",
                "意外身故/伤残",
                "疾病身故",
                "家庭责任专项金（失能收入补偿）",
            ],
            premium_example="30岁男性，保额100万，20年交，年交约5500元",
            features=[
                "保费豁免：患轻症/中奖/重疾免交剩余保费",
                "失能补偿：每年额外给付20%保额（最多5年）",
                "就医绿通：三甲医院专家门诊/手术安排",
                "住院费用垫付",
                "术后康复指导",
            ],
            min_coverage=50,
            max_coverage=200,
        )

    def get_product(self, name: str) -> Product | None:
        """
        获取产品信息

        Args:
            name: 产品名称

        Returns:
            Product或None
        """
        # 模糊匹配
        for key, product in self.products.items():
            if key in name or name in key:
                return product
            if key in name.replace("守护", ""):
                return product
        return None

    def get_all_products(self) -> list[Product]:
        """获取所有产品"""
        return list(self.products.values())

    def match_products(self, needs: dict[str, Any]) -> list[Product]:
        """
        根据需求匹配产品

        Args:
            needs: 需求字典，包含：
                - age: 年龄
                - family: 家庭状况
                - concerns: 担忧
                - budget: 预算

        Returns:
            匹配的产品列表
        """
        matched = []
        age = needs.get("age", 0)
        budget_str = needs.get("budget", "")

        for product in self.products.values():
            # 年龄匹配
            if "30-45" in product.target_audience:
                if 30 <= age <= 45:
                    matched.append(product)
                elif age == 0:  # 未知年龄，默认推荐
                    matched.append(product)

        return matched

    def format_product_intro(self, product: Product) -> str:
        """
        格式化产品介绍

        Args:
            product: 产品

        Returns:
            格式化后的产品介绍
        """
        parts = [f"【{product.name}】"]
        parts.append(f"适用人群：{product.target_audience}")
        parts.append("")
        parts.append("保障内容：")
        for i, c in enumerate(product.coverage, 1):
            parts.append(f"  {i}. {c}")

        parts.append("")
        parts.append("特色功能：")
        for f in product.features:
            parts.append(f"  - {f}")

        parts.append("")
        parts.append(f"保费示例：{product.premium_example}")

        return "\n".join(parts)

    def get_product_summary(self, product: Product) -> str:
        """
        获取产品摘要

        Args:
            product: 产品

        Returns:
            简短的产品摘要
        """
        return f"{product.name}（{product.target_audience}），{product.premium_example}"


@dataclass
class PolicyDatabase:
    """
    条款数据库

    存储和管理保险条款信息
    """

    policies: dict[str, PolicyDetail] = field(default_factory=dict)
    _initialized: bool = field(default=False, repr=False)

    def __post_init__(self):
        if not self._initialized:
            self._init_policies()
            self._initialized = True

    def _init_policies(self) -> None:
        """初始化条款数据"""
        # 失能定义
        self.policies["失能"] = PolicyDetail(
            key="失能",
            title="失能定义",
            content="以《人身保险伤残评定标准》为准，由二级以上医院出具诊断证明，如\"双目失明\"\"肢体缺失\"等明确状态，不存在主观判断。",
            example="上周刚有位客户因车祸导致瘫痪，提交资料后7天就收到了首笔20万补偿金。",
        )

        # 理赔流程
        self.policies["理赔"] = PolicyDetail(
            key="理赔",
            title="理赔流程",
            content="1. 确诊后打客服电话报案\n2. 提交诊断证明/发票\n3. 保险公司审核\n4. 赔款到账",
            example="去年理赔率98.7%，平均理赔时效1.8天。",
        )

        # 等待期
        self.policies["等待期"] = PolicyDetail(
            key="等待期",
            title="等待期",
            content="90天（行业最短之一）",
            example="今天投保，明天零时生效，等待期90天。",
        )

        # 犹豫期
        self.policies["犹豫期"] = PolicyDetail(
            key="犹豫期",
            title="犹豫期",
            content="20天",
            example="犹豫期20天内觉得不合适随时退全款，零风险尝试。",
        )

        # 保费豁免
        self.policies["保费豁免"] = PolicyDetail(
            key="保费豁免",
            title="保费豁免",
            content="被保人患轻症/中奖/重疾，或投保人（配偶）身故/全残，免交剩余保费，保障继续有效。",
            example="上个月一位客户确诊甲状腺癌（轻症），提交资料后3天就收到30万，同时豁免了剩余18年保费（约9.9万），保障继续有效。",
        )

        # 核保
        self.policies["核保"] = PolicyDetail(
            key="核保",
            title="健康告知与核保",
            content="脂肪肝要看程度：\n- 轻度（肝功能正常）：大概率标准体承保\n- 中度：可能需要加费500-800元/年\n- 重度：可能除外肝脏相关责任",
            example="轻度脂肪肝+肝功正常，99%概率标准体承保。",
        )

        # 身故赔付
        self.policies["身故"] = PolicyDetail(
            key="身故",
            title="身故/全残赔付",
            content="无论疾病还是意外导致身故/全残，直接赔付保额给家人。",
            example="100万保额，身故直接赔100万给家人。",
        )

        # 少儿特疾
        self.policies["少儿特疾"] = PolicyDetail(
            key="少儿特疾",
            title="少儿特疾额外赔",
            content="活动期间可免费附加，若孩子患白血病等少儿特定疾病，额外赔付50万。",
            example="相当于给全家都加了层防护。",
        )

    def get_policy(self, key: str) -> PolicyDetail | None:
        """
        获取条款详情

        Args:
            key: 条款关键词

        Returns:
            PolicyDetail或None
        """
        # 模糊匹配
        for k, policy in self.policies.items():
            if k in key or key in k:
                return policy
        return None

    def search_policies(self, query: str) -> list[PolicyDetail]:
        """
        搜索条款

        Args:
            query: 查询关键词

        Returns:
            匹配的条款列表
        """
        query_lower = query.lower()
        results = []

        for policy in self.policies.values():
            if (query_lower in policy.key.lower() or
                query_lower in policy.title.lower() or
                query_lower in policy.content.lower()):
                results.append(policy)

        return results

    def format_policy(self, policy: PolicyDetail, include_example: bool = True) -> str:
        """
        格式化条款

        Args:
            policy: 条款
            include_example: 是否包含示例

        Returns:
            格式化后的条款
        """
        parts = [f"【{policy.title}】"]
        parts.append(policy.content)

        if include_example and policy.example:
            parts.append("")
            parts.append(f"比如：{policy.example}")

        return "\n".join(parts)


@dataclass
class SalesKnowledge:
    """
    销售知识库

    整合产品和条款知识
    """

    products: ProductKnowledge = field(default_factory=ProductKnowledge)
    policies: PolicyDatabase = field(default_factory=PolicyDatabase)

    # 异议处理话术
    objection_responses: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self._init_objection_responses()

    def _init_objection_responses(self) -> None:
        """初始化异议处理话术"""
        self.objection_responses = {
            "太贵": "您说得对，价格确实需要考虑。不过从保障角度看，{premium}的保费换来{coverage}的保障，杠杆效应很高。而且保费是20年交的，平均到每个月也就几百块钱。",
            "通胀": "这是个好问题！通胀确实存在，但保险的杠杆效应是关键：{age}岁年交{premium}元，一旦{age2}岁出险，能立刻拿到{coverage}，杠杆很高。而且您可以每5年检视一次保单，收入提高了再加保。",
            "理赔麻烦": "这是我们最重视的环节！{claim_rate}，{claim_speed}。流程很简单：确诊后打客服电话报案→提交诊断证明/发票→保险公司审核→赔款到账。",
            "怕被坑": "特别理解您的担心！很多客户一开始都觉得保险条款像天书，其实核心是用确定的小钱，转移不确定的大风险。我会帮您把条款都讲清楚。",
            "条款复杂": "条款确实比较专业，这也是为什么需要一个专业的顾问来帮您解读。我会用大白话帮您把每一条都讲清楚。",
        }

    def get_objection_response(self, objection: str, context: dict[str, Any]) -> str:
        """
        获取异议处理话术

        Args:
            objection: 异议类型
            context: 上下文信息

        Returns:
            处理话术
        """
        template = self.objection_responses.get(objection, "")
        if not template:
            return ""

        try:
            return template.format(**context)
        except KeyError:
            return template

    def get_relevant_knowledge(self, query: str) -> list[str]:
        """
        获取与查询相关的知识

        Args:
            query: 查询

        Returns:
            知识列表
        """
        results = []

        # 搜索条款
        policies = self.policies.search_policies(query)
        for p in policies:
            results.append(self.policies.format_policy(p))

        return results
