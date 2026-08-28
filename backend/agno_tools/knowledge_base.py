import re
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# print(PROJECT_ROOT)
sys.path.append(str(PROJECT_ROOT))

from agno.knowledge.embedder.sentence_transformer import SentenceTransformerEmbedder
from agno.run import RunContext
from agno.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.vectordb.search import SearchType
from agno.knowledge.reranker.cohere import CohereReranker
from agno.db.sqlite import SqliteDb
from backend.config import CONTENTS_DB,LANCE_DB
from dotenv import load_dotenv

load_dotenv()


_knowledge_instance = None

CITATION_HEADER_RE = re.compile(
    r"\[FIR:\s*(?P<fir_number>[^\|]+?)\s*\|\s*station:\s*(?P<station>[^\|]+?)\s*\|\s*date_filed:\s*(?P<date_filed>[^\|]+?)\s*\|\s*page:\s*(?P<page>[^\|]+?)\s*\|\s*score:\s*(?P<score>[\d.]+)\]"
)


def get_knowledge() -> Knowledge:
    global _knowledge_instance
    if _knowledge_instance is None:
        contents_db = SqliteDb(db_file=CONTENTS_DB)
        _knowledge_instance = Knowledge(
            name="KSP FIR Knowledge Base",
            contents_db=contents_db,
            vector_db=LanceDb(
                uri=LANCE_DB,
                table_name="fir_reports",
                search_type=SearchType.hybrid,
                embedder=SentenceTransformerEmbedder(id="sentence-transformers/all-MiniLM-L6-v2",dimensions=384),
                reranker=CohereReranker(model="rerank-v3.5"),
            ),
            max_results=5,
        )
    return _knowledge_instance


def search_fir_knowledge(run_context:RunContext,query:str,fir_number:str=None):
    """Search FIR case records. Asks the user for a fir
       number if not provided"""
       
    if not fir_number:
        return "Please provide the corresponding FIR number."
    
    min_score = 0.45
    top_k = 5
    
    filters = {"fir_number": fir_number} if fir_number else None
    
    knowledge = get_knowledge()
    try:
        results = knowledge.search(query=query, filters=filters)
        print(f"[KNOWLEDGE BASE] Raw results: {results}\n")
    except Exception as e:
        raise Exception(e)
    
    if not results:
        return f"No matching content found for FIR {fir_number}."

    # filter by threshold first, then take top_k of what remains
    scored = [r for r in results if (r.reranking_score or 0)>=min_score]

    if not scored:
        return f"No sufficiently relevant content found for FIR {fir_number}. Please rephrase your query or check the FIR number."

    scored.sort(key=lambda r: r.reranking_score, reverse=True)
    top_results = scored[:top_k]

    formatted = []
    for r in top_results:
        meta = r.meta_data or {}
        station = meta.get("police_station", "unknown")
        date_filed = meta.get("date_filed", "unknown")
        page = meta.get("page", "unknown")

        formatted.append(
            f"[FIR: {fir_number} | station: {station} | date_filed: {date_filed} | page: {page} | score: {r.reranking_score:.3f}]\n{r.content}"
        )
        
        run_context.session_state['referenced_firs'].append({
            "police_station":station,
            "date":date_filed,
            "page_nos":page,
        })
        
    print(f"[RECORDS AGENT] Session state: {run_context.session_state}\n")

    return "\n\n---\n\n".join(formatted)


# def add_citations(run_output: RunOutput) -> None:
#     """
#     Deterministic post-hook: appends FIR source citations to the final answer
#     based on structured retrieval metadata — never relies on the model
#     mentioning sources itself.
#     """
#     print(f"[POST_HOOK] Run_output: {run_output} \n")
#     if not run_output.tools:
#         return

#     seen = set()
#     sources = []
#     for tool_exec in run_output.tools:
#         if tool_exec.tool_name != "search_fir_knowledge" or tool_exec.tool_call_error:
#             continue

#         result = tool_exec.result or ""
#         print(f"[POST_HOOK] Tool execution result: {result} \n")
#         for match in CITATION_HEADER_RE.finditer(result):
#             fir_number = match.group("fir_number").strip()
#             station = match.group("station").strip()
#             date_filed = match.group("date_filed").strip()
#             page = match.group("page").strip()

#             key = (fir_number, page)
#             if key in seen:
#                 continue
#             seen.add(key)
#             sources.append(f"{fir_number} — {station} (filed {date_filed}), page {page}")

#     if not sources:
#         return

#     citation_block = "\n\n**Referenced FIRs:**\n" + "\n".join(f"- {s}" for s in sources)
#     run_output.content = (run_output.content or "") + citation_block


if __name__ == "__main__":
    knowledge = get_knowledge()

    seed_firs = [
        {
            "path": str(PROJECT_ROOT  / "rag_case_reports" / "KSP_2023_0006.pdf"),
            "fir_number": "KSP/2023/0006",
            "police_station": "Mangaluru North",
            "date_filed": "2023-09-09",
        },
        {
            "path": str(PROJECT_ROOT / "rag_case_reports" / "KSP_2023_0014.pdf"),
            "fir_number": "KSP/2023/0014",
            "police_station": "Shivamogga Central",
            "date_filed": "2023-12-06",
        },
        {
            "path": str(PROJECT_ROOT  / "rag_case_reports" / "KSP_2023_0015.pdf"),
            "fir_number": "KSP/2023/0015",
            "police_station": "Kalaburagi North",
            "date_filed": "2023-10-20",
        },
        {
            "path": str(PROJECT_ROOT  / "rag_case_reports" / "KSP_2023_0016.pdf"),
            "fir_number": "KSP/2023/0016",
            "police_station": "Belagavi North",
            "date_filed": "2023-09-13",
        },
    ]

    for r in seed_firs:
        print(f"Ingesting {r['fir_number']}...")
        knowledge.insert(
            path=r["path"],
            name=f"FIR-{r['fir_number']}",
            metadata={
                "fir_number": r["fir_number"],
                "police_station": r["police_station"],
                "date_filed": r["date_filed"],
            },
        )
        print(f"Done: {r['fir_number']}")