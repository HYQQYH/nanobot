# 小安虚拟保险顾问 (Sales Advisor)

小安是嵌入在 Nanobot 中的虚拟保险顾问模块，通过自然对话引导用户完成保险咨询、需求分析和产品推荐流程。

## 快速开始

### 1. 基本使用

```python
from nanobot.agent.sales_advisor import XiaoAnAdvisor

# 创建顾问实例
advisor = XiaoAnAdvisor()

# 获取系统提示词
system_prompt = advisor.get_system_prompt()

# 查询产品信息
product_info = advisor.get_product_info("安家守护")
print(product_info)
```

### 2. 集成到 Nanobot

```python
from nanobot import Nanobot
from nanobot.agent.sales_advisor import SalesAdvisorHook, SalesAdvisorHookConfig

# 创建钩子
config = SalesAdvisorHookConfig(enabled=True)
hook = SalesAdvisorHook(config=config)

# 附加到 Nanobot
bot = Nanobot.from_config()
result = await bot.run("我想了解保险", hooks=[hook])
```

### 3. 在 Hook 中使用顾问能力

```python
from nanobot.agent.sales_advisor import SalesAdvisorHook

hook = SalesAdvisorHook()

# 查询条款信息
policy_info = hook.get_policy_info("失能")

# 查询异议处理话术
response = hook.get_objection_response("太贵", premium="5500元", coverage="100万")

# 获取当前销售阶段
stage = hook.get_current_stage()
```

## 核心模块

### persona.py - 小安人设

定义小安的角色特征、说话风格和行为规则。

```python
from nanobot.agent.sales_advisor import XiaoAnPersona

persona = XiaoAnPersona()

# 获取系统提示词
prompt = persona.get_system_prompt()

# 获取阶段指导
guidance = persona.get_stage_guidance("opening")

# 验证回复是否符合人设
is_valid, msg = persona.validate_response("我理解您的担忧...")
```

**人设特点**：
- 名字：小安
- 角色：平安保险顾问
- 公司：明亚保险
- 个性：热情、专业、像朋友一样贴心

### state.py - 状态管理

管理对话状态和客户信息。

```python
from nanobot.agent.sales_advisor import ConversationState, CustomerProfile, StateManager

# 客户画像
customer = CustomerProfile()
customer.name = "阿哲"
customer.age = 32
customer.budget = "年交6000以内"

# 对话状态
state = ConversationState(session_key="test:123")
state.customer = customer
state.advance_stage("empathy")

# 状态序列化
state_dict = state.to_dict()
restored = ConversationState.from_dict(state_dict)
```

**客户画像字段**：
- 基本信息：name, age, gender
- 家庭状况：family, has_children, children_age, has_mortgage
- 财务状况：income_annual, budget
- 担忧和需求：concerns, needs
- 健康状况：health, has_pre_existing, pre_existing_detail
- 保险认知：has_insurance_knowledge, insurance_concerns

### flow.py - 销售流程管理

管理销售阶段的自动推进。

```python
from nanobot.agent.sales_advisor import SalesFlowManager

manager = SalesFlowManager()

# 检测用户消息对应的阶段
stage = manager.detect_stage_from_message("具体保什么？")

# 获取阶段定义
definition = manager.get_stage_definition("opening")
print(definition.name)  # "开场破冰"

# 获取阶段提示
prompt = manager.get_stage_prompt("opening")
```

**销售阶段**：
1. opening - 开场破冰
2. empathy - 共情客户
3. needs_discovery - 需求挖掘
4. product_intro - 产品介绍
5. policy_detail - 条款解读
6. objection_handling - 异议处理
7. closing - 促成交易
8. after_sales - 售后确认
9. completed - 交易完成

### capabilities.py - 能力模块

检测并调用合适的专业能力。

```python
from nanobot.agent.sales_advisor import CapabilityModule

cap = CapabilityModule()

# 检测需要的能力
capabilities = cap.detect_capabilities(
    "条款具体怎么赔付的",
    stage="policy_detail",
    context={}
)

for cap in capabilities:
    print(f"{cap.id}: {cap.name}")
```

**7种内部能力**：
- ice_breaking - 开场破冰
- needs_discovery - 需求挖掘
- product_explanation - 产品讲解
- policy_interpretation - 条款解读
- objection_handling - 异议处理
- closing - 促成交易
- empathy - 共情表达

### knowledge.py - 知识库

存储产品信息和条款数据。

```python
from nanobot.agent.sales_advisor import ProductKnowledge, PolicyDatabase, SalesKnowledge

# 产品知识
pk = ProductKnowledge()
product = pk.get_product("安家守护")
intro = pk.format_product_intro(product)

# 条款数据库
pd = PolicyDatabase()
policy = pd.get_policy("失能")
formatted = pd.format_policy(policy)

# 异议处理话术
sk = SalesKnowledge()
response = sk.get_objection_response("太贵", {
    "premium": "5500元",
    "coverage": "100万"
})
```

**产品信息**：
- 安家守护综合保障计划
  - 适用人群：30-45岁家庭顶梁柱
  - 保障内容：120种重疾、50种轻症、意外身故/伤残、疾病身故等
  - 特色功能：保费豁免、失能补偿、就医绿通等

**条款信息**：
- 失能定义 - 以《人身保险伤残评定标准》为准
- 理赔流程 - 确诊报案 → 提交资料 → 审核 → 到账
- 等待期 - 90天
- 犹豫期 - 20天
- 保费豁免 - 患轻症/重疾免交剩余保费
- 核保 - 脂肪肝分程度处理

### advisor.py - 顾问主入口

整合所有模块的完整顾问接口。

```python
from nanobot.agent.sales_advisor import XiaoAnAdvisor, SalesContext, AdvisorConfig

# 创建顾问
config = AdvisorConfig(
    use_llm_stage_detection=False,
    min_stage_advance_turns=2,
)
advisor = XiaoAnAdvisor(config=config)

# 处理对话
result = await advisor.chat(
    user_message="我想给家人买保险",
    history=[],
    session_key="feishu:user123"
)

print(result["response"])
print(f"阶段变化: {result['stage_changed']}")
print(f"新阶段: {result['new_stage']}")

# 导出上下文
exported = advisor.export_context(result["context"])
```

### hook.py - Nanobot 集成

通过 AgentHook 接口集成到 Nanobot。

```python
from nanobot.agent.sales_advisor import SalesAdvisorHook, SalesAdvisorHookConfig

# 创建钩子配置
config = SalesAdvisorHookConfig(
    enabled=True,
    use_llm_stage_detection=False,
    min_stage_advance_turns=2,
    inject_sales_context=True,
    inject_product_knowledge=True,
)

# 创建钩子
hook = SalesAdvisorHook(config=config)

# 附加会话
hook.set_session(session)

# 获取销售进度
progress = hook.get_stage_progress()
print(f"当前进度: {progress}")

# 重置状态
hook.reset_sales_state()
```

## 销售上下文注入

小安支持在对话中自动注入销售上下文，让小安了解当前销售进度和客户信息。

### 自动注入的内容

1. **当前阶段**：开场破冰、共情客户、需求挖掘等
2. **客户信息**：姓名、年龄、预算、家庭状况等
3. **销售进度**：已完成阶段、当前阶段
4. **产品知识**：根据用户问题自动关联
5. **条款信息**：根据用户问题自动关联

### 注入方式

```python
from nanobot.agent.sales_advisor import SalesContextMixin

mixin = SalesContextMixin(hook=sales_hook)

# 获取要注入到 prompt 的上下文
sales_ctx = mixin.get_sales_context_for_prompt()

# 获取相关知识
knowledge = mixin.get_relevant_knowledge("失能是什么意思？")
```

## 阶段推进规则

小安的销售流程按以下规则自动推进：

1. **关键词检测**：根据用户消息中的关键词判断是否进入下一阶段
2. **轮次限制**：每个阶段至少需要 `min_stage_advance_turns` 轮对话才能推进
3. **阶段可回退**：如果用户讨论之前阶段的话题，可能回退到之前阶段

### 关键词示例

| 阶段 | 触发关键词 |
|------|-----------|
| 开场破冰 | 你好、在吗、咨询、怕被坑 |
| 共情客户 | 家庭、老婆、孩子、房贷、万一 |
| 需求挖掘 | 算账、风险、缺口、收入 |
| 产品介绍 | 推荐、产品、安家守护、保什么 |
| 条款解读 | 条款、失能、赔付、理赔 |
| 异议处理 | 太贵、通胀、理赔麻烦 |
| 促成交易 | 价格、确认、下单、购买 |
| 售后确认 | 受益人、生效、谢谢 |

## 单元测试

```bash
# 运行所有测试
pytest tests/agent/test_sales_advisor.py -v

# 运行特定测试类
pytest tests/agent/test_sales_advisor.py::TestXiaoAnAdvisor -v

# 查看测试覆盖
pytest tests/agent/test_sales_advisor.py --cov=nanobot.agent.sales_advisor
```

## 文件结构

```
nanobot/agent/sales_advisor/
├── __init__.py          # 模块导出
├── persona.py           # 小安人设定义 (200行)
├── state.py            # 对话状态管理 (462行)
├── flow.py             # 销售流程管理 (347行)
├── capabilities.py     # 能力模块 (252行)
├── knowledge.py        # 知识库 (365行)
├── advisor.py          # 顾问主入口 (445行)
└── hook.py             # Nanobot集成 (281行)

tests/agent/
└── test_sales_advisor.py  # 单元测试 (588行)
```

## 使用示例

### 完整对话流程

```python
from nanobot.agent.sales_advisor import XiaoAnAdvisor

advisor = XiaoAnAdvisor()

# 模拟对话
messages = []

# 用户开场
user_msg = "你好，我想了解下保险，怕被坑"
result = await advisor.chat(user_msg, messages, "test:123")
messages.append({"role": "user", "content": user_msg})
messages.append({"role": "assistant", "content": result["response"]})

# 小安开场破冰后，用户表达担忧
user_msg = "我已婚有孩子，有房贷"
result = await advisor.chat(user_msg, messages, "test:123")
messages.append({"role": "user", "content": user_msg})
messages.append({"role": "assistant", "content": result["response"]})

# 用户询问产品
user_msg = "有什么适合我的产品吗？"
result = await advisor.chat(user_msg, messages, "test:123")
```

### 查询产品信息

```python
advisor = XiaoAnAdvisor()

# 获取安家守护产品介绍
info = advisor.get_product_info("安家守护")
print(info)

# 获取条款信息
policy = advisor.get_policy_info("失能")
print(policy)

# 获取异议处理
response = advisor.get_objection_response("太贵", {
    "premium": "5500元/年",
    "coverage": "100万"
})
print(response)
```

### 导出销售数据

```python
advisor = XiaoAnAdvisor()
result = await advisor.chat("我想买保险", [], "test:123")

# 导出上下文用于分析
data = advisor.export_context(result["context"])
print(f"客户: {data['customer']['name']}")
print(f"阶段: {data['stage_progress']}")
print(f"已讨论产品: {data['customer']['discussed_products']}")
```
