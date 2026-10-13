"""Configuration gates run without any certificate, file, listener or provider."""
import ssl
import unittest
from unittest.mock import Mock

from coding_orchestrator.preview_broker import PreviewBroker


class PreviewBrokerConfigurationTests(unittest.TestCase):
    def configuration(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.verify_mode = ssl.CERT_REQUIRED
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        return dict(context=context, client_id="synthetic-nas", client_sha256="a" * 64,
                    grants={}, admit_start=lambda *_: False)

    def test_default_off_closes_without_tls_or_dispatch(self):
        service, connection = Mock(), Mock()
        broker = PreviewBroker(service, **self.configuration())
        broker.handle(connection)
        connection.close.assert_called_once_with()
        self.assertEqual(service.mock_calls, [])

    def test_missing_or_weakened_configuration_is_rejected(self):
        for override in ({"context": None}, {"client_id": ""}, {"client_sha256": ""},
                         {"timeout_seconds": 0}, {"timeout_seconds": float("nan")},
                         {"enabled": 1}, {"admit_start": None}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                PreviewBroker(Mock(), **{**self.configuration(), **override})
        options = self.configuration()
        options["context"].verify_mode = ssl.CERT_OPTIONAL
        with self.assertRaises(ValueError):
            PreviewBroker(Mock(), **options)

    def test_busy_broker_does_not_queue_another_connection(self):
        connection = Mock()
        broker = PreviewBroker(Mock(), **self.configuration(), enabled=True)
        broker._active.acquire()
        try:
            broker.handle(connection)
            connection.close.assert_called_once_with()
        finally:
            broker._active.release()
