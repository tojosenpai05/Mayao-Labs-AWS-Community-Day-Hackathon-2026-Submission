# Solution 1: RAG-Based Document Q&A System

**Pain Point Addressed:** Documents exist but can't be found + Slow decision-making  
**Type:** Technical Architecture Solution  
**Maturity:** Production-proven (multiple real-world deployments)

---

## What It Is

Retrieval-Augmented Generation (RAG) is a technique that combines a document retrieval engine with a large language model. Instead of a user searching for keywords, they ask a question in natural language. The system finds the most relevant document chunks, passes them to the LLM, and the LLM generates a grounded, cited answer.

---

## Key Research

### Deltek + AWS GenAIIC — Government Solicitation Documents (2024)
**Source:** [AWS Machine Learning Blog](https://aws.amazon.com/blogs/machine-learning/how-deltek-uses-amazon-bedrock-for-question-and-answering-on-government-solicitation-documents/)

Deltek, serving 30,000+ government contracting clients, built a RAG system using Amazon Textract, Amazon OpenSearch, and Amazon Bedrock. Key finding: applying RAG across **multiple temporally related documents** (e.g., a policy issued in 2021, amended in 2023, updated in 2025) requires chronological awareness — otherwise the system returns an answer that was correct once but is now outdated. This maps directly to the government SOP/circular problem.

Architecture used:
- Amazon Textract → extract text from PDFs
- Amazon OpenSearch → vector + keyword hybrid search index
- Amazon Bedrock (Claude/Titan) → answer generation with citations

### RAG for Domain-Specific Q&A — CMU/Pittsburgh Case Study (arXiv, 2024)
**Source:** [arxiv.org/html/2411.13691v1](https://arxiv.org/html/2411.13691v1)

Built a RAG system over 1,800+ government and institutional web pages. Used a hybrid BM25 + FAISS retriever with a reranker. Results:
- F1 score improved from **5.45% (no RAG)** to **42.21% (with RAG)**
- Recall: **56.18%**

Key insight: combining sparse retrieval (BM25) with dense vector retrieval (FAISS) significantly outperforms either alone — especially for domain-specific institutional language.

### An Empirical Evaluation of RAG for Policy Document QA (arXiv, 2026)
**Source:** [arxiv.org/abs/2601.15457](https://arxiv.org/abs/2601.15457)

Compared Basic RAG vs Advanced RAG on policy documents:
- Basic RAG: faithfulness score **0.621** (vs 0.347 baseline)
- Advanced RAG: faithfulness **0.797**

Key finding: domain-specific fine-tuning of the retriever improves retrieval metrics, but does not always improve end-to-end QA — hallucinations increase when relevant documents are absent from the corpus. **Confidence calibration** (knowing when to say "I don't know") is critical for policy use cases.

---

## AWS Implementation Stack

```
Documents (PDF, DOCX, scanned) 
    → Amazon Textract (OCR + structure extraction)
    → Amazon Bedrock Knowledge Bases (chunking + embedding)
    → Amazon OpenSearch Serverless (vector store)
    → Amazon Bedrock (Claude 3 / Nova) (answer generation)
    → API Gateway + Lambda (API layer)
    → Amplify / React (frontend)
```

---

## Strengths for Government Context

- Works on top of existing document repositories — no migration required
- Supports PDFs, Word, scanned documents, web pages
- Cites sources with every answer — auditability built in
- No model retraining needed — new documents added at any time

## Weaknesses / Watch-outs

- Fails when the document corpus has outdated or missing content (FP1 from Deakin paper)
- Dense retrieval alone struggles with legal/regulatory language — must use hybrid BM25+vector
- Temporal document management (multiple versions of same policy) requires extra handling

---

*Content paraphrased for compliance with licensing restrictions.*
