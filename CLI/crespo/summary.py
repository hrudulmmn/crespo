from groq import Groq
import os
from . import cli



class Summariser():
    PROMPTS = {
    
        "repo": """Describe this codebase in 2 sentence max 50 words.
        Include what it does, primary stack, core features.
        Repo: {repo_name}
        Dependencies: {deps}
        Files: {files}
        Return only the summary.""",

        "file": """Describe this file's responsibility in 2-3 sentences max 50 words.
        Include what it does using technical terms,core features.
        File: {path}
        Language: {lang}
        Imports: {imports}
        Classes: {classes}
        Functions: {functions}
        Return only the summary.""",
        "files_batch": """Summarize each file below. For each write 1-2 sentences max 40 words.
            Use this format strictly:
            FILE_INDEX: <summary>
            One line per file, no extra text.

            Files:
            {files_block}

            Return only the indexed summaries.""",

        }
    def __init__(self):
            self.client = Groq(api_key=os.getenv('CRESPO_GROQ_KEY'))
            self.systemprompt = """You are an expert senior software engineer and technical writer specializing in code analysis and distillation.

                        Your task is to analyze a single file from a codebase and create a highly concise, information-dense summary optimized for LLM consumption.

                        Rules:
                        - Be extremely precise and technical
                        - Focus on purpose, responsibilities, and key implementations
                        - Never use phrases like "This file", "This module", "The code contains"
                        - Assume the reader is an experienced developer
                        - Prioritize signal over politeness
                        - Keep summaries short but information-rich

                        Output Format (strictly follow this):
                        [2 sentences maximum. Explain key responsibilities, important classes/functions, architecture decisions, and relationships with other parts of the project.]

                        Style Guidelines:
                        - Use professional but natural language
                        - Highlight important patterns (e.g., threading, real-time processing, event-driven, etc.)
                        - Mention key technologies only if they are central
                        - If the file is low value (utils, config, tests), keep DESCRIPTION very short
                            """


    def get_prompt(self,type:str,**kwargs):
        template = self.PROMPTS.get(type)
        if not template:
            raise ValueError(f"Unknown Prompt type:{type}")
        return template.format(**kwargs)

    def summarise_repo(self,repo_name,deps,files):
        userPrompt = self.get_prompt("repo",repo_name=repo_name,files = files,deps=deps)
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role":"system",
                "content":self.systemprompt
            },
            {
                "role":"user",
                "content":userPrompt
            }],temperature=0.1,max_tokens=50
        )
        return response.choices[0].message.content.strip()
    
    def summarise_file(self,path,lang,imports,classes,functions):
        userPrompt = self.get_prompt("file",path=path,lang=lang,imports=imports,classes=classes,functions=functions)
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role":"system",
                "content":self.systemprompt
            },
            {
                "role":"user",
                "content":userPrompt
            }],temperature=0.1,max_tokens=50
        )
        return response.choices[0].message.content.strip()
    
    def summarise_files_batch(self, files_data: list[dict]) -> list[str]:
        lines = []
        for i, f in enumerate(files_data):
            lines.append(
                f"[{i}] File: {f['path']} | Lang: {f['lang']} | "
                f"Imports: {f['imports']} | "
                f"Classes: {list(f['classes'].keys()) if f['classes'] else []} | "
                f"Functions: {[fn['name'] for fn in f['functions']] if f['functions'] else []}"
            )
        files_block = "\n".join(lines)
        user_prompt = self.get_prompt("files_batch", files_block=files_block)

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": self.systemprompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=60 * len(files_data),
            )
            raw = response.choices[0].message.content.strip()
            return self._parse_batch_response(raw, len(files_data))

        except Exception as e:
            error = str(e)

            # ── token limit: split batch in half and retry ────────────────────
            if "413" in error or "too large" in error.lower() or "context" in error.lower():
                if len(files_data) == 1:
                    # can't split further — return fallback for this single file
                    return ["Summary unavailable."]
                mid = len(files_data) // 2
                left  = self.summarise_files_batch(files_data[:mid])
                right = self.summarise_files_batch(files_data[mid:])
                return left + right

            # ── rate limit: wait and retry once ──────────────────────────────
            elif "429" in error:
                import time
                time.sleep(10)
                try:
                    response = self.client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": self.systemprompt},
                            {"role": "user",   "content": user_prompt},
                        ],
                        temperature=0.1,
                        max_tokens=60 * len(files_data),
                    )
                    raw = response.choices[0].message.content.strip()
                    return self._parse_batch_response(raw, len(files_data))
                except Exception:
                    # retry also failed — raise so gen_summ can catch and fallback to structure
                    raise

            else:
                raise


    def _parse_batch_response(self, raw: str, expected: int) -> list[str]:
        """Parse 'FILE_INDEX: summary' lines back into an ordered list."""
        results = [""] * expected
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" not in line:
                continue
            idx_part, _, summary = line.partition(":")
            # handle both "FILE_0" and "0" prefixes
            idx_str = idx_part.strip().lstrip("FILE_").lstrip("FILE").strip()
            try:
                idx = int(idx_str)
                if 0 <= idx < expected:
                    results[idx] = summary.strip()
            except ValueError:
                continue
        # fill any unparsed slots with a fallback
        return [s if s else "Summary unavailable." for s in results]
        