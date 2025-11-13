"""Tests for serialization of MessageAction with callouts."""

import pytest

from openhands.events.action.message import CalloutMessage, CalloutType, MessageAction
from openhands.events.serialization import event_from_dict, event_to_dict


class TestMessageActionWithCallouts:
    """Test MessageAction with callouts serialization/deserialization."""

    def test_message_action_without_callouts(self):
        """Test that MessageAction works without callouts (backward compatibility)."""
        action = MessageAction(content='This is a test message.')
        action._source = 'agent'
        action._id = 1

        serialized = event_to_dict(action)
        assert 'callouts' not in serialized['args'] or serialized['args']['callouts'] is None

        # Deserialize
        deserialized = event_from_dict(serialized)
        assert isinstance(deserialized, MessageAction)
        assert deserialized.content == 'This is a test message.'
        assert deserialized.callouts is None

    def test_message_action_with_single_callout(self):
        """Test MessageAction with a single callout."""
        callout = CalloutMessage(
            type=CalloutType.WORKAROUND,
            title='Installing packages individually',
            details='Using individual package installation instead of requirements.txt.',
        )

        action = MessageAction(
            content='Installing dependencies...', callouts=[callout]
        )
        action._source = 'agent'
        action._id = 2

        serialized = event_to_dict(action)

        # Check serialization
        assert 'callouts' in serialized['args']
        assert len(serialized['args']['callouts']) == 1
        assert serialized['args']['callouts'][0]['type'] == 'workaround'
        assert serialized['args']['callouts'][0]['title'] == 'Installing packages individually'

    def test_message_action_with_multiple_callouts(self):
        """Test MessageAction with multiple callouts."""
        callout1 = CalloutMessage(
            type=CalloutType.ASSUMPTION,
            title='Assuming Python 3.12',
            details='No version specified.',
        )
        callout2 = CalloutMessage(
            type=CalloutType.WARNING,
            title='Security concern',
            details='This may have security implications.',
        )

        action = MessageAction(
            content='Processing request...', callouts=[callout1, callout2]
        )
        action._source = 'agent'
        action._id = 3

        serialized = event_to_dict(action)

        assert len(serialized['args']['callouts']) == 2
        assert serialized['args']['callouts'][0]['type'] == 'assumption'
        assert serialized['args']['callouts'][1]['type'] == 'warning'

    def test_message_action_str_with_callouts(self):
        """Test that __str__ method shows callouts."""
        callout = CalloutMessage(
            type=CalloutType.HACK,
            title='Quick fix',
            details='Temporary workaround.',
        )

        action = MessageAction(
            content='Applying fix...', callouts=[callout]
        )
        action._source = 'agent'

        str_repr = str(action)

        assert 'CALLOUTS: 1 callout(s)' in str_repr
        assert '🔧 HACK: Quick fix' in str_repr
