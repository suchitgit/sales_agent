"""DeepEval's LLM judge, backed by the Anthropic API — so no OpenAI key is needed and no local
model is used. The judge is a *third* model role: it grades, it never writes or scores in the spine."""
from __future__ import annotations
from deepeval.models import DeepEvalBaseLLM
from langchain_core.messages import HumanMessage
from .. import config


class AnthropicJudge(DeepEvalBaseLLM):
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or config.MODEL_READER
        super().__init__()

    def load_model(self):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=self.model_name, api_key=config.ANTHROPIC_API_KEY, temperature=0, max_tokens=800)

    def generate(self, prompt: str, schema=None) -> str:
        return self.load_model().invoke([HumanMessage(content=prompt)]).content

    async def a_generate(self, prompt: str, schema=None) -> str:
        return (await self.load_model().ainvoke([HumanMessage(content=prompt)])).content

    def get_model_name(self) -> str:
        return f"anthropic:{self.model_name}"
