import argparse
import os
import sys
import time
from . import walker
from . import parse
from . import generate
from . import counter
from . import keystore
from importlib.resources import files as _res_files
from pathlib import Path

# import ui — handle missing gracefully
try:
    from . import cli
    HAS_UI = True
except ImportError:
    HAS_UI = False

def main():
    # ── find cresbee image ────────────────────────────────────────────────────
    cresbee = None
    try:
        cresbee = str(_res_files("crespo").joinpath("cresbee.png"))
    except Exception:
        cresbee = None

    # ── argument parsing ──────────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        prog="crespo",
        description="Crespo — Crisp repos. Sharp AI.",
        add_help=False
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "path",
        nargs="?",
        type=str,
        help="Root directory path of your codebase"
    )
    group.add_argument(
        "--git",
        type=str,
        help="GitHub URL to clone and analyse"
    )

    parser.add_argument(
        "--mode",
        choices=["structure", "summarize", "concat"],
        default="structure",
        help="Output mode (default: structure)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output filename (default: <reponame>_<mode>.xml)"
    )
    parser.add_argument(
        "--groq",
        type=str,
        default=None,
        help="Groq API key for summarize mode"
    )
    parser.add_argument(
        "--help", "-h",
        action="store_true",
        help="Show this help message"
    )

    args = parser.parse_args()

    # ── help ──────────────────────────────────────────────────────────────────
    if args.help:
        if HAS_UI:
            cli.print_header(cresbee)
            cli.print_usage()
        else:
            parser.print_help()
        sys.exit(0)

    if args.groq and (args.path is None and args.git is None):
        saved_key = keystore.load_key()  # read stored key directly, no side effects

        if args.groq == saved_key:
            if HAS_UI:
                cli.print_rule()
                cli.print_info("✓ This key is already saved.")
                cli.print_rule()
            else:
                print("✓ This key is already saved.")
        else:
            keystore.get_key(provided=args.groq)  # saves + injects into env
            if HAS_UI:
                cli.print_rule()
                cli.print_info("✓ Groq key saved.")
                cli.print_rule()
            else:
                print("✓ Groq key saved.")
        sys.exit(0)

    if args.path is None and args.git is None:
        if HAS_UI:
            cli.print_header(cresbee)
            cli.print_usage()
        else:
            parser.print_help()
    sys.exit(0)
        

    if HAS_UI:
        cli.print_header(cresbee)

    start_time = time.time()
    cloned = False

    # ── resolve source FIRST ──────────────────────────────────────────────────
    if args.git:
        if HAS_UI:
            cli.print_info(f"Cloning {args.git} ...")
        try:
            import git
            import tempfile

            temp_dir = tempfile.mkdtemp()
            git.Repo.clone_from(args.git, temp_dir, depth=1, single_branch=True)
            if HAS_UI:
                cli.print_info("Clone successful\n")
                cli.print_rule()
            path = temp_dir
            reponame = args.git.rstrip("/").split("/")[-1].replace(".git", "")
            cloned = True
        except Exception as e:
            if HAS_UI:
                cli.print_error(f"Clone failed: {e}")
            else:
                print(f"Error: Clone failed: {e}")
            sys.exit(1)
    else:
        path = args.path
        if not os.path.exists(path):
            if HAS_UI:
                cli.print_error(f"Path '{path}' does not exist!")
            else:
                print(f"Error: Path '{path}' does not exist!")
            sys.exit(1)
        reponame = Path(path).resolve().name

    mode = args.mode

    # ── scan ──────────────────────────────────────────────────────────────────
    if HAS_UI:
        cli.print_scan_start(args.git or path, mode)
    else:
        print(f"\nRepo: {Path(reponame).resolve()}  |  Mode: {mode}\nScanning...")

    valid_files = walker.walk_dir(path=path)

    if HAS_UI:
        cli.print_tree_classic([f["relpath"] for f in valid_files], root=reponame)
    else:
        for file in valid_files:
            print(f"  ✓  {file['relpath']}")

    # ── parse ─────────────────────────────────────────────────────────────────
    if HAS_UI:
        cli.run_with_progress(valid_files, label="Parsing files")
    else:
        print(f"\nParsing {len(valid_files)} files...")

    extracted = []
    for file in valid_files:
        signature = parse.extract_struct(
            Path(file["abspath"]).resolve(),
            mode,
            file["relpath"]
        )
        extracted.append(signature)

    # ── groq key for summarize ────────────────────────────────────────────────
    if mode == "summarize":
        saved_key = keystore.load_key()
        provided_key = args.groq

        if provided_key:
            if provided_key == saved_key:
                if HAS_UI:
                    cli.print_info("✓ Using saved Groq key.")
                groq_key = provided_key
            else:
                groq_key = keystore.get_key(provided=provided_key)  # saves + injects
                if HAS_UI:
                    cli.print_info("✓ New Groq key saved.")
                else:
                    print("✓ New Groq key saved.")
        else:
            groq_key = keystore.get_key()  # checks env + saved file

        if not groq_key:
            if HAS_UI:
                cli.print_no_groq_key()
            else:
                print("Warning: No Groq key found. Falling back to structure mode.")
            mode = "structure"

    # ── security scan ─────────────────────────────────────────────────────────
    secrets_count = sum(
        1 for e in extracted
        if isinstance(e, dict) and e.get("secrets_redacted", 0) > 0
    )
    if HAS_UI:
        cli.print_security_result(secrets_count, len(valid_files))
    else:
        if secrets_count:
            print(f"Warning: {secrets_count} file(s) had secrets redacted.")

    # ── generate ──────────────────────────────────────────────────────────────
    out_path = None

    try:
        if mode == "structure":
            out_path = generate.gen_struct(extracted, reponame)
        elif mode == "summarize":
            out_path = generate.gen_summ(extracted, reponame)
        elif mode == "concat":
            out_path = generate.gen_concat(valid_files, reponame=reponame)
    except Exception as e:
        error = str(e)
        if "429" in error:
            if HAS_UI:
                cli.print_groq_fallback()
            else:
                print("Groq Limit Hit: falling back to Structure mode.")
            mode = "structure"
            out_path = generate.gen_struct(extracted, reponame)
        else:
            raise

    # override output path if --output given
    if args.output and out_path:
        import shutil as _shutil
        _shutil.move(out_path, args.output)
        out_path = args.output

    # ── token stats ───────────────────────────────────────────────────────────
    original_tokens, output_tokens = counter.tok_count(valid_files, out_path)
    elapsed = round(time.time() - start_time, 1)

    if mode == "concat":
        if HAS_UI:
            cli.print_info(
                f"Concat mode preserves full source — "
                f"output is {output_tokens:,} tokens (XML overhead included)\n"
            )
            cli.print_loc(out_path)
        else:
            print(
                f"Concat mode preserves full source — "
                f"output is {output_tokens:,} tokens (XML overhead included)\n"
                f"Blueprint saved -> {out_path}"
            )

    else:
        if HAS_UI:
            cli.print_token_stats(
                original_tokens=original_tokens,
                output_tokens=output_tokens,
                mode=mode,
                output_file=out_path or "output.xml",
                elapsed=elapsed,
            )
        else:
            reduction = round((1 - output_tokens / max(original_tokens, 1)) * 100)
            print(f"\nDone!")
            print(f"Original:  {original_tokens:,} tokens")
            print(f"Output:    {output_tokens:,} tokens")
            print(f"Reduction: {reduction}%")
            print(f"Saved to:  {out_path}")

    # ── cleanup cloned repo ───────────────────────────────────────────────────
    if cloned:
        import shutil
        shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    main()