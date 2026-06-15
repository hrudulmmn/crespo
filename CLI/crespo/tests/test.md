<div align="center">

<img src="./CLI/crespo/cresbee.png" alt="Cresbee" width="160"/>

<img src="./CLI/crespo/crespo-banner.png" alt="Crespo" width="560"/>

<br/>

<p>
  <img src="https://img.shields.io/badge/version-v1.0.9-64c88c?style=for-the-badge" />
  <img src="https://img.shields.io/pypi/v/crespo?style=for-the-badge&color=8c73d2&label=pypi" />
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/github/stars/hrudulmmn/crespo?style=for-the-badge&color=64c88c" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" />
</p>

<h2>Give AI the blueprint, not the code.</h2>

<p><i>Stop burning your context window on raw source files.<br/>Crespo extracts what matters — and compresses everything else.</i></p>

```bash
pip install crespo && crespo ./myproject
```

</div>

---

## The Problem

You paste a codebase into Claude. It hits the context limit.
You paste one file at a time. The AI loses the big picture.
You use Repomix. The AI reads 40,000 tokens linearly and still misses the architecture.

**Crespo solves this differently.**

Instead of concatenating raw files, Crespo uses **Tree-sitter AST parsing** to extract only the structural DNA of your repository — imports, classes, functions, module connections — and emits a compact XML blueprint. Same architectural understanding. A fraction of the tokens.

---

## Quickstart

```bash
pip install crespo
```

```bash
# analyse a local project
crespo ./myproject

# analyse directly from GitHub
crespo --git https://github.com/user/repo

# with AI summaries per file
crespo ./myproject --mode summary --groq YOUR_KEY

# full source, secrets redacted
crespo ./myproject --mode concat
```

That's it. Your blueprint is saved to `structure.xml`.

---

## How It Works

```
your repo
    │
    ▼
 walker          respects .gitignore · skips tests · skips build artifacts
    │
    ▼
 tree-sitter     real AST parse · 10 languages · no regex
    │
    ▼
 extractor       imports · classes · functions · structs · enums
    │
    ▼
 blueprint XML   compact · structured · LLM-ready
```

No heuristics. No regex scraping. Real language grammars via Tree-sitter — the same parser used by GitHub, Neovim, and Zed.

---

## Modes

<table>
<tr>
<th>Mode</th>
<th>What it produces</th>
<th>Token reduction</th>
<th>Best for</th>
</tr>
<tr>
<td><code>structure</code></td>
<td>AST skeleton — imports, classes, functions</td>
<td><strong>~87% avg</strong></td>
<td>Architecture review · LLM context · onboarding</td>
</tr>
<tr>
<td><code>summary</code></td>
<td>Structure + AI one-line descriptions per file</td>
<td><strong>~76% avg</strong></td>
<td>Deeper understanding · codebase reconstruction</td>
</tr>
<tr>
<td><code>concat</code></td>
<td>Full source in structured XML, secrets redacted</td>
<td><strong>~15–20%</strong></td>
<td>Passing full repos to LLMs safely</td>
</tr>
</table>

---

## Example Output

```xml
<?xml version='1.0' encoding='utf-8'?>
<repo n="kara" s="Gesture-controlled PDF viewer using PyQt6, MediaPipe, and OpenCV.">
  <meta>
    <dep>cv2,mediapipe,numpy,PyQt6,fitz,groq,markdown</dep>
  </meta>
  <files>
    <f p="Ui.py" e=".py"
       s="Main PyQt6 window coordinating PDF rendering, gesture input, and AI summarisation.">
      <imp>PyQt6,fitz,render,summarise,gesture,markdown</imp>
      <cls n="Window">
        <fn n="summary"    p="(self)" />
        <fn n="startGest"  p="(self, state)" />
        <fn n="gestZoom"   p="(self, state: int)" />
      </cls>
    </f>
    <f p="gesture.py" e=".py"
       s="MediaPipe hand tracking with gesture classification and debouncing.">
      <imp>mediapipe,cv2,numpy</imp>
      <cls n="GestureController">
        <fn n="detect"    p="(self, frame)" />
        <fn n="classify"  p="(self, landmarks)" />
      </cls>
    </f>
  </files>
</repo>
```

> Feed this to any LLM. It understands the entire codebase.

---

## Benchmarks

### Token Reduction — Structure Mode

> Measured against filtered source files. Tests, docs, and build artifacts excluded.

| Repo | Language | Raw tokens | Blueprint | Reduction |
|------|----------|-----------|-----------|-----------|
| Express | JS | 17,222 | 707 | **96%** |
| Axios | JS | 61,494 | 6,989 | **89%** |
| Urai | TS/JS | 17,418 | 2,304 | **87%** |
| Flask | Python | 77,402 | 13,848 | **82%** |
| Moodilist | Python | 8,580 | 1,396 | **84%** |
| Requests | Python | 49,556 | 9,585 | **81%** |
| Kara | Python | 4,667 | 934 | **80%** |
| FastAPI | Python | 145,606 | 124,993 | **14%** |
| **Average** | | | | **~87%** |

