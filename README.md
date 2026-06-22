<div align="center">
<p align="center">
  <img src="./CLI/crespo/cresbee.png" alt="Cresbee" width="200">
  <img src="./CLI/crespo/crespo-banner.png" alt="Crespo" width="600" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/pypi/v/crespo?style=for-the-badge&color=2EA44F" alt="Version" />
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/pepy/dt/crespo?style=for-the-badge&color=2EA44F" alt="Downloads" />
  <img src="https://img.shields.io/github/stars/hrudulmmn/crespo?style=for-the-badge" alt="Stars" />
</p>

<p align="center">
  <h2>Crisp Repos, Sharp AI.</h2>

<p><i>Built <b>Crespo</b> because I kept hitting the context limit on multiple AI's.</i></p>

```bash
pip install crespo && crespo ./myproject
```
</div>

---

## The Problem

When we paste the whole codebase to any LLM either it dosent understand fully or we hit the token limit. But when we try to give the context file by file it can't understand the relation between files and all these requires limited tokens that are wasted on making the AI understand the codebase rather than doing work.

**Crespo solves this differently.**

Instead of concatenating raw files, Crespo uses **Tree-sitter AST parsing** to extract only the structural aspects of your repository such as  imports, classes, functions, module connections and generates a compact XML blueprint. 
This helps the AI understand better at the cost of a fraction of tokens.

---

## Usage

```bash
# Structure mode (default)
crespo ./myproject

# Summary mode — requires Groq key
crespo ./myproject --mode summary --groq YOUR_KEY

# Save your Groq key for future runs
crespo --groq YOUR_KEY

# Concat mode — full source, redacted
crespo ./myproject --mode concat

# Analyse a GitHub repo directly
crespo --git https://github.com/user/repo

# Custom output filename
crespo ./myproject --output blueprint.xml
```

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

Tree-sitter handles language grammar without failing on edge cases where regex fails.

---

## Demo

<div align="center">
  <img src="./CLI/crespo/demovid2.gif" alt="Cresbee" width="1000">
</div>

---

## Modes

| Mode | What it produces | Best for |
|---|---|---|
| `structure` | AST skeleton — imports, classes, functions | When you want LLM to understand the codebase |
| `summary` | Structure + AI one-line descriptions per file | When you want descriptions for files |
| `concat` | Full source, secrets redacted, in structured XML | When you want to make changes in code |

---

## Languages supported

Python · JavaScript · TypeScript · JSX · TSX · Rust · Go · Java · C · C++

---

## Example output

```xml
<?xml version='1.0' encoding='utf-8'?>
<repo n="kara" s="Gesture-controlled PDF viewer using PyQt6, MediaPipe, and OpenCV.">
  <meta>
    <dep>cv2,mediapipe,numpy,PyQt6,fitz,groq,markdown</dep>
  </meta>
  <files>
    <f p="Ui.py" e=".py" s="Main PyQt6 window coordinating PDF rendering, gesture input, and AI summarisation.">
      <imp>PyQt6,fitz,render,summarise,gesture,markdown</imp>
      <cls n="Window">
        <fn n="summary" p="(self)" />
        <fn n="startGest" p="(self, state)" />
        <fn n="gestZoom" p="(self, state: int)" />
      </cls>
    </f>
    <f p="gesture.py" e=".py" s="MediaPipe hand tracking with gesture classification and debouncing.">
      <imp>mediapipe,cv2,numpy</imp>
      <cls n="GestureController">
        <fn n="detect" p="(self, frame)" />
        <fn n="classify" p="(self, landmarks)" />
      </cls>
    </f>
  </files>
</repo>
```

---

## Benchmarks

Tested on real open-source repositories. Structure accuracy evaluated by asking an LLM three questions from the blueprint alone — no access to the original source.

### Structure mode accuracy

| Repo | Components & connections | Dependencies | Entry point | Score |
|---|---|---|---|---|
| Axios | ✅ correct and specific | ✅ correct and specific | ✅ correct and specific | 3/3 |
| Express | ✅ correct and specific | ✅ correct and specific | ✅ correct and specific | 3/3 |
| Kara | ✅ correct and specific | ✅ correct and specific | ✅ correct and specific | 3/3 |
| Moodilist | ✅ correct and specific | ✅ correct and specific | ✅ correct and specific | 3/3 |
| Requests | ✅ correct and specific | ✅ correct and specific | ⚠️ partially correct | 2/3 |
| Urai | ✅ correct and specific | ✅ correct and specific | ⚠️ partially correct | 2/3 |
| FastAPI | ✅ correct and specific | ✅ correct and specific | ⚠️ partially correct | 2/3 |
| Flask | ✅ correct and specific | ✅ correct and specific | ⚠️ partially correct | 2/3 |
| **Average** | | | | **2.75 / 3** |

⚠️ Entry points are partially correct on framework-level repos (FastAPI, Flask) and convention-driven repos (Next.js) where the entry point is implicit rather than explicit. Architecture and dependency accuracy remains perfect across all tested repos.

### Token reduction — structure mode

| Repo | Raw tokens | Blueprint tokens | Reduction |
|---|---|---|---|
| Kara | ~4,667 | ~934 | ~80% |
| Moodilist | ~8,580 | ~1,396 | ~84% |
| Axios | ~61,494 | ~6,989 | ~89% |
| Express | ~17,222 | ~707 | ~96% |
| FastAPI | ~145,606 | ~124,993 | ~14% |
| Flask | ~77,402 | ~13,848 | ~82% |
| Requests | ~49,556 | ~9,585 | ~81% |
| Urai | ~ 17,418 | ~2,304 | ~87% |
| **Average** | | | **~86%** |


> FastAPI (14% reduction) excluded from average — as a 
> framework repo its structure IS the content. 
> Crespo correctly preserves it rather than discarding it.

Framework-heavy repos compress slightly less because the preserved structure is genuinely useful as there is less noise to discard.


Token Counting is done using `tiktoken` python library.


**Compression Depends on Repo Type**

---

## Security

Before writing anything in the concat mode, <b>crespo</b> scans the file body for secrets and then replaces them with `[REDACTED]`.

It is still not perfect but captures common patterns such as:

- Quoted assignments — `api_key = "..."`, `token: '...'`
- Raw `.env` style — `GROQ_KEY=abc123`
- Known key prefixes — Groq (`gsk_`), OpenAI (`sk-`), Anthropic (`sk-ant-`), GitHub (`ghp_`), AWS (`AKIA`), Slack (`xox`)

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

## Roadmap

- Something for Humans coming soon!
- More aggressive compression preset
- More language support (Ruby, PHP, Swift, Kotlin)
- `.crespoignore` support

---

## Troubleshooting
 
### `crespo: command not found`
 
This usually means Crespo was installed successfully, but the executable isn't on your system `PATH`.
 
**Verify installation**
 
```bash
python -m pip show crespo
```
 
If Crespo appears in the output but the `crespo` command still isn't recognized, it's a `PATH` issue 

Follow the steps below for your OS.
 
**Windows**
 
Add your Python `Scripts` directory to `PATH` (typically):
 
```text
C:\Users\<you>\AppData\Local\Programs\Python\Python3x\Scripts
```
 
Restart your terminal afterwards.
 
**macOS / Linux**
 
Find your user scripts directory:
 
```bash
python3 -m site --user-base
```
 
Then add its `bin` folder to your shell configuration:
 
```bash
export PATH="$HOME/.local/bin:$PATH"
```
 
Restart your shell and try again.
 
**Multiple Python installations**
 
If you have multiple Python versions installed, make sure installation and execution use the same interpreter. Check which `python`/`pip` you're actually using:
 
```bash
where python      # Windows
which -a python3  # macOS / Linux
```
 
Reinstall using that same interpreter explicitly if needed:
 
```bash
python -m pip install --force-reinstall crespo
```
 
**Recommended: use `pipx`**
 
For CLI tools, `pipx` avoids most PATH-related issues entirely:
 
```bash
pipx install crespo
crespo ./myproject
```

---

## Contributing

Contributions are welcome. If you have ideas for new output modes, better parsing, or additional language support, open an issue or PR.

---

## License

MIT © [Hrudul Krishna K V](https://github.com/hrudulmmn)

---

<div align="center">
<br/>
<img src="./CLI/crespo/cresbee.png" width="60"/>
<br/>
<sub>Built by a CS student who kept hitting AI's free limit.</sub>
<br/>
<sub>
  <a href="https://github.com/hrudulmmn/crespo">GitHub</a> ·
  <a href="https://pypi.org/project/crespo">PyPI</a>
</sub>
</div>
