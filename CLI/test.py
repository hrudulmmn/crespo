import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from summary import Summariser
import keystore
import os
import sys
import tempfile


# ─── Fixtures ────────────────────────────────────────────────────────────────

def make_file(path="main.py", ext="py", imports=None, classes=None, functions=None):
    """Fixture in gen_summ/extracted shape (file_name/ext keys)."""
    return {
        "file_name": path,
        "ext":       ext,
        "imports":   imports or [],
        "classes":   classes or {},
        "functions": functions or [],
        "struct":    [],
        "enum":      [],
    }

def make_batch_file(path="main.py", ext="py", imports=None, classes=None, functions=None):
    """Fixture in summarise_files_batch shape (path/lang keys)."""
    return {
        "path":      path,
        "lang":      ext,
        "imports":   imports or [],
        "classes":   classes or {},
        "functions": functions or [],
    }

def make_fallback():
    return {"Fallback": True, "file_name": "skip.py"}


# ─── summary.py: _parse_batch_response ───────────────────────────────────────

class TestParseBatchResponse:

    def setup_method(self):
        self.s = Summariser.__new__(Summariser)

    def test_normal_parse(self):
        raw = "0: Handles routing\n1: DB models\n2: Auth logic"
        result = self.s._parse_batch_response(raw, 3)
        assert result == ["Handles routing", "DB models", "Auth logic"]

    def test_file_prefix(self):
        raw = "FILE_0: Handles routing\nFILE_1: DB models"
        result = self.s._parse_batch_response(raw, 2)
        assert result == ["Handles routing", "DB models"]

    def test_missing_index_fills_fallback(self):
        raw = "0: Handles routing\n2: Auth logic"
        result = self.s._parse_batch_response(raw, 3)
        assert result[0] == "Handles routing"
        assert result[1] == "Summary unavailable."
        assert result[2] == "Auth logic"

    def test_empty_response(self):
        result = self.s._parse_batch_response("", 3)
        assert result == ["Summary unavailable."] * 3

    def test_garbage_lines_ignored(self):
        raw = "Sure! Here are summaries:\n0: Does routing\nHope this helps!"
        result = self.s._parse_batch_response(raw, 1)
        assert result == ["Does routing"]

    def test_out_of_range_index_ignored(self):
        raw = "0: Valid\n99: Out of range"
        result = self.s._parse_batch_response(raw, 1)
        assert result == ["Valid"]

    def test_single_file(self):
        raw = "0: Single file summary"
        result = self.s._parse_batch_response(raw, 1)
        assert result == ["Single file summary"]


# ─── summary.py: summarise_files_batch ───────────────────────────────────────

