---
mode: 'agent'
description: 'Search for similar code before writing anything new — prevent duplication.'
---

# RAG Code Search

## RAG Search — Before Writing New Code
1. Describe what you want to build in 5-10 words.
2. Run: `ag rag "<description>"` or use `semantic_search` in the workspace.
3. Evaluate results:
   - **High relevance (>0.8)**: Reuse or extend the existing code — do not duplicate.
   - **Medium relevance (0.5-0.8)**: Review the match; adapt if patterns align.
   - **Low relevance (<0.5)**: Proceed with new implementation, following project conventions.
4. Reference the matched file and function in your implementation comments.
