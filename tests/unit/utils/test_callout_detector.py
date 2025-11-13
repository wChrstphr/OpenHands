"""Tests for CalloutDetector - automatic detection of callouts in messages."""

import pytest

from openhands.events.action.message import CalloutMessage, CalloutType, MessageAction
from openhands.utils.callout_detector import CalloutDetector


class TestCalloutDetector:
    """Test the CalloutDetector for automatic callout detection."""

    def test_detector_initialization(self):
        """Test that CalloutDetector can be initialized."""
        detector = CalloutDetector()
        assert detector is not None

    def test_detect_workaround_keyword(self):
        """Test detection of 'workaround' keyword."""
        detector = CalloutDetector()
        message = 'I will use a workaround to fix this issue.'

        callouts = detector.detect(message)

        assert len(callouts) == 1
        assert callouts[0].type == CalloutType.WORKAROUND
        assert 'workaround' in callouts[0].title.lower()

    def test_detect_hack_keyword(self):
        """Test detection of 'hack' keyword."""
        detector = CalloutDetector()
        message = 'This is a quick hack to solve the problem.'

        callouts = detector.detect(message)

        assert len(callouts) == 1
        assert callouts[0].type == CalloutType.HACK
        assert 'hack' in callouts[0].title.lower()

    def test_detect_compromise_keyword(self):
        """Test detection of 'compromise' keyword."""
        detector = CalloutDetector()
        message = 'We need to compromise on performance for simplicity.'

        callouts = detector.detect(message)

        assert len(callouts) == 1
        assert callouts[0].type == CalloutType.COMPROMISE

    def test_detect_assumption_keyword(self):
        """Test detection of 'assuming' keyword."""
        detector = CalloutDetector()
        message = 'I am assuming Python 3.12 is installed.'

        callouts = detector.detect(message)

        assert len(callouts) == 1
        assert callouts[0].type == CalloutType.ASSUMPTION

    def test_detect_incomplete_keywords(self):
        """Test detection of 'partial' and 'incomplete' keywords."""
        detector = CalloutDetector()
        message1 = 'This is a partial solution to the problem.'
        message2 = 'The implementation is incomplete.'

        callouts1 = detector.detect(message1)
        callouts2 = detector.detect(message2)

        assert len(callouts1) == 1
        assert callouts1[0].type == CalloutType.INCOMPLETE
        assert len(callouts2) == 1
        assert callouts2[0].type == CalloutType.INCOMPLETE

    def test_detect_warning_keywords(self):
        """Test detection of warning keywords."""
        detector = CalloutDetector()
        message = 'Warning: This operation may fail.'

        callouts = detector.detect(message)

        assert len(callouts) == 1
        assert callouts[0].type == CalloutType.WARNING

    def test_no_detection_in_normal_message(self):
        """Test that normal messages without keywords don't trigger callouts."""
        detector = CalloutDetector()
        message = 'I will install the dependencies using pip install.'

        callouts = detector.detect(message)

        assert len(callouts) == 0

    def test_detect_multiple_callouts_in_one_message(self):
        """Test detection of multiple different callouts in one message."""
        detector = CalloutDetector()
        message = 'I will use a workaround here. Warning: this is a hack and may not work in all cases.'

        callouts = detector.detect(message)

        assert len(callouts) >= 2
        types = {c.type for c in callouts}
        assert CalloutType.WORKAROUND in types
        assert CalloutType.WARNING in types or CalloutType.HACK in types

    def test_detect_case_insensitive(self):
        """Test that detection is case-insensitive."""
        detector = CalloutDetector()
        messages = [
            'This is a WORKAROUND',
            'This is a Workaround',
            'this is a workaround',
        ]

        for message in messages:
            callouts = detector.detect(message)
            assert len(callouts) == 1
            assert callouts[0].type == CalloutType.WORKAROUND

    def test_detect_with_context_extraction(self):
        """Test that detector extracts relevant context around the keyword."""
        detector = CalloutDetector()
        message = 'I will install packages individually instead of using requirements.txt as a workaround for formatting issues.'

        callouts = detector.detect(message)

        assert len(callouts) == 1
        assert callouts[0].type == CalloutType.WORKAROUND
        # Details should contain context
        assert 'install' in callouts[0].details.lower() or 'packages' in callouts[0].details.lower()

    def test_enrich_message_action_without_callouts(self):
        """Test enriching MessageAction without existing callouts."""
        detector = CalloutDetector()
        action = MessageAction(content='I will use a workaround to fix this.')

        enriched = detector.enrich_message_action(action)

        assert enriched.callouts is not None
        assert len(enriched.callouts) == 1
        assert enriched.callouts[0].type == CalloutType.WORKAROUND

    def test_enrich_message_action_with_existing_callouts(self):
        """Test enriching MessageAction that already has callouts."""
        detector = CalloutDetector()
        existing_callout = CalloutMessage(
            type=CalloutType.HACK,
            title='Manual callout',
            details='Manually added callout.',
        )
        action = MessageAction(
            content='I will use a workaround here.',
            callouts=[existing_callout],
        )

        enriched = detector.enrich_message_action(action)

        # Should have both existing and detected callouts
        assert len(enriched.callouts) == 2
        types = {c.type for c in enriched.callouts}
        assert CalloutType.HACK in types
        assert CalloutType.WORKAROUND in types

    def test_enrich_message_action_no_detection(self):
        """Test enriching MessageAction when no callouts are detected."""
        detector = CalloutDetector()
        action = MessageAction(content='I will install the packages.')

        enriched = detector.enrich_message_action(action)

        # Should not add empty callouts list
        assert enriched.callouts is None

    def test_detect_alternative_workaround_phrases(self):
        """Test detection of alternative workaround phrases."""
        detector = CalloutDetector()
        messages = [
            'I will work around this issue.',
            'As a temporary solution, I will...',
            'For now, I will bypass this...',
        ]

        for message in messages:
            callouts = detector.detect(message)
            assert len(callouts) >= 1
            # Should detect at least one callout (WORKAROUND, INCOMPLETE, etc.)
