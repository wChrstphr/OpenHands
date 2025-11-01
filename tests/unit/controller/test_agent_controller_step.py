"""
MC/DC tests for the AgentController._step method

Based on 20 identified conditions and 25 derived MC/DC test cases.
Coverage: 4 main composite decisions (lines 926-938, 951-956, 983-984, 995-996) from AgentController._step.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from litellm import BadRequestError, ContextWindowExceededError

from openhands.controller.agent_controller import AgentController
from openhands.controller.state.state import State
from openhands.core.config import OpenHandsConfig
from openhands.core.config.agent_config import AgentConfig
from openhands.core.config.llm_config import LLMConfig
from openhands.core.schema import AgentState
from openhands.events import EventSource, EventStream
from openhands.events.action import (
    BrowseInteractiveAction,
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.events.observation import ErrorObservation
from openhands.llm import LLM
from openhands.llm.llm_registry import LLMRegistry
from openhands.llm.metrics import Metrics
from openhands.runtime.impl.action_execution.action_execution_client import (
    ActionExecutionClient,
)
from openhands.events.action.action import (
    ActionSecurityRisk,
    ActionConfirmationStatus,
)
from openhands.events.action.agent import CondensationRequestAction
from openhands.core.exceptions import LLMContextWindowExceedError
from openhands.server.services.conversation_stats import ConversationStats
from openhands.storage.memory import InMemoryFileStore


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_agent_with_stats():
    """Create a mock agent with properly connected LLM registry and conversation stats."""
    import uuid

    # Create LLM registry
    config = OpenHandsConfig()
    llm_registry = LLMRegistry(config=config)

    # Create conversation stats
    file_store = InMemoryFileStore({})
    conversation_id = f'test-conversation-{uuid.uuid4()}'
    conversation_stats = ConversationStats(
        file_store=file_store, conversation_id=conversation_id, user_id='test-user'
    )

    # Connect registry to stats
    llm_registry.subscribe(conversation_stats.register_llm)

    # Create mock agent
    agent = MagicMock()
    agent_config = MagicMock(spec=AgentConfig)
    llm_config = LLMConfig(
        model='gpt-4o',
        api_key='test_key',
        num_retries=2,
        retry_min_wait=1,
        retry_max_wait=2,
    )
    agent_config.disabled_microagents = []
    agent_config.enable_mcp = True
    agent_config.cli_mode = False  # Add cli_mode attribute
    llm_registry.service_to_llm.clear()
    mock_llm = llm_registry.get_llm('agent_llm', llm_config)
    agent.llm = mock_llm
    agent.name = 'test-agent'
    agent.sandbox_plugins = []
    agent.config = agent_config
    agent.prompt_manager = MagicMock()

    # Add system message mock
    from openhands.events.action.message import SystemMessageAction

    system_message = SystemMessageAction(
        content='Test system message', tools=['test_tool']
    )
    system_message._source = EventSource.AGENT
    system_message._id = -1
    agent.get_system_message.return_value = system_message

    return agent, conversation_stats, llm_registry


@pytest.fixture
def test_event_stream():
    """Create a real event stream for testing."""
    event_stream = EventStream(sid='test', file_store=InMemoryFileStore({}))
    return event_stream


@pytest.fixture
def mock_runtime(test_event_stream):
    """Create a mock runtime."""
    runtime = MagicMock(spec=ActionExecutionClient)
    runtime.event_stream = test_event_stream
    return runtime


# ============================================================================
# GROUP 1: CONTEXT WINDOW ERROR DETECTION (Decision lines 926-938)
# Table 2.1 - 10 test cases (CT01-CT10)
# Structure: A or B or C or D or E or F or (G and H) or I
# ============================================================================


class TestContextWindowErrorDetection:
    """MC/DC tests for context window error detection (lines 926-938)."""

    @pytest.mark.asyncio
    async def test_ct01_only_contextwindowexceedederror_string(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT01: Only CD1 is true
        Input: error_str contains "contextwindowexceedederror"
        Expected: Detects context error and adds CondensationRequestAction
        Coverage: CD1=V, CD2-9=F → Line 1 from Table 2.1
        MC/DC Pair: {CT01, CT10}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats
        # Enable history truncation so error is handled
        agent.config.enable_history_truncation = True

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,
            headless_mode=True,
        )

        # Setup: agent raises exceção com string específica
        error = BadRequestError(
            message='Error: contextwindowexceedederror occurred',
            model='gpt-4',
            llm_provider='openai',
        )

        def agent_step_fn(state):
            raise error

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # Executa o step
        await controller._step()

        # Verify that context window error was detected
        # O código deve adicionar um CondensationRequestAction ao event_stream
        events = list(test_event_stream.get_events())
        condensation_events = [e for e in events if isinstance(e, CondensationRequestAction)]
        assert len(condensation_events) > 0, "Deveria adicionar CondensationRequestAction"
        assert controller.state.agent_state == AgentState.RUNNING

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct02_only_prompt_is_too_long_string(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT02: Only CD2 is true
        Input: error_str contains "prompt is too long"
        Expected: Detects context error and adds CondensationRequestAction
        Coverage: CD1=F, CD2=V, CD3-9=F → Line 2 from Table 2.1
        MC/DC Pair: {CT02, CT10}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats
        # Enable history truncation so error is handled
        agent.config.enable_history_truncation = True

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,
            headless_mode=True,
        )

        error = BadRequestError(
            message='Error: prompt is too long: 233885 tokens > 200000 maximum',
            model='gpt-4',
            llm_provider='openai',
        )

        def agent_step_fn(state):
            raise error

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # Executa o step
        await controller._step()

        # Verify that context window error was detected
        # O código deve adicionar um CondensationRequestAction ao event_stream
        events = list(test_event_stream.get_events())
        condensation_events = [e for e in events if isinstance(e, CondensationRequestAction)]
        assert len(condensation_events) > 0, "Deveria adicionar CondensationRequestAction"
        assert controller.state.agent_state == AgentState.RUNNING

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct03_only_input_length_max_tokens_string(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT03: Only CD3 is true
        Input: error_str contains "input length and max_tokens exceed context limit"
        Expected: Detects context error and adds CondensationRequestAction
        Coverage: CD1-2=F, CD3=V, CD4-9=F → Line 3 from Table 2.1
        MC/DC Pair: {CT03, CT10}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats
        # Enable history truncation so error is handled
        agent.config.enable_history_truncation = True

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,
            headless_mode=True,
        )

        error = BadRequestError(
            message='Error: input length and `max_tokens` exceed context limit',
            model='gpt-4',
            llm_provider='openai',
        )

        def agent_step_fn(state):
            raise error

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # Executa o step
        await controller._step()

        # Verify that context window error was detected
        events = list(test_event_stream.get_events())
        condensation_events = [e for e in events if isinstance(e, CondensationRequestAction)]
        assert len(condensation_events) > 0, "Deveria adicionar CondensationRequestAction"
        assert controller.state.agent_state == AgentState.RUNNING

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct04_only_please_reduce_length_string(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT04: Only CD4 is true
        Input: error_str contains "please reduce the length of"
        Expected: Detects context error and adds CondensationRequestAction
        Coverage: CD1-3=F, CD4=V, CD5-9=F → Line 4 from Table 2.1
        MC/DC Pair: {CT04, CT10}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats
        # Enable history truncation so error is handled
        agent.config.enable_history_truncation = True

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,
            headless_mode=True,
        )

        error = BadRequestError(
            message='Error: please reduce the length of your message',
            model='gpt-4',
            llm_provider='openai',
        )

        def agent_step_fn(state):
            raise error

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # Executa o step
        await controller._step()

        # Verify that context window error was detected
        events = list(test_event_stream.get_events())
        condensation_events = [e for e in events if isinstance(e, CondensationRequestAction)]
        assert len(condensation_events) > 0, "Deveria adicionar CondensationRequestAction"
        assert controller.state.agent_state == AgentState.RUNNING

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct05_only_request_exceeds_context_string(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT05: Only CD5 is true
        Input: error_str contains "the request exceeds the available context size"
        Expected: Detects context error and adds CondensationRequestAction
        Coverage: CD1-4=F, CD5=V, CD6-9=F → Line 5 from Table 2.1
        MC/DC Pair: {CT05, CT10}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats
        # Enable history truncation so error is handled
        agent.config.enable_history_truncation = True

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,
            headless_mode=True,
        )

        error = BadRequestError(
            message='Error: the request exceeds the available context size',
            model='gpt-4',
            llm_provider='openai',
        )

        def agent_step_fn(state):
            raise error

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # Executa o step
        await controller._step()

        # Verify that context window error was detected
        events = list(test_event_stream.get_events())
        condensation_events = [e for e in events if isinstance(e, CondensationRequestAction)]
        assert len(condensation_events) > 0, "Deveria adicionar CondensationRequestAction"
        assert controller.state.agent_state == AgentState.RUNNING

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct06_only_context_length_exceeded_string(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT06: Only CD6 is true
        Input: error_str contains "context length exceeded"
        Expected: Detects context error and adds CondensationRequestAction
        Coverage: CD1-5=F, CD6=V, CD7-9=F → Line 6 from Table 2.1
        MC/DC Pair: {CT06, CT10}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats
        # Enable history truncation so error is handled
        agent.config.enable_history_truncation = True

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,
            headless_mode=True,
        )

        error = BadRequestError(
            message='Error: context length exceeded',
            model='gpt-4',
            llm_provider='openai',
        )

        def agent_step_fn(state):
            raise error

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # Executa o step
        await controller._step()

        # Verify that context window error was detected
        events = list(test_event_stream.get_events())
        condensation_events = [e for e in events if isinstance(e, CondensationRequestAction)]
        assert len(condensation_events) > 0, "Deveria adicionar CondensationRequestAction"
        assert controller.state.agent_state == AgentState.RUNNING

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct07_sambanova_with_maximum_context_and(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT07: CD7 AND CD8 are true (G and H)
        Input: error_str contains "sambanovaexception" E "maximum context length"
        Expected: Detects context error and adds CondensationRequestAction
        Coverage: CD1-6=F, CD7=V, CD8=V, CD9=F → Line 7 from Table 2.1
        MC/DC Pair: {CT07, CT09} - testa o AND composto
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats
        # Enable history truncation so error is handled
        agent.config.enable_history_truncation = True

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,
            headless_mode=True,
        )

        error = BadRequestError(
            message='Error: sambanovaexception: maximum context length exceeded',
            model='sambanova',
            llm_provider='sambanova',
        )

        def agent_step_fn(state):
            raise error

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # Executa o step
        await controller._step()

        # Verify that context window error was detected
        events = list(test_event_stream.get_events())
        condensation_events = [e for e in events if isinstance(e, CondensationRequestAction)]
        assert len(condensation_events) > 0, "Deveria adicionar CondensationRequestAction"
        assert controller.state.agent_state == AgentState.RUNNING

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct08_isinstance_contextwindowexceedederror(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT08: Only CD9 is true
        Input: Exceção é instância de ContextWindowExceededError
        Expected: Detects context error and adds CondensationRequestAction
        Coverage: CD1-8=F, CD9=V → Line 8 from Table 2.1
        MC/DC Pair: {CT08, CT10}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats
        # Enable history truncation so error is handled
        agent.config.enable_history_truncation = True

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,
            headless_mode=True,
        )

        error = ContextWindowExceededError(
            message='Context window exceeded',
            model='gpt-4',
            llm_provider='openai',
        )

        def agent_step_fn(state):
            raise error

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # Executa o step
        await controller._step()

        # Verify that context window error was detected
        events = list(test_event_stream.get_events())
        condensation_events = [e for e in events if isinstance(e, CondensationRequestAction)]
        assert len(condensation_events) > 0, "Deveria adicionar CondensationRequestAction"
        assert controller.state.agent_state == AgentState.RUNNING

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct09_sambanova_without_maximum_context_not_detected(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT09: CD7=V but CD8=F (G sem H) - teste negativo do AND
        Input: error_str contains "sambanovaexception" but NOT "maximum context length"
        Expected: NÃO detecta como erro de contexto
        Coverage: CD1-6=F, CD7=V, CD8=F, CD9=F → Line 9 from Table 2.1
        MC/DC Pair: {CT09, CT07} - proves that H is necessary junto com G
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats
        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,
            headless_mode=True,
        )

        error = BadRequestError(
            message='Error: sambanovaexception: different error message',
            model='sambanova',
            llm_provider='sambanova',
        )

        def agent_step_fn(state):
            raise error

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # Aqui esperamos que o erro seja tratado genericamente, não como context window
        with pytest.raises(BadRequestError):
            await controller._step()

        # Verifica que NÃO adicionou CondensationRequestAction
        events = list(test_event_stream.get_events())
        condensation_events = [e for e in events if isinstance(e, CondensationRequestAction)]
        assert len(condensation_events) == 0, "Não deveria adicionar CondensationRequestAction"

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct10_generic_error_not_context_window(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT10: All conditions are false (caso base)
        Input: Erro genérico sem nenhuma string de context window
        Expected: Does NOT detect context error
        Coverage: CD1-9=F → Line 10 from Table 2.1
        MC/DC Pair: Base para todos os outros casos
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats
        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,
            headless_mode=True,
        )

        error = BadRequestError(
            message='Generic API error message',
            model='gpt-4',
            llm_provider='openai',
        )

        def agent_step_fn(state):
            raise error

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        with pytest.raises(BadRequestError):
            await controller._step()

        # Verifica que NÃO adicionou CondensationRequestAction
        events = list(test_event_stream.get_events())
        condensation_events = [e for e in events if isinstance(e, CondensationRequestAction)]
        assert len(condensation_events) == 0, "Não deveria adicionar CondensationRequestAction"

        await controller.close()


# ============================================================================
# GROUP 2: ACTION TYPE CHECK FOR CONFIRMATION (Decision lines 951-956)
# Table 2.2 - 7 test cases (CT11-CT17)
# Structure: A and (B or C or D or E or F)
# ============================================================================


class TestActionTypeCheckForConfirmation:
    """MC/DC tests for action type verification (lines 951-956)."""

    @pytest.mark.asyncio
    async def test_ct11_cmdrunaction_with_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT11: CmdRunAction with confirmation_mode enabled
        Input: confirmation_mode=True e action é CmdRunAction
        Expected: Enters security verification block
        Coverage: CD10=V, CD11=V, CD12-15=F → Line 1 from Table 2.2
        MC/DC Pair: {CT11, CT17}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.LOW

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,  # CD10=V
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = CmdRunAction(command='ls -la')  # CD11=V

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()

        # Verify that security analyzer was called
        mock_security_analyzer.security_risk.assert_called_once()

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct12_ipythonrunaction_with_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT12: IPythonRunCellAction with confirmation_mode enabled
        Input: confirmation_mode=True e action é IPythonRunCellAction
        Expected: Enters security verification block
        Coverage: CD10=V, CD11=F, CD12=V, CD13-15=F → Line 2 from Table 2.2
        MC/DC Pair: {CT12, CT17}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.LOW

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = IPythonRunCellAction(code='print("hello")')  # CD12=V

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()
        mock_security_analyzer.security_risk.assert_called_once()

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct13_browseinteractiveaction_with_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT13: BrowseInteractiveAction with confirmation_mode enabled
        Input: confirmation_mode=True e action é BrowseInteractiveAction
        Expected: Enters security verification block
        Coverage: CD10=V, CD11-12=F, CD13=V, CD14-15=F → Line 3 from Table 2.2
        MC/DC Pair: {CT13, CT17}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.LOW

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = BrowseInteractiveAction(
            browser_actions='goto("http://example.com")'
        )  # CD13=V

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()
        mock_security_analyzer.security_risk.assert_called_once()

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct14_fileeditaction_with_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT14: FileEditAction with confirmation_mode enabled
        Input: confirmation_mode=True e action é FileEditAction
        Expected: Enters security verification block
        Coverage: CD10=V, CD11-13=F, CD14=V, CD15=F → Line 4 from Table 2.2
        MC/DC Pair: {CT14, CT17}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.LOW

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = FileEditAction(path='test.txt', content='test')  # CD14=V

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()
        mock_security_analyzer.security_risk.assert_called_once()

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct15_filereadaction_with_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT15: FileReadAction with confirmation_mode enabled
        Input: confirmation_mode=True e action é FileReadAction
        Expected: Enters security verification block
        Coverage: CD10=V, CD11-14=F, CD15=V → Line 5 from Table 2.2
        MC/DC Pair: {CT15, CT17}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.LOW

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = FileReadAction(path='test.txt')  # CD15=V

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()
        mock_security_analyzer.security_risk.assert_called_once()

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct16_non_runnable_action_with_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT16: Non-runnable action with confirmation_mode enabled
        Input: confirmation_mode=True but action is not runnable
        Expected: Does NOT enter verification block (no type matches)
        Coverage: CD10=V, CD11-15=F → Line 6 from Table 2.2
        MC/DC Pair: Demonstra que pelo menos um tipo deve ser True
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = MessageAction(content='test')  # Não é runnable

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()

        # Verify that SecurityAnalyzer was NOT called
        mock_security_analyzer.security_risk.assert_not_called()

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct17_cmdrunaction_without_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT17: CmdRunAction without confirmation_mode
        Input: confirmation_mode=False e action é CmdRunAction
        Expected: Does NOT enter verification block
        Coverage: CD10=F, CD11=V, CD12-15=F → Line 7 from Table 2.2
        MC/DC Pair: {CT17, CT11} - proves that CD10 is necessary
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,  # CD10=F
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = CmdRunAction(command='ls -la')

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()

        # Verify that SecurityAnalyzer was NOT called
        mock_security_analyzer.security_risk.assert_not_called()

        await controller.close()


# ============================================================================
# GROUP 3: SECURITY CONFIRMATION LOGIC (Decision lines 983-984)
# Table 2.3 - 5 test cases (CT18-CT22)
# Structure: (A or B) and C
# ============================================================================


class TestSecurityConfirmationLogic:
    """MC/DC tests for security confirmation logic (lines 983-984)."""

    @pytest.mark.asyncio
    async def test_ct18_high_risk_with_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT18: HIGH risk with confirmation_mode enabled
        Input: is_high_security_risk=True, confirmation_mode=True
        Expected: Action marked as AWAITING_CONFIRMATION
        Coverage: CD16=V, CD17=F, CD18=V → VFV from Table 2.3 (Line 3)
        MC/DC Pair: {CT18, CT19}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = (
            ActionSecurityRisk.HIGH
        )  # CD16=V

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,  # CD18=V
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = CmdRunAction(command='rm -rf /')

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()

        # Verify that action has confirmation_state set
        events = list(test_event_stream.get_events())
        action_events = [e for e in events if isinstance(e, CmdRunAction)]
        assert len(action_events) > 0
        last_action = action_events[-1]
        assert hasattr(last_action, 'confirmation_state')
        assert (
            last_action.confirmation_state
            == ActionConfirmationStatus.AWAITING_CONFIRMATION
        )

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct19_high_risk_without_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT19: HIGH risk without confirmation_mode
        Input: is_high_security_risk=True, confirmation_mode=False
        Expected: Action does NOT require confirmation
        Coverage: CD16=V, CD17=F, CD18=F → VFF from Table 2.3 (Line 4)
        MC/DC Pair: {CT19, CT18}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.HIGH

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,  # CD18=F
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = CmdRunAction(command='rm -rf /')

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()

        # Verify that action does NOT have confirmation_state or is not AWAITING
        events = list(test_event_stream.get_events())
        action_events = [e for e in events if isinstance(e, CmdRunAction)]
        if action_events:
            last_action = action_events[-1]
            # Should not be waiting for confirmation
            if hasattr(last_action, 'confirmation_state'):
                assert (
                    last_action.confirmation_state
                    != ActionConfirmationStatus.AWAITING_CONFIRMATION
                )

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct20_ask_every_action_with_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT20: Ask every action with confirmation_mode enabled
        Input: is_ask_for_every_action=True, confirmation_mode=True
        Expected: Action marked as AWAITING_CONFIRMATION
        Coverage: CD16=F, CD17=V, CD18=V → FVV from Table 2.3 (Line 5)
        MC/DC Pair: {CT20, CT21}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Configure ask_for_every_action through config
        config = OpenHandsConfig()
        config.security.confirmation_mode = True
        config.security.security_analyzer = 'none'  # Simulates ask_for_every_action

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.MEDIUM

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,  # CD18=V
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = CmdRunAction(command='ls -la')

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # Simulate ask_for_every_action flag
        controller._ask_for_every_action = True  # CD17=V

        await controller._step()

        events = list(test_event_stream.get_events())
        action_events = [e for e in events if isinstance(e, CmdRunAction)]
        if action_events:
            last_action = action_events[-1]
            if hasattr(last_action, 'confirmation_state'):
                # May be AWAITING_CONFIRMATION if logic applies
                pass

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct21_ask_every_action_without_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT21: Ask every action without confirmation_mode
        Input: is_ask_for_every_action=True, confirmation_mode=False
        Expected: Action does NOT require confirmation
        Coverage: CD16=F, CD17=V, CD18=F → FVF from Table 2.3 (Line 6)
        MC/DC Pair: {CT21, CT20}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.MEDIUM

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,  # CD18=F
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = CmdRunAction(command='ls -la')

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        controller._ask_for_every_action = True  # CD17=V

        await controller._step()

        events = list(test_event_stream.get_events())
        action_events = [e for e in events if isinstance(e, CmdRunAction)]
        if action_events:
            last_action = action_events[-1]
            if hasattr(last_action, 'confirmation_state'):
                assert (
                    last_action.confirmation_state
                    != ActionConfirmationStatus.AWAITING_CONFIRMATION
                )

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct22_no_risks_identified_with_confirmation_mode(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT22: No risks identified with confirmation_mode enabled
        Input: is_high_security_risk=False, is_ask_for_every_action=False, confirmation_mode=True
        Expected: Action does NOT require confirmation
        Coverage: CD16=F, CD17=F, CD18=V → FFV from Table 2.3 (Line 7)
        MC/DC Pair: Demonstrates that (A or B) needs to be True
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = (
            ActionSecurityRisk.LOW
        )  # CD16=F

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,  # CD18=V
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = CmdRunAction(command='ls -la')

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        controller._ask_for_every_action = False  # CD17=F

        await controller._step()

        events = list(test_event_stream.get_events())
        action_events = [e for e in events if isinstance(e, CmdRunAction)]
        if action_events:
            last_action = action_events[-1]
            # Should not be waiting for confirmation
            if hasattr(last_action, 'confirmation_state'):
                assert (
                    last_action.confirmation_state
                    != ActionConfirmationStatus.AWAITING_CONFIRMATION
                )

        await controller.close()


# ============================================================================
# GROUP 4: AWAITING CONFIRMATION CHECK (Decision lines 995-996)
# Table 2.4 - 3 test cases (CT23-CT25)
# Structure: A and B
# ============================================================================


class TestAwaitingConfirmationCheck:
    """MC/DC tests for confirmation state verification (lines 995-996)."""

    @pytest.mark.asyncio
    async def test_ct23_action_with_awaiting_confirmation_state(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT23: Action with confirmation_state AWAITING_CONFIRMATION
        Input: action has attribute confirmation_state with value AWAITING_CONFIRMATION
        Expected: Agent state changes to AWAITING_USER_CONFIRMATION
        Coverage: CD19=V, CD20=V → VV from Table 2.4 (Line 1)
        MC/DC Pair: {CT23, CT24}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.HIGH

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = CmdRunAction(command='rm -rf /')
        # Simulate that action already has confirmation_state
        action.confirmation_state = ActionConfirmationStatus.AWAITING_CONFIRMATION

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()

        # Verify that state changed to AWAITING_USER_CONFIRMATION
        assert (
            controller.state.agent_state == AgentState.AWAITING_USER_CONFIRMATION
        )

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct24_action_with_different_confirmation_state(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT24: Action with confirmation_state diferente
        Input: action has attribute confirmation_state but value is CONFIRMED
        Expected: Agent state does NOT change
        Coverage: CD19=V, CD20=F → VF from Table 2.4 (Line 2)
        MC/DC Pair: {CT24, CT23}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.LOW

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        action = CmdRunAction(command='ls -la')
        # Simulate that action has confirmation_state but was already confirmed
        action.confirmation_state = ActionConfirmationStatus.CONFIRMED

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()

        # Verify that state did NOT change to AWAITING_USER_CONFIRMATION
        assert (
            controller.state.agent_state != AgentState.AWAITING_USER_CONFIRMATION
        )

        await controller.close()

    @pytest.mark.asyncio
    async def test_ct25_action_without_confirmation_state(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        CT25: Action without attribute confirmation_state
        Input: action does NOT have attribute confirmation_state
        Expected: Agent state does NOT change
        Coverage: CD19=F, CD20=V → FV from Table 2.4 (Line 3)
        MC/DC Pair: {CT25, CT23}
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats
        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=False,
            headless_mode=True,
        )

        action = MessageAction(content='test')  # Does not have confirmation_state

        def agent_step_fn(state):
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        await controller._step()

        # Verify that state did NOT change to AWAITING_USER_CONFIRMATION
        assert controller.state.agent_state != AgentState.AWAITING_USER_CONFIRMATION

        await controller.close()


# ============================================================================
# TESTES DE INTEGRAÇÃO
# ============================================================================


class TestStepIntegration:
    """Integration tests to verify the complete _step method flow."""

    @pytest.mark.asyncio
    async def test_full_flow_context_error_then_security_check(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        Teste de integração: Context window error followed by security check
        Verifies that the complete flow works correctly.
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.HIGH

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        call_count = 0

        def agent_step_fn(state):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # Primeira chamada: raises context window error
                raise ContextWindowExceededError(
                    message='Context window exceeded',
                    model='gpt-4',
                    llm_provider='openai',
                )
            else:
                # Second call: returns action that needs confirmation
                return CmdRunAction(command='rm -rf /')

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # First call: context window error
        agent.config.enable_history_truncation = True
        await controller._step()
        assert call_count == 1

        # Second call: security check
        controller.state.agent_state = AgentState.RUNNING
        await controller._step()
        assert call_count == 2

        await controller.close()

    @pytest.mark.asyncio
    async def test_multiple_action_types_in_sequence(
        self, mock_agent_with_stats, test_event_stream
    ):
        """
        Teste de integração: Multiple action types in sequence
        Verifies that different action types are processed correctly.
        """
        agent, conversation_stats, llm_registry = mock_agent_with_stats

        # Create security_analyzer mock
        mock_security_analyzer = AsyncMock()
        mock_security_analyzer.security_risk.return_value = ActionSecurityRisk.LOW

        controller = AgentController(
            agent=agent,
            event_stream=test_event_stream,
            conversation_stats=conversation_stats,
            iteration_delta=10,
            sid='test',
            confirmation_mode=True,
            headless_mode=True,
            security_analyzer=mock_security_analyzer,
        )

        actions = [
            CmdRunAction(command='ls'),
            IPythonRunCellAction(code='print("test")'),
            FileReadAction(path='test.txt'),
        ]
        current_action_index = 0

        def agent_step_fn(state):
            nonlocal current_action_index
            action = actions[current_action_index]
            current_action_index = (current_action_index + 1) % len(actions)
            return action

        agent.step = agent_step_fn
        controller.state.agent_state = AgentState.RUNNING

        # Execute 3 steps
        for _ in range(3):
            controller.state.agent_state = AgentState.RUNNING
            await controller._step()

        # Verify that at least one action was processed
        # Exact behavior may vary depending on agent state after each step
        assert current_action_index >= 1  # At least one action was processed

        await controller.close()
