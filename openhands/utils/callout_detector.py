"""CalloutDetector - Automatic detection of callouts in agent messages."""

import re
from typing import Pattern

from openhands.events.action.message import CalloutMessage, CalloutType, MessageAction


class CalloutDetector:
    """Detects callouts (workarounds, hacks, compromises) in agent messages."""

    def __init__(self):
        """Initialize the CalloutDetector with keyword patterns."""
        # Define patterns for each callout type
        self.patterns: dict[CalloutType, list[Pattern]] = {
            CalloutType.WORKAROUND: [
                re.compile(r'\bworkaround\b', re.IGNORECASE),
                re.compile(r'\bwork around\b', re.IGNORECASE),
            ],
            CalloutType.HACK: [
                re.compile(r'\bhack\b', re.IGNORECASE),  # Check for 'hack' first
                re.compile(r'\bquick fix\b', re.IGNORECASE),
                re.compile(r'\btemporary fix\b', re.IGNORECASE),
            ],
            CalloutType.COMPROMISE: [
                re.compile(r'\bcompromise\b', re.IGNORECASE),
                re.compile(r'\btrade[-\s]?off\b', re.IGNORECASE),
                re.compile(r'\bsuboptimal\b', re.IGNORECASE),
            ],
            CalloutType.ASSUMPTION: [
                re.compile(r'\bassum(e|ing)\b', re.IGNORECASE),
                re.compile(r'\bexpect(ing)?\b', re.IGNORECASE),
            ],
            CalloutType.INCOMPLETE: [
                re.compile(r'\bincomplete\b', re.IGNORECASE),
                re.compile(r'\bpartial\b', re.IGNORECASE),
                re.compile(r'\btemporary solution\b', re.IGNORECASE),
                re.compile(r'\bfor now\b', re.IGNORECASE),
                re.compile(r'\bbypass\b', re.IGNORECASE),
            ],
            CalloutType.WARNING: [
                re.compile(r'\bwarning\b', re.IGNORECASE),
                re.compile(r'\bcaution\b', re.IGNORECASE),
                re.compile(r'\bmay fail\b', re.IGNORECASE),
                re.compile(r'\bmight fail\b', re.IGNORECASE),
                re.compile(r'\brisk\b', re.IGNORECASE),
            ],
        }

    def detect(self, message: str) -> list[CalloutMessage]:
        """
        Detect callouts in a message.

        Args:
            message: The message content to analyze

        Returns:
            List of detected CalloutMessage objects
        """
        callouts: list[CalloutMessage] = []
        detected_types: set[CalloutType] = set()

        for callout_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = pattern.search(message)
                if match and callout_type not in detected_types:
                    # Extract context around the match
                    context = self._extract_context(message, match)

                    callout = CalloutMessage(
                        type=callout_type,
                        title=self._generate_title(callout_type, match.group()),
                        details=context,
                    )
                    callouts.append(callout)
                    detected_types.add(callout_type)
                    break  # Only detect one instance per type per message

        return callouts

    def _extract_context(self, message: str, match: re.Match, context_chars: int = 100) -> str:
        """
        Extract context around a matched keyword.

        Args:
            message: The full message
            match: The regex match object
            context_chars: Number of characters to extract around the match

        Returns:
            Context string around the matched keyword
        """
        start = max(0, match.start() - context_chars // 2)
        end = min(len(message), match.end() + context_chars // 2)

        context = message[start:end].strip()

        # Try to get complete sentences
        # Find the sentence containing the match
        sentences = re.split(r'[.!?]\s+', message)
        for sentence in sentences:
            if match.group() in sentence:
                return sentence.strip()

        return context

    def _generate_title(self, callout_type: CalloutType, matched_text: str) -> str:
        """
        Generate a title for the callout based on type and matched text.

        Args:
            callout_type: The type of callout
            matched_text: The text that was matched

        Returns:
            A descriptive title for the callout
        """
        # If the matched text is a direct keyword, use it in the title
        matched_lower = matched_text.lower().strip()

        if matched_lower in ['hack', 'workaround', 'compromise', 'warning']:
            return f'{matched_text.capitalize()} Detected'

        # Otherwise use default titles
        titles = {
            CalloutType.WORKAROUND: 'Workaround Applied',
            CalloutType.HACK: 'Hack Applied',
            CalloutType.COMPROMISE: 'Compromise Made',
            CalloutType.ASSUMPTION: 'Assumption Made',
            CalloutType.INCOMPLETE: 'Incomplete Solution',
            CalloutType.WARNING: 'Warning',
        }
        return titles.get(callout_type, f'{callout_type.value.title()} Detected')

    def enrich_message_action(self, action: MessageAction) -> MessageAction:
        """
        Enrich a MessageAction with automatically detected callouts.

        Args:
            action: The MessageAction to enrich

        Returns:
            The enriched MessageAction (same instance, modified in place)
        """
        detected_callouts = self.detect(action.content)

        if detected_callouts:
            if action.callouts is None:
                action.callouts = []

            # Add detected callouts that don't overlap with existing ones
            existing_types = {c.type for c in action.callouts} if action.callouts else set()

            for callout in detected_callouts:
                if callout.type not in existing_types:
                    action.callouts.append(callout)

        return action
