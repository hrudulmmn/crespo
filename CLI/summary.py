from groq import Groq
import os



class Summariser():
    PROMPTS = {
    
        "repo": """Describe this codebase in ONE sentence max 20 words.
        Include what it does, primary stack, core features.
        Repo: {repo_name}
        Dependencies: {deps}
        Files: {files}
        Return only the summary.""",

        "file": """Describe this file's responsibility in ONE sentence max 15 words.
        File: {path}
        Language: {lang}
        Imports: {imports}
        Classes: {classes}
        Functions: {functions}
        Return only the summary.""",

        "class": """Describe what this class represents and manages in ONE sentence max 15 words.
        Class: {name}
        Language: {lang}
        Methods:
        {method_signatures}
        Return only the summary.""",

        "function": """Describe this {lang} function in ONE sentence max 20 words.
        Start with action verb. Include inputs, outputs, side effects.
        Signature: {signature}
        Body:
        {body}
        Return only the summary sentence."""

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
                    DESCRIPTION: [2 sentences maximum. Explain key responsibilities, important classes/functions, architecture decisions, and relationships with other parts of the project.]

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
            model="llama-3.3-70b-versatile",
            messages=[{
                "role":"system",
                "content":self.systemprompt
            },
            {
                "role":"user",
                "content":userPrompt
            }],temperature=0.1,max_tokens=300
        )
        return response.choices[0].message.content.strip()
    
    def summarise_file(self,path,lang,imports,classes,functions):
        userPrompt = self.get_prompt("file",path=path,lang=lang,imports=imports,classes=classes,functions=functions)
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role":"system",
                "content":self.systemprompt
            },
            {
                "role":"user",
                "content":userPrompt
            }],temperature=0.1,max_tokens=300
        )
        return response.choices[0].message.content.strip()
    
    def summarise_class(self,name,lang,method_signature):
        userPrompt = self.get_prompt("class",name=name,lang=lang,method_signatures=method_signature)
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role":"system",
                "content":self.systemprompt
            },
            {
                "role":"user",
                "content":userPrompt
            }],temperature=0.1,max_tokens=300
        )
        return response.choices[0].message.content.strip()
    
    def summarise_fun(self,lang,signature,body):
        userPrompt = self.get_prompt("function",lang=lang,signature=signature,body=body)
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role":"system",
                "content":self.systemprompt
            },
            {
                "role":"user",
                "content":userPrompt
            }],temperature=0.1,max_tokens=300
        )
        return response.choices[0].message.content.strip()