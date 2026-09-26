"""DeepEval's LLM judge, backed by the Anthropic API — so no OpenAI key is needed and no local
model is used. The judge is a *third* model role: it grades, it never writes or scores in the spine."""
from __future__ import annotations
from deepeval.models import DeepEvalBaseLLM
from langchain_core.messages import HumanMessage
from .. import config
from ..models import chat, text_of


class AnthropicJudge(DeepEvalBaseLLM):
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or config.MODEL_READER
        super().__init__(self.model_name)  # calls load_model() once and keeps it as self.model

    def load_model(self):
        return chat(self.model_name, 4000)

    def generate(self, prompt: str, schema=None) -> str:
        # DeepEval parses the JSON out of the text when it does not get a schema instance back
        return text_of(self.model.invoke([HumanMessage(content=prompt)]).content)

    async def a_generate(self, prompt: str, schema=None) -> str:
        return text_of((await self.model.ainvoke([HumanMessage(content=prompt)])).content)

    def get_model_name(self) -> str:
        return f"anthropic:{self.model_name}"