> FastAPI compresses less because it is primarily a framework — the preserved structure is genuinely useful, there is very little noise to discard.

---

### Accuracy — Structure Mode

> Evaluated by asking an LLM three questions from the blueprint alone with no access to the original source.

| Repo | Architecture | Dependencies | Entry point | Score |
|------|-------------|-------------|------------|-------|
| Axios | ✅ | ✅ | ✅ | **3 / 3** |
| Express | ✅ | ✅ | ✅ | **3 / 3** |
| Kara | ✅ | ✅ | ✅ | **3 / 3** |
| Moodilist | ✅ | ✅ | ✅ | **3 / 3** |
| FastAPI | ✅ | ✅ | ⚠️ | **2 / 3** |
| Flask | ✅ | ✅ | ⚠️ | **2 / 3** |
| Requests | ✅ | ✅ | ⚠️ | **2 / 3** |
| Urai | ✅ | ✅ | ⚠️ | **2 / 3** |
| **Average** | | | | **2.75 / 3** |

⚠️ Entry points are partially correct on framework-level repos (FastAPI, Flask) and convention-driven repos (Next.js) where the entry point is implicit rather than a single explicit file. Architecture and dependency accuracy is perfect across all tested repos.

---

## Usage Reference

```bash
# local directory — structure mode (default)
crespo ./myproject

# from GitHub
crespo --git https://github.com/user/repo

# summary mode — AI descriptions per file
crespo ./myproject --mode summary --groq YOUR_GROQ_KEY

# save your Groq key — never type it again
crespo --groq YOUR_GROQ_KEY

# concat mode — full source, secrets redacted
crespo ./myproject --mode concat

# custom output file
crespo ./myproject --output blueprint.xml
```

---

## Languages

| | | | | |
|---|---|---|---|---|
| Python | JavaScript | TypeScript | JSX | TSX |
| Rust | Go | Java | C | C++ |

More coming — Ruby, PHP, Swift, Kotlin.

---

## Security

Crespo scans and redacts secrets before writing any output. Nothing sensitive leaves your machine.

**Patterns covered:**

| Type | Example |
|------|---------|
| Quoted assignments | `api_key = "abc123"` → `api_key = "[REDACTED]"` |
| ENV style | `GROQ_KEY=abc123` → `GROQ_KEY=[REDACTED]` |
| Groq keys | `gsk_...` |
| OpenAI keys | `sk-...` |
| Anthropic keys | `sk-ant-...` |
| GitHub tokens | `ghp_...` |
| AWS keys | `AKIA...` |
| Slack tokens | `xox...` |

---

## Groq Setup

Summary mode uses [Groq](https://console.groq.com) to generate one-line descriptions per file and function. The free tier is more than enough.

```bash
# pass once — saved to ~/.crespo/config
crespo --groq YOUR_KEY

# all future summary runs pick it up automatically
crespo ./myproject --mode summary
```

Your key is stored locally at `~/.crespo/config` and never sent anywhere except Groq's API.

---

## vs Repomix

| | Repomix | Crespo |
|---|---|---|
| Approach | Concatenates raw files | AST-based extraction |
| Output | Flat text dump | Structured XML blueprint |
| Token efficiency | Minimal reduction | ~87% avg reduction |
| AI comprehension | Linear read of all code | Architecture-first understanding |
| Secret redaction | ✅ | ✅ |
| Respects .gitignore | ✅ | ✅ |
| Skips test files | ❌ | ✅ |
| Function summaries | ❌ | ✅ (summary mode) |
| Multi-language AST | ❌ | ✅ 10 languages |

> Repomix packs your repo. Crespo maps it.

---

## Roadmap

- **Graph mode** — interactive HTML dependency visualisation
- **More languages** — Ruby, PHP, Swift, Kotlin
- **`.crespoignore`** — custom ignore rules
- **More aggressive compression** — configurable depth

---

## Contributing

Contributions are welcome. Open an issue or PR for:
- New output modes
- Better parsing or extraction
- Additional language support
- Bug reports

---

## License

MIT © [Hrudul Krishna K V](https://github.com/hrudulmmn)

---

<div align="center">
<br/>
<img src="./CLI/crespo/cresbee.png" width="60"/>
<br/>
<sub>Built by a CS student who kept hitting Claude's free limit.</sub>
<br/>
<sub>
  <a href="https://github.com/hrudulmmn/crespo">GitHub</a> ·
  <a href="https://pypi.org/project/crespo">PyPI</a>
</sub>
</div>