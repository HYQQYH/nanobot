"""Tests for sales_advisor module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# =============================================================================
# persona.py tests
# =============================================================================

class TestXiaoAnPersona:
    """Tests for XiaoAnPersona."""

    def test_persona_creation(self):
        from nanobot.agent.sales_advisor.persona import XiaoAnPersona

        persona = XiaoAnPersona()
        assert persona.name == "小安"
        assert persona.role == "平安保险顾问"

    def test_get_system_prompt(self):
        from nanobot.agent.sales_advisor.persona import XiaoAnPersona

        persona = XiaoAnPersona()
        prompt = persona.get_system_prompt()

        assert len(prompt) > 0
        assert "小安" in prompt
        assert "保险" in prompt

    def test_get_stage_guidance_opening(self):
        from nanobot.agent.sales_advisor.persona import XiaoAnPersona

        persona = XiaoAnPersona()
        guidance = persona.get_stage_guidance("opening")

        assert len(guidance) > 0
        assert "开场" in guidance or "破冰" in guidance

    def test_get_stage_guidance_invalid(self):
        from nanobot.agent.sales_advisor.persona import XiaoAnPersona

        persona = XiaoAnPersona()
        guidance = persona.get_stage_guidance("invalid_stage")
        # Returns a default message for invalid stages
        assert "invalid_stage" in guidance
        assert len(guidance) > 0

    def test_validate_response_valid(self):
        from nanobot.agent.sales_advisor.persona import XiaoAnPersona

        persona = XiaoAnPersona()
        is_valid, msg = persona.validate_response("我理解您的担忧，让我们来看看有什么适合您的产品。")
        assert is_valid is True
        assert msg == ""

    def test_validate_response_ai_identity(self):
        from nanobot.agent.sales_advisor.persona import XiaoAnPersona

        persona = XiaoAnPersona()
        is_valid, msg = persona.validate_response("作为一个AI助手，我可以帮助您...")
        assert is_valid is False
        assert "AI" in msg

    def test_validate_response_robot_identity(self):
        from nanobot.agent.sales_advisor.persona import XiaoAnPersona

        persona = XiaoAnPersona()
        # This contains "我是机器人" exactly
        is_valid, msg = persona.validate_response("您好！我是机器人，有什么可以帮您...")
        assert is_valid is False
        assert "机器人" in msg or "AI" in msg


# =============================================================================
# state.py tests
# =============================================================================

class TestCustomerProfile:
    """Tests for CustomerProfile."""

    def test_customer_profile_defaults(self):
        from nanobot.agent.sales_advisor.state import CustomerProfile

        customer = CustomerProfile()
        assert customer.name == ""
        assert customer.age == 0
        assert customer.gender == ""
        assert customer.has_children is False

    def test_customer_to_context(self):
        from nanobot.agent.sales_advisor.state import CustomerProfile

        customer = CustomerProfile()
        customer.name = "阿哲"
        customer.age = 32
        customer.budget = "年交6000以内"

        context = customer.to_context()
        assert "阿哲" in context
        assert "32" in context
        assert "6000" in context

    def test_customer_to_context_empty(self):
        from nanobot.agent.sales_advisor.state import CustomerProfile

        customer = CustomerProfile()
        context = customer.to_context()
        assert "新客户" in context

    def test_customer_update_from_message(self):
        from nanobot.agent.sales_advisor.state import CustomerProfile

        customer = CustomerProfile()
        customer.update_from_message("我老婆全职带娃，有房贷", "user")

        assert customer.has_mortgage is True
        assert customer.family == "已婚"


class TestConversationState:
    """Tests for ConversationState."""

    def test_conversation_state_creation(self):
        from nanobot.agent.sales_advisor.state import ConversationState

        state = ConversationState(session_key="test:123")
        assert state.session_key == "test:123"
        assert state.current_stage == "opening"
        assert state.turn_count == 0

    def test_conversation_state_to_dict(self):
        from nanobot.agent.sales_advisor.state import ConversationState

        state = ConversationState(session_key="test:123")
        state_dict = state.to_dict()

        assert "session_key" in state_dict
        assert "customer" in state_dict
        assert "current_stage" in state_dict

    def test_conversation_state_from_dict(self):
        from nanobot.agent.sales_advisor.state import ConversationState

        original = ConversationState(session_key="test:456")
        original.customer.name = "测试用户"
        original.customer.age = 30

        state_dict = original.to_dict()
        restored = ConversationState.from_dict(state_dict)

        assert restored.session_key == "test:456"
        assert restored.customer.name == "测试用户"
        assert restored.customer.age == 30

    def test_advance_stage(self):
        from nanobot.agent.sales_advisor.state import ConversationState

        state = ConversationState(session_key="test:789")
        state.advance_stage("empathy")

        assert state.current_stage == "empathy"
        assert "opening" in state.stage_history

    def test_to_llm_context(self):
        from nanobot.agent.sales_advisor.state import ConversationState

        state = ConversationState(session_key="test:ctx")
        state.customer.name = "张三"
        ctx = state.to_llm_context()

        assert "客户" in ctx
        assert "张三" in ctx
        assert "开场" in ctx


class TestSalesStage:
    """Tests for SalesStage enum."""

    def test_all_stages(self):
        from nanobot.agent.sales_advisor.state import SalesStage

        stages = SalesStage.all_stages()
        assert "opening" in stages
        assert "empathy" in stages
        assert "closing" in stages
        assert "completed" in stages
        assert len(stages) == 9

    def test_next_stage(self):
        from nanobot.agent.sales_advisor.state import SalesStage

        assert SalesStage.next_stage("opening") == "empathy"
        assert SalesStage.next_stage("closing") == "after_sales"
        assert SalesStage.next_stage("completed") is None

    def test_stage_index(self):
        from nanobot.agent.sales_advisor.state import SalesStage

        assert SalesStage.stage_index("opening") == 0
        assert SalesStage.stage_index("empathy") == 1
        assert SalesStage.stage_index("closing") == 6


# =============================================================================
# flow.py tests
# =============================================================================

class TestSalesFlowManager:
    """Tests for SalesFlowManager."""

    def test_manager_creation(self):
        from nanobot.agent.sales_advisor.flow import SalesFlowManager

        manager = SalesFlowManager()
        assert manager.current_stage == "opening"

    def test_get_stage_definition(self):
        from nanobot.agent.sales_advisor.flow import SalesFlowManager

        manager = SalesFlowManager()
        definition = manager.get_stage_definition("opening")

        assert definition is not None
        assert definition.name == "开场破冰"

    def test_get_stage_name(self):
        from nanobot.agent.sales_advisor.flow import SalesFlowManager

        manager = SalesFlowManager()
        assert manager.get_stage_name("opening") == "开场破冰"
        assert manager.get_stage_name("empathy") == "共情客户"
        assert manager.get_stage_name("unknown") == "unknown"

    def test_detect_stage_from_message_opening(self):
        from nanobot.agent.sales_advisor.flow import SalesFlowManager

        manager = SalesFlowManager()
        manager.current_stage = "opening"

        detected = manager.detect_stage_from_message("你们这行水太深，怕被坑")
        # Should detect objection handling due to "怕"
        assert detected in ["objection_handling", "empathy"]

    def test_detect_stage_from_message_product(self):
        from nanobot.agent.sales_advisor.flow import SalesFlowManager

        manager = SalesFlowManager()
        manager.current_stage = "opening"

        detected = manager.detect_stage_from_message("具体保什么？")
        assert detected == "product_intro"

    def test_detect_stage_from_message_no_match(self):
        from nanobot.agent.sales_advisor.flow import SalesFlowManager

        manager = SalesFlowManager()
        manager.current_stage = "opening"

        detected = manager.detect_stage_from_message("今天天气真好")
        assert detected is None

    def test_get_stage_prompt(self):
        from nanobot.agent.sales_advisor.flow import SalesFlowManager

        manager = SalesFlowManager()
        prompt = manager.get_stage_prompt("opening")

        assert len(prompt) > 0
        assert "开场" in prompt or "opening" in prompt.lower()

    def test_get_progress_summary_empty(self):
        from nanobot.agent.sales_advisor.flow import SalesFlowManager

        manager = SalesFlowManager()
        summary = manager.get_progress_summary()
        assert "刚开场" in summary or "just started" in summary.lower()

    def test_reset(self):
        from nanobot.agent.sales_advisor.flow import SalesFlowManager

        manager = SalesFlowManager()
        manager.current_stage = "closing"
        manager.stage_history.append(MagicMock())

        manager.reset()
        assert manager.current_stage == "opening"
        assert len(manager.stage_history) == 0


# =============================================================================
# capabilities.py tests
# =============================================================================

class TestCapabilityModule:
    """Tests for CapabilityModule."""

    def test_capability_module_creation(self):
        from nanobot.agent.sales_advisor.capabilities import CapabilityModule

        module = CapabilityModule()
        assert len(module.capabilities) == 7

    def test_detect_capabilities_ice_breaking(self):
        from nanobot.agent.sales_advisor.capabilities import CapabilityModule

        module = CapabilityModule()
        caps = module.detect_capabilities("你们这行水太深，怕被坑", "opening", {})

        assert len(caps) > 0
        cap_ids = [c.id for c in caps]
        assert "ice_breaking" in cap_ids or "objection_handling" in cap_ids

    def test_detect_capabilities_product(self):
        from nanobot.agent.sales_advisor.capabilities import CapabilityModule

        module = CapabilityModule()
        caps = module.detect_capabilities("具体保什么？", "product_intro", {})

        assert len(caps) > 0
        cap_ids = [c.id for c in caps]
        assert "product_explanation" in cap_ids

    def test_get_capability_hint(self):
        from nanobot.agent.sales_advisor.capabilities import CapabilityModule

        module = CapabilityModule()
        hint = module.get_capability_hint("ice_breaking")
        assert len(hint) > 0


# =============================================================================
# knowledge.py tests
# =============================================================================

class TestProductKnowledge:
    """Tests for ProductKnowledge."""

    def test_product_knowledge_creation(self):
        from nanobot.agent.sales_advisor.knowledge import ProductKnowledge

        pk = ProductKnowledge()
        assert len(pk.products) > 0

    def test_get_product(self):
        from nanobot.agent.sales_advisor.knowledge import ProductKnowledge

        pk = ProductKnowledge()
        product = pk.get_product("安家守护")

        assert product is not None
        assert "安家" in product.name

    def test_get_product_fuzzy_match(self):
        from nanobot.agent.sales_advisor.knowledge import ProductKnowledge

        pk = ProductKnowledge()
        product = pk.get_product("守护")

        assert product is not None

    def test_get_all_products(self):
        from nanobot.agent.sales_advisor.knowledge import ProductKnowledge

        pk = ProductKnowledge()
        products = pk.get_all_products()

        assert len(products) > 0

    def test_format_product_intro(self):
        from nanobot.agent.sales_advisor.knowledge import ProductKnowledge

        pk = ProductKnowledge()
        product = pk.get_product("安家守护")
        intro = pk.format_product_intro(product)

        assert len(intro) > 0
        assert "安家" in intro
        assert "保障" in intro

    def test_match_products_by_age(self):
        from nanobot.agent.sales_advisor.knowledge import ProductKnowledge

        pk = ProductKnowledge()
        matched = pk.match_products({"age": 35})

        assert len(matched) > 0


class TestPolicyDatabase:
    """Tests for PolicyDatabase."""

    def test_policy_database_creation(self):
        from nanobot.agent.sales_advisor.knowledge import PolicyDatabase

        pd = PolicyDatabase()
        assert len(pd.policies) > 0

    def test_get_policy(self):
        from nanobot.agent.sales_advisor.knowledge import PolicyDatabase

        pd = PolicyDatabase()
        policy = pd.get_policy("失能")

        assert policy is not None
        assert "失能" in policy.title

    def test_get_policy_fuzzy(self):
        from nanobot.agent.sales_advisor.knowledge import PolicyDatabase

        pd = PolicyDatabase()
        policy = pd.get_policy("理赔")

        assert policy is not None

    def test_search_policies(self):
        from nanobot.agent.sales_advisor.knowledge import PolicyDatabase

        pd = PolicyDatabase()
        results = pd.search_policies("等待")

        assert len(results) > 0

    def test_format_policy(self):
        from nanobot.agent.sales_advisor.knowledge import PolicyDatabase

        pd = PolicyDatabase()
        policy = pd.get_policy("等待期")
        formatted = pd.format_policy(policy)

        assert len(formatted) > 0
        assert "等待期" in formatted


class TestSalesKnowledge:
    """Tests for SalesKnowledge."""

    def test_sales_knowledge_creation(self):
        from nanobot.agent.sales_advisor.knowledge import SalesKnowledge

        sk = SalesKnowledge()
        assert sk.products is not None
        assert sk.policies is not None
        assert len(sk.objection_responses) > 0

    def test_get_objection_response(self):
        from nanobot.agent.sales_advisor.knowledge import SalesKnowledge

        sk = SalesKnowledge()
        response = sk.get_objection_response(
            "太贵",
            {"premium": "5500元", "coverage": "100万"}
        )

        assert len(response) > 0
        assert "5500" in response
        assert "100万" in response

    def test_get_objection_response_unknown_type(self):
        from nanobot.agent.sales_advisor.knowledge import SalesKnowledge

        sk = SalesKnowledge()
        response = sk.get_objection_response("unknown_type", {})
        assert response == ""

    def test_get_relevant_knowledge(self):
        from nanobot.agent.sales_advisor.knowledge import SalesKnowledge

        sk = SalesKnowledge()
        results = sk.get_relevant_knowledge("失能")

        assert len(results) > 0


# =============================================================================
# advisor.py tests
# =============================================================================

class TestXiaoAnAdvisor:
    """Tests for XiaoAnAdvisor."""

    def test_advisor_creation(self):
        from nanobot.agent.sales_advisor.advisor import XiaoAnAdvisor

        advisor = XiaoAnAdvisor()
        assert advisor.persona is not None
        assert advisor.flow_manager is not None
        assert advisor.knowledge is not None

    def test_get_system_prompt(self):
        from nanobot.agent.sales_advisor.advisor import XiaoAnAdvisor

        advisor = XiaoAnAdvisor()
        prompt = advisor.get_system_prompt(None)

        assert len(prompt) > 0

    def test_get_product_info(self):
        from nanobot.agent.sales_advisor.advisor import XiaoAnAdvisor

        advisor = XiaoAnAdvisor()
        info = advisor.get_product_info("安家守护")

        assert len(info) > 0
        assert "安家" in info

    def test_get_product_info_not_found(self):
        from nanobot.agent.sales_advisor.advisor import XiaoAnAdvisor

        advisor = XiaoAnAdvisor()
        info = advisor.get_product_info("不存在的产品")

        assert "未找到" in info

    def test_get_policy_info(self):
        from nanobot.agent.sales_advisor.advisor import XiaoAnAdvisor

        advisor = XiaoAnAdvisor()
        info = advisor.get_policy_info("失能")

        assert len(info) > 0

    def test_get_objection_response(self):
        from nanobot.agent.sales_advisor.advisor import XiaoAnAdvisor

        advisor = XiaoAnAdvisor()
        response = advisor.get_objection_response("太贵", {"premium": "5500元", "coverage": "100万"})

        assert len(response) > 0

    def test_reset(self):
        from nanobot.agent.sales_advisor.advisor import XiaoAnAdvisor

        advisor = XiaoAnAdvisor()
        advisor._turn_count = 10
        advisor.reset()

        assert advisor._turn_count == 0

    def test_export_context(self):
        from nanobot.agent.sales_advisor.advisor import XiaoAnAdvisor, SalesContext

        advisor = XiaoAnAdvisor()
        context = SalesContext(session_key="test:export")
        context.customer.name = "测试"

        exported = advisor.export_context(context)
        assert "session_key" in exported
        assert "customer" in exported
        assert exported["customer"]["name"] == "测试"


class TestSalesContext:
    """Tests for SalesContext."""

    def test_sales_context_creation(self):
        from nanobot.agent.sales_advisor.advisor import SalesContext

        ctx = SalesContext(session_key="test:ctx")
        assert ctx.session_key == "test:ctx"
        assert ctx.current_stage == "opening"
        assert ctx.turn_count == 0

    def test_sales_context_to_context(self):
        from nanobot.agent.sales_advisor.advisor import SalesContext

        ctx = SalesContext(session_key="test:ctx")
        ctx.customer.name = "李四"
        ctx.last_product_mentioned = "安家守护"

        context_str = ctx.to_context()
        assert "李四" in context_str
        assert "安家守护" in context_str


class TestAdvisorConfig:
    """Tests for AdvisorConfig."""

    def test_advisor_config_defaults(self):
        from nanobot.agent.sales_advisor.advisor import AdvisorConfig

        config = AdvisorConfig()
        assert config.use_llm_stage_detection is False
        assert config.use_llm_capabilities is False
        assert config.min_stage_advance_turns == 2
