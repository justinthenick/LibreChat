import importlib.util
import json
import pathlib
import tempfile
import unittest


MODULE_PATH = pathlib.Path(__file__).with_name("runtime-evidence.py")
SPEC = importlib.util.spec_from_file_location("runtime_evidence", MODULE_PATH)
runtime_evidence = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runtime_evidence)


class RuntimeEvidenceTests(unittest.TestCase):
    def test_safe_mounts_omit_host_bind_source(self):
        mounts = [
            {
                "Type": "bind",
                "Source": "/volume1/private/secret-path",
                "Destination": "/workspace",
                "RW": True,
            },
            {
                "Type": "volume",
                "Name": "librechat-data",
                "Source": "/var/lib/docker/volumes/librechat-data/_data",
                "Destination": "/app/data",
                "RW": True,
            },
        ]
        result = runtime_evidence.safe_mounts(mounts)
        rendered = json.dumps(result)
        self.assertNotIn("secret-path", rendered)
        self.assertNotIn("/var/lib/docker/volumes", rendered)
        self.assertEqual(result[0]["destination"], "/workspace")
        self.assertEqual(result[1]["name"], "librechat-data")

    def test_snapshot_guard_rejects_secret_shaped_keys(self):
        with self.assertRaises(RuntimeError):
            runtime_evidence.assert_snapshot_safe({"token": "must-not-emit"})
        with self.assertRaises(RuntimeError):
            runtime_evidence.assert_snapshot_safe({"nested": {"environment": {}}})

    def test_snapshot_guard_accepts_expected_runtime_shape(self):
        runtime_evidence.assert_snapshot_safe(
            {
                "deployment": {"branch": "server/synology", "commit": "abc"},
                "service_health": {"mongodb": "running"},
                "containers": {
                    "api": {
                        "image": "librechat/example:test",
                        "network_names": ["synology_librechat"],
                        "mounts": [
                            {
                                "type": "volume",
                                "name": "librechat-data",
                                "destination": "/app/data",
                                "read_only": False,
                            }
                        ],
                    }
                },
            }
        )

    def test_write_snapshot_is_atomic_json(self):
        snapshot = {"schema": 1, "safety": {"raw_logs_exposed": False}}
        with tempfile.TemporaryDirectory() as directory:
            target = runtime_evidence.write_snapshot(directory, snapshot)
            with open(target, "r", encoding="utf-8") as handle:
                self.assertEqual(json.load(handle), snapshot)


if __name__ == "__main__":
    unittest.main()
