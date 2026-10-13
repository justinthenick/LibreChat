import json
import os
import socket
import sys
import time
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parent


def denied(*args, **kwargs):
    raise RuntimeError('Offline review fixture prohibits networking')


socket.socket.connect = denied
socket.socket.connect_ex = denied
(root / 'started').write_text(str(os.getpid()))
while (root / 'hold').exists():
    time.sleep(0.01)

from openhands.sdk.llm import Message, MessageToolCall, TextContent
from openhands.sdk.testing import TestLLM
from coding_orchestrator.provider import OpenHandsProviderConfig
from coding_orchestrator.review_cli import main


def scripted_provider(self):
    (root / 'provider-called').write_text('scripted only')
    result = {'findings': [{'severity': 'minor', 'path': 'example.py', 'line': 1,
                           'title': 'Synthetic material finding', 'evidence': 'value = 2',
                           'recommendation': 'Fixture only: verify the changed value.'}]}
    response = Message(role='assistant', content=[TextContent(text='')], tool_calls=[
        MessageToolCall(id='fixture-finish', name='finish', origin='completion',
                        arguments=json.dumps({'message': json.dumps(result)}))])
    return TestLLM.from_messages([response], disable_vision=True)


with patch.object(OpenHandsProviderConfig, 'build_llm', scripted_provider):
    sys.exit(main(sys.argv[5:]))
