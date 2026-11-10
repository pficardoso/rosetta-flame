"""Analyze a submitted text and suggest Weak Spots and related Topics.

``analyze_text`` is the feature entry point. The CLI (and later the web app) only depend
on this function and on the result classes below.
"""
import asyncio
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query


_SYSTEM_PROMPT = "Your a english text analysis agent that will work as an english teacher, whose jobs" \
"is to analyse students text and identify their errors and weaknesses. When naming this errors and weaknesses" \
"you should use topics similar to those given in an English class." \
"You are going to analyze a submitted text and identify weak spots the writter seems to have. " \
"Weak spots are areas where the writer shows weaknesses or lacks clarity, and clearly needs to improve." \
"The weak spots should not be too specific nor too generic. They should be similar to a topic given in a english class." \
"Examples of good weak spots: present continuous, past simple, adverbs, confusing rather with than, vocabulary about houses" \
"Examples of bad weak spots: typos, very specific word choices, overly broad topics"

class TextAnalysisAgent:
    
    def __init__(self):
        # Initialize the agent with necessary configurations
        self.system_prompt = _SYSTEM_PROMPT
        self.options = ClaudeAgentOptions(
            model="claude-sonnet-5",
            system_prompt=self.system_prompt,
        )

    async def run(self, text: str):
        async for message in query(
            prompt=f"Analyze the following text and suggest weak spots:\n \"{text}\".",
            options=self.options
        ):
            if isinstance(message, ResultMessage) and not message.is_error:
                print(message.result)

def analyze_text(text: str) -> dict:
    # Placeholder implementation

    # Start an agent
    agent = TextAnalysisAgent()
    # Read the the text 
    asyncio.run(agent.run(text))

    return {"text": text, "weak_spots": [], "related_topics": []}



