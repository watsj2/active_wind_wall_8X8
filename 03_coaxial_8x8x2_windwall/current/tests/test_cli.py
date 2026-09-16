from __future__ import annotations

import contextlib
import io
import unittest

from main import parse_args


class CommandLineTests(unittest.TestCase):
    def test_application_accepts_no_runtime_mode_switches(self) -> None:
        parse_args([])

    def test_mock_option_is_rejected(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                parse_args(["--mock"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
