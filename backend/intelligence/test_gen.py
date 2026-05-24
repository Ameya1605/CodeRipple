import logging
from typing import List, Dict, Any
from backend.indexer.schema import CodeChunk
from backend.query.llm_client import llm_client

logger = logging.getLogger(__name__)

TEST_GEN_PROMPT = """
You are a senior QA engineer. Generate a pytest skeleton for the following Python symbol.
The goal is to provide a regression test for a symbol impacted by upstream changes.

<symbol_context>
Name: {name}
Signature: {signature}
Contract: {contract}
Content:
{content}
</symbol_context>

<requirements>
1. Use `pytest`.
2. Mock any internal calls identified in the contract.
3. Provide a test case for the happy path and one for a common edge case.
4. Output ONLY the python code, no markdown wrapping.
</requirements>
"""

class TestGenerator:
    async def generate_skeleton(self, chunk: CodeChunk) -> str:
        prompt = TEST_GEN_PROMPT.format(
            name=chunk.symbol_name,
            signature=chunk.signature,
            contract=str(chunk.contract_data),
            content=chunk.content
        )
        
        response = await llm_client.generate(prompt)
        return response.strip()

test_generator = TestGenerator()
