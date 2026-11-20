import json
import unittest
from unittest.mock import Mock, patch

import llama_autostart


class PortTests(unittest.TestCase):
    def test_port_status_checks_requested_ports(self):
        with patch("llama_autostart.socket.socket") as socket_type:
            socket = socket_type.return_value.__enter__.return_value
            socket.connect_ex.return_value = 0
            result = llama_autostart.port_status(ports=(9931, 11434))

        self.assertEqual(result, {"9931": True, "11434": True})
        self.assertEqual(socket.settimeout.call_count, 2)


class OllamaTests(unittest.TestCase):
    def test_ollama_facts_collects_service_environment_and_ps(self):
        ps_script_output = json.dumps({
            "service": {
                "name": "Ollama",
                "state": "Running",
                "start_mode": "Automatic",
                "path": "C:\\Tools\\ollama.exe",
                "process_id": 1234,
            },
            "process_running": True,
            "processes": [{"ProcessId": 1234, "ExecutablePath": "C:\\Tools\\ollama.exe"}],
            "host": "127.0.0.1:11434",
            "models": "D:\\OllamaModels",
        })
        ps_result = Mock(
            returncode=0,
            stdout="NAME ID SIZE\nllama3 x 4GB",
            stderr="",
        )
        with patch("llama_autostart.powershell",
                   return_value=Mock(returncode=0, stdout=ps_script_output)), \
             patch("llama_autostart.shutil.which", return_value="C:\\Tools\\ollama.exe"), \
             patch("llama_autostart.run_command", return_value=ps_result):
            result = llama_autostart.ollama_facts()

        self.assertEqual(result["service"]["state"], "Running")
        self.assertTrue(result["process_running"])
        self.assertEqual(result["host"], "127.0.0.1:11434")
        self.assertEqual(result["models"], "D:\\OllamaModels")
        self.assertIn("llama3", result["ps"]["output"])


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.facts = {
            "generated_at": "2026-11-20T00:00:00+00:00",
            "host": {
                "computerName": "TEST-PC",
                "os": {"Caption": "Microsoft Windows 11"},
                "cpu": {"Name": "Test CPU"},
                "memory": {"TotalVisibleMemorySize": "16000000"},
                "gpu": [{"Name": "Test GPU"}],
            },
            "cuda": {"CUDA_PATH": None, "nvidia_smi": None, "nvcc": None},
            "ports": {str(port): False for port in (9931, 11434, 1234, 3000, 8080, 8000)},
            "runners": {
                "llama_cpp": {"reachable": False, "status": None},
                "ollama": {"reachable": False, "status": None},
                "lm_studio": {"reachable": False, "status": None},
                "open_webui": {"reachable": False, "status": None},
                "vllm": {"reachable": False, "status": None},
            },
            "ollama": {
                "executable": "C:\\Tools\\ollama.exe",
                "service": {"name": "Ollama", "state": "Running"},
                "process_running": True,
                "host": "127.0.0.1:11434",
                "models": "D:\\OllamaModels",
                "ps": {"returncode": 0, "output": "NAME ID SIZE", "error": ""},
            },
            "llama_cpp": {
                "task": "Ready",
                "endpoint": "http://127.0.0.1:9931",
                "executable": "C:\\tools\\llama.exe",
                "log": "C:\\Tools\\llama-server.log",
            },
        }

    def test_markdown_report_contains_answer_first_findings(self):
        report = llama_autostart.markdown_report(self.facts)
        self.assertIn("# AI Workstation Diagnostic Report", report)
        self.assertIn("## Findings", report)
        self.assertIn("llamacpp.server_stopped", report)

    def test_redaction_replaces_app_profile_and_username(self):
        with patch.dict("os.environ", {"USERNAME": "Jane", "USERPROFILE": "C:\\Users\\Jane"}):
            result = llama_autostart.redact("Jane is under C:\\Users\\Jane")
        self.assertNotIn("Jane", result)
        self.assertIn("<user>", result)


if __name__ == "__main__":
    unittest.main()
