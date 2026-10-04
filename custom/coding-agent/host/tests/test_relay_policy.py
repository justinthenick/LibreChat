import copy
import unittest
from pathlib import Path
from host_maintenance.relay_policy import validate_relay
from host_maintenance.acp_sandbox import ACP_NETWORK, ACP_RELAY_CONTAINER

IMAGE = 'sha256:' + 'a' * 64
SOCKET = Path('/reviewed/run')

def specimen():
    return {'Name': '/' + ACP_RELAY_CONTAINER, 'Image': IMAGE, 'State': {'Running': True},
        'Config': {'User': '10001:10001', 'Entrypoint': ['python3', '/app/relay.py'], 'Cmd': None,
                   'Env': ['CODEX_ADAPTER_SOCKET=/run/codex-adapter/codex.sock', 'ALLOWED_MODEL=phase3-mock']},
        'HostConfig': {'ReadonlyRootfs': True, 'Privileged': False, 'CapDrop': ['ALL'],
                       'SecurityOpt': ['no-new-privileges'], 'NetworkMode': ACP_NETWORK,
                       'PidsLimit': 64, 'Memory': 134217728, 'MemorySwap': 134217728, 'NanoCpus': 500000000},
        'NetworkSettings': {'Networks': {ACP_NETWORK: {}}},
        'Mounts': [{'Type': 'bind', 'Source': str(SOCKET), 'Destination': '/run/codex-adapter', 'RW': False, 'Propagation': 'rprivate'}]}

class RelayPolicyTests(unittest.TestCase):
    def test_reviewed_relay_passes(self):
        validate_relay(specimen(), IMAGE, SOCKET)

    def test_unpinned_or_wrong_image_rejected(self):
        for image in ('', 'relay:latest', 'sha256:' + 'b' * 64):
            with self.subTest(image=image), self.assertRaises(RuntimeError):
                validate_relay(specimen(), image, SOCKET)

    def test_runtime_drift_rejected(self):
        cases = [
            ('Config', 'User', '0'), ('Config', 'Entrypoint', ['sh']),
            ('HostConfig', 'ReadonlyRootfs', False), ('HostConfig', 'Privileged', True),
            ('HostConfig', 'CapAdd', ['SYS_ADMIN']), ('HostConfig', 'NetworkMode', 'host'),
            ('HostConfig', 'PortBindings', {'8080/tcp': [{}]}), ('HostConfig', 'PidMode', 'host'),
            ('HostConfig', 'Memory', 0), ('HostConfig', 'PidsLimit', 0),
            ('HostConfig', 'SecurityOpt', []), ('State', 'Running', False),
            ('NetworkSettings', 'Networks', {ACP_NETWORK: {}, 'bridge': {}})]
        for section, key, value in cases:
            with self.subTest(section=section, key=key):
                info=specimen(); info[section][key]=value
                with self.assertRaises(RuntimeError): validate_relay(info, IMAGE, SOCKET)

    def test_mount_drift_rejected(self):
        for key, value in [('RW', True), ('Source', '/home'), ('Destination', '/host'), ('Propagation', 'shared')]:
            with self.subTest(key=key):
                info=specimen(); info['Mounts'][0][key]=value
                with self.assertRaises(RuntimeError): validate_relay(info, IMAGE, SOCKET)
        info=specimen(); info['Mounts'].append(copy.deepcopy(info['Mounts'][0]))
        with self.assertRaises(RuntimeError): validate_relay(info, IMAGE, SOCKET)

    def test_provider_credentials_and_socket_override_rejected(self):
        for addition in ['OPENAI_API_KEY=secret', 'HTTPS_PROXY=http://proxy', 'CODEX_ADAPTER_SOCKET=/other.sock']:
            info=specimen(); info['Config']['Env'].append(addition)
            with self.assertRaises(RuntimeError): validate_relay(info, IMAGE, SOCKET)
