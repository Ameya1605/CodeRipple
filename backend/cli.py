import asyncio
import argparse
import sys
from backend.indexer.schema import CodeChunk
from backend.retrieval.retriever import retrieve_dependents, build_call_graph_summary
from backend.query.prompt_builder import build_query_prompt
from backend.query.llm_client import call_llm_streaming
from backend.query.response_validator import validate_response
from backend.bot.pr_commenter import PRCommenter

async def run_analyze(repo_id: str, symbol_name: str):
    print(f"Analyzing {symbol_name} in {repo_id}...", file=sys.stderr)
    
    chunk = CodeChunk(
        chunk_id=f"{repo_id}:{symbol_name}",
        repo_id=repo_id,
        file_path="mock.py",
        symbol_type="func",
        symbol_name=symbol_name,
        qualified_name=symbol_name,
        start_line=1,
        end_line=10,
        signature=f"def {symbol_name}()",
        content="pass",
        language="python"
    )
    
    retrieved = await retrieve_dependents(chunk)
    graph_summary = await build_call_graph_summary(symbol_name, repo_id)
    
    messages = build_query_prompt(chunk, "CLI Triggered Analysis", retrieved, graph_summary)
    
    full_response = ""
    async for text_delta in call_llm_streaming(messages):
        full_response += text_delta
        
    validated = validate_response(full_response, retrieved)
    markdown = PRCommenter.render_markdown(validated)
    print(markdown)

def main():
    parser = argparse.ArgumentParser(description="Dependency Impact Analyzer CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--repo", required=True)
    analyze_parser.add_argument("--symbol", required=True)
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        asyncio.run(run_analyze(args.repo, args.symbol))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
