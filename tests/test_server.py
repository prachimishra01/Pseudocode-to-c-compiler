"""
Integration tests for server.py HTTP server and API endpoints.
"""

import unittest
import urllib.request
import json
import threading
import time
from http.server import ThreadingHTTPServer
from server import CompilerRequestHandler


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 5092
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", cls.port), CompilerRequestHandler)
        cls.server_thread = threading.Thread(
            target=cls.httpd.serve_forever,
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_get_index(self):
        url = f"http://127.0.0.1:{self.port}/"
        with urllib.request.urlopen(url, timeout=3) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("Pseudocode to C Compiler", body)
            self.assertIn("cCodeDisplay", body)

    def test_get_examples(self):
        url = f"http://127.0.0.1:{self.port}/api/examples"
        with urllib.request.urlopen(url, timeout=3) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("examples", data)
            self.assertEqual(len(data["examples"]), 20)

    def test_post_compile(self):
        url = f"http://127.0.0.1:{self.port}/api/compile"
        req = urllib.request.Request(
            url,
            data=json.dumps({"code": "START\nDECLARE age: INTEGER\nage = 21\nPRINT age\nEND"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data["success"])
            self.assertIn("int age;", data["c_code"])
            self.assertIn("printf(\"%d\\n\", age);", data["c_code"])
            self.assertTrue(len(data["explanation"]) > 0)

    def test_post_compile_error(self):
        url = f"http://127.0.0.1:{self.port}/api/compile"
        req = urllib.request.Request(
            url,
            data=json.dumps({"code": "START\nIF x > 10 THEN\nPRINT x\nEND"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                self.fail("Expected 400 Bad Request for invalid syntax")
        except urllib.error.HTTPError as err:
            self.assertEqual(err.code, 400)
            data = json.loads(err.read().decode("utf-8"))
            self.assertFalse(data["success"])
            self.assertIn("error", data)
            self.assertIn("Missing 'END IF'", data["error"]["message"])


if __name__ == "__main__":
    unittest.main()