class TestSummariseFilesBatch:

    def _make_summariser(self, response_text):
        s = Summariser.__new__(Summariser)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = response_text
        s.client = MagicMock()
        s.client.chat.completions.create.return_value = mock_response
        s.systemprompt = "sys"
        s.PROMPTS = Summariser.PROMPTS
        return s

    def test_normal_batch(self):
        s = self._make_summariser("0: Does routing\n1: Handles DB")
        files = [make_batch_file("main.py"), make_batch_file("db.py")]
        result = s.summarise_files_batch(files)
        assert len(result) == 2
        assert result[0] == "Does routing"
        assert result[1] == "Handles DB"

    def test_single_file_batch(self):
        s = self._make_summariser("0: Entry point")
        result = s.summarise_files_batch([make_batch_file("app.py")])
        assert result == ["Entry point"]

    def test_413_splits_and_retries(self):
        s = Summariser.__new__(Summariser)
        s.systemprompt = "sys"
        s.PROMPTS = Summariser.PROMPTS
        call_count = [0]

        def mock_create(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("413 request too large")
            mock_resp = MagicMock()
            # each half will have 1-2 files
            mock_resp.choices[0].message.content = "0: First\n1: Second"
            return mock_resp

        s.client = MagicMock()
        s.client.chat.completions.create.side_effect = lambda **kw: mock_create(**kw)

        files = [make_batch_file("a.py"), make_batch_file("b.py"), make_batch_file("c.py")]
        result = s.summarise_files_batch(files)
        assert len(result) == 3
        assert "Summary unavailable." not in result

    def test_413_single_file_returns_fallback(self):
        s = Summariser.__new__(Summariser)
        s.systemprompt = "sys"
        s.PROMPTS = Summariser.PROMPTS
        s.client = MagicMock()
        s.client.chat.completions.create.side_effect = Exception("413 too large")
        result = s.summarise_files_batch([make_batch_file("huge.py")])
        assert result == ["Summary unavailable."]

    def test_429_retries_after_wait(self):
        s = self._make_summariser("0: Retry success")
        call_count = [0]

        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("429 rate limit")
            mock_resp = MagicMock()
            mock_resp.choices[0].message.content = "0: Retry success"
            return mock_resp

        s.client.chat.completions.create.side_effect = side_effect

        with patch("time.sleep") as mock_sleep:
            result = s.summarise_files_batch([make_batch_file("app.py")])
            mock_sleep.assert_called_once_with(10)
        assert result == ["Retry success"]

    def test_429_retry_also_fails_raises(self):
        s = Summariser.__new__(Summariser)
        s.systemprompt = "sys"
        s.PROMPTS = Summariser.PROMPTS
        s.client = MagicMock()
        s.client.chat.completions.create.side_effect = Exception("429 rate limit")

        with patch("time.sleep"):
            with pytest.raises(Exception):
                s.summarise_files_batch([make_batch_file("app.py")])

    def test_unknown_error_raises(self):
        s = Summariser.__new__(Summariser)
        s.systemprompt = "sys"
        s.PROMPTS = Summariser.PROMPTS
        s.client = MagicMock()
        s.client.chat.completions.create.side_effect = Exception("connection refused")

        with pytest.raises(Exception):
            s.summarise_files_batch([make_batch_file("app.py")])


# ─── generate.py: gen_summ batch fallback ────────────────────────────────────

class TestGenSummBatchFallback:

    def test_failed_batch_fills_unavailable(self):
        import generate
        import importlib

        extracted = [
            make_file("a.py", imports=["os"], functions=[{"name": "run", "params": ""}]),
            make_file("b.py", imports=["sys"], functions=[{"name": "main", "params": ""}]),
        ]

        mock_cli = MagicMock()
        advance_mock = MagicMock()
        mock_cli.summary_progress_context.return_value.__enter__ = MagicMock(return_value=advance_mock)
        mock_cli.summary_progress_context.return_value.__exit__ = MagicMock(return_value=False)

        # patch cli into generate's own namespace directly — no import needed
        with patch.object(generate, "cli", mock_cli, create=True), \
            patch("generate.Summariser") as MockSummariser:
            instance = MockSummariser.return_value
            instance.summarise_repo.return_value = "A test repo"
            instance.summarise_files_batch.side_effect = Exception("500 error")
            generate.gen_summ(extracted, "testrepo")

        import xml.etree.ElementTree as ET
        tree = ET.parse("summarised.xml")
        summaries = [f.get("s") for f in tree.findall(".//f")]
        assert all(s == "Summary unavailable." for s in summaries)


# ─── keystore.py ─────────────────────────────────────────────────────────────

class TestKeystore:

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        keystore.CONFIG_DIR  = Path(self.tmp)
        keystore.CONFIG_FILE = Path(self.tmp) / "config"
        os.environ.pop("CRESPO_GROQ_KEY", None)

    def teardown_method(self):
        os.environ.pop("CRESPO_GROQ_KEY", None)

    def test_save_and_load(self):
        keystore.save_key("test-key-123")
        assert keystore.load_key() == "test-key-123"

    def test_load_missing_file_returns_none(self):
        assert keystore.load_key() is None

    def test_get_key_provided_saves_and_returns(self):
        key = keystore.get_key(provided="new-key")
        assert key == "new-key"
        assert keystore.load_key() == "new-key"
        assert os.environ.get("CRESPO_GROQ_KEY") == "new-key"

    def test_get_key_no_args_reads_saved(self):
        keystore.save_key("saved-key")
        key = keystore.get_key()
        assert key == "saved-key"

    def test_get_key_env_takes_priority_over_saved(self):
        keystore.save_key("saved-key")
        os.environ["CRESPO_GROQ_KEY"] = "env-key"
        key = keystore.get_key()
        assert key == "env-key"

    def test_get_key_provided_overwrites_saved(self):
        keystore.save_key("old-key")
        key = keystore.get_key(provided="new-key")
        assert key == "new-key"
        assert keystore.load_key() == "new-key"

    def test_get_key_nothing_returns_none(self):
        assert keystore.get_key() is None

    def test_same_key_not_rewritten(self):
        keystore.save_key("same-key")
        mtime_before = keystore.CONFIG_FILE.stat().st_mtime
        keystore.get_key(provided="same-key")
        mtime_after = keystore.CONFIG_FILE.stat().st_mtime
        assert mtime_before == mtime_after


# ─── main.py: groq key block ─────────────────────────────────────────────────

class TestMainGroqKeyBlock:

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        keystore.CONFIG_DIR  = Path(self.tmp)
        keystore.CONFIG_FILE = Path(self.tmp) / "config"
        os.environ.pop("CRESPO_GROQ_KEY", None)

    def teardown_method(self):
        os.environ.pop("CRESPO_GROQ_KEY", None)

    def test_new_key_saved_when_none_stored(self):
        import main as main_mod
        with patch("sys.argv", ["crespo", "--groq", "brand-new-key"]):
            with patch.object(main_mod, "HAS_UI", True), \
                 patch("cli.print_header"), \
                 patch("cli.print_info") as mock_info:
                with pytest.raises(SystemExit):
                    main_mod.main()
        assert keystore.load_key() == "brand-new-key"
        mock_info.assert_called_with("✓ Groq key saved.")

    def test_same_key_reports_already_saved(self):
        keystore.save_key("existing-key")
        import main as main_mod
        with patch("sys.argv", ["crespo", "--groq", "existing-key"]):
            with patch.object(main_mod, "HAS_UI", True), \
                 patch("cli.print_header"), \
                 patch("cli.print_info") as mock_info:
                with pytest.raises(SystemExit):
                    main_mod.main()
        mock_info.assert_called_with("✓ This key is already saved.")

    def test_different_key_overwrites(self):
        keystore.save_key("old-key")
        import main as main_mod
        with patch("sys.argv", ["crespo", "--groq", "new-key"]):
            with patch.object(main_mod, "HAS_UI", True), \
                 patch("cli.print_header"), \
                 patch("cli.print_info"):
                with pytest.raises(SystemExit):
                    main_mod.main()
        assert keystore.load_key() == "new-key"

    def test_no_key_falls_back_to_structure(self):
        import main as main_mod
        with patch("sys.argv", ["crespo", ".", "--mode", "summarize"]):
            with patch.object(main_mod, "HAS_UI", True), \
                 patch("cli.print_header"), \
                 patch("cli.print_no_groq_key") as mock_warn, \
                 patch("walker.walk_dir", return_value=[]), \
                 patch("generate.gen_struct", return_value=Path("out.xml")), \
                 patch("counter.tok_count", return_value=(100, 10)), \
                 patch("cli.print_token_stats"), \
                 patch("cli.print_scan_start"), \
                 patch("cli.print_tree_classic"), \
                 patch("cli.run_with_progress"), \
                 patch("cli.print_security_result"), \
                 patch("os.path.exists", return_value=True):
                main_mod.main()
        mock_warn.assert_called_once()