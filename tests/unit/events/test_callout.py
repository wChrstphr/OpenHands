"""Tests for the Callout system - workarounds, hacks, and compromise notifications."""

import pytest

from openhands.events.action.message import CalloutMessage, CalloutType


class TestCalloutType:
    """Test the CalloutType enum."""

    def test_callout_types_exist(self):
        """Test that all expected callout types are defined."""
        assert hasattr(CalloutType, 'WARNING')
        assert hasattr(CalloutType, 'HACK')
        assert hasattr(CalloutType, 'WORKAROUND')
        assert hasattr(CalloutType, 'COMPROMISE')
        assert hasattr(CalloutType, 'ASSUMPTION')
        assert hasattr(CalloutType, 'INCOMPLETE')

    def test_callout_type_values(self):
        """Test that callout types have correct string values."""
        assert CalloutType.WARNING.value == 'warning'
        assert CalloutType.HACK.value == 'hack'
        assert CalloutType.WORKAROUND.value == 'workaround'
        assert CalloutType.COMPROMISE.value == 'compromise'
        assert CalloutType.ASSUMPTION.value == 'assumption'
        assert CalloutType.INCOMPLETE.value == 'incomplete'


class TestCalloutMessage:
    """Test the CalloutMessage data class."""

    def test_callout_message_creation(self):
        """Test creating a CalloutMessage with required fields."""
        callout = CalloutMessage(
            type=CalloutType.WORKAROUND,
            title='Installing packages individually',
            details='Using individual package installation instead of requirements.txt due to formatting issues.',
        )

        assert callout.type == CalloutType.WORKAROUND
        assert callout.title == 'Installing packages individually'
        assert (
            callout.details
            == 'Using individual package installation instead of requirements.txt due to formatting issues.'
        )
        assert callout.metadata is None

    def test_callout_message_with_metadata(self):
        """Test creating a CalloutMessage with metadata."""
        callout = CalloutMessage(
            type=CalloutType.HACK,
            title='Quick fix applied',
            details='Using a temporary workaround for the issue.',
            metadata={'file': 'test.py', 'line': 42},
        )

        assert callout.type == CalloutType.HACK
        assert callout.metadata == {'file': 'test.py', 'line': 42}

    def test_callout_message_to_dict(self):
        """Test converting CalloutMessage to dictionary."""
        callout = CalloutMessage(
            type=CalloutType.ASSUMPTION,
            title='Assuming Python 3.12',
            details='No Python version specified, assuming 3.12 is available.',
        )

        result = callout.to_dict()

        assert result['type'] == 'assumption'
        assert result['title'] == 'Assuming Python 3.12'
        assert result['details'] == 'No Python version specified, assuming 3.12 is available.'
        assert result['metadata'] is None

    def test_callout_message_to_dict_with_metadata(self):
        """Test converting CalloutMessage with metadata to dictionary."""
        callout = CalloutMessage(
            type=CalloutType.INCOMPLETE,
            title='Partial solution',
            details='Only solved part of the problem.',
            metadata={'coverage': '60%'},
        )

        result = callout.to_dict()

        assert result['type'] == 'incomplete'
        assert result['metadata'] == {'coverage': '60%'}

    def test_callout_message_from_dict(self):
        """Test creating CalloutMessage from dictionary."""
        data = {
            'type': 'compromise',
            'title': 'Using suboptimal approach',
            'details': 'This approach works but is not ideal.',
            'metadata': None,
        }

        callout = CalloutMessage.from_dict(data)

        assert callout.type == CalloutType.COMPROMISE
        assert callout.title == 'Using suboptimal approach'
        assert callout.details == 'This approach works but is not ideal.'
        assert callout.metadata is None

    def test_callout_message_from_dict_with_metadata(self):
        """Test creating CalloutMessage from dictionary with metadata."""
        data = {
            'type': 'warning',
            'title': 'Security concern',
            'details': 'This operation might have security implications.',
            'metadata': {'severity': 'medium'},
        }

        callout = CalloutMessage.from_dict(data)

        assert callout.type == CalloutType.WARNING
        assert callout.metadata == {'severity': 'medium'}

    def test_callout_message_emoji_property(self):
        """Test that each callout type has an associated emoji."""
        test_cases = [
            (CalloutType.WARNING, '⚠️'),
            (CalloutType.HACK, '🔧'),
            (CalloutType.WORKAROUND, '🔄'),
            (CalloutType.COMPROMISE, '⚖️'),
            (CalloutType.ASSUMPTION, '💭'),
            (CalloutType.INCOMPLETE, '🚧'),
        ]

        for callout_type, expected_emoji in test_cases:
            callout = CalloutMessage(
                type=callout_type, title='Test', details='Test details'
            )
            assert callout.emoji == expected_emoji
