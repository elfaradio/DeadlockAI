# Senior Software Engineer Review Report: DeadlockAI

This document presents a comprehensive audit and engineering review of the DeadlockAI codebase, highlighting architectural, security, performance, scalability, maintainability, testing, and API design issues, followed by the refactoring design.

## 📊 System Quality Scorecard

| Metric | Score | Key Area |
| :--- | :---: | :--- |
| **Current Architecture** | **8 / 10** | Layered correctly, but direct global container imports violate clean DI principles. |
| **Security** | **7 / 10** | Missing strict input sanitation on IDs; potential SQL/command injection vectors. |
| **Scalability** | **6 / 10** | Sync database queries block FastAPI's single-threaded event loop. |
| **Maintainability** | **8 / 10** | Good component division, but uses deprecated FastAPI lifecycle events. |
| **Performance** | **7 / 10** | Unclosed Matplotlib figures causing memory leaks; lack of database indexes. |

---

## 🔍 Detailed Audit Findings

### 1. Architectural Weaknesses
- **Tight DI Coupling**: Routers import `container` directly from `src.infrastructure.di.container`. This prevents dependency overriding during testing or hot-swapping implementations.
- **Deprecated Startup Hooks**: FastAPI `@app.on_event("startup")` is deprecated. Lifespan context managers are now the standard.

### 2. Security Vulnerabilities
- **Input Validation Gaps**: Process IDs (`pid`) and resource IDs (`rid`) accept arbitrary string characters. If malicious commands or SQL fragments are entered, it could compromise database security.
- **Error Information Disclosure**: Global exception middleware returns raw traceback details directly to API clients.

### 3. Performance Bottlenecks
- **Event-Loop Blocking**: Calling synchronous database repository queries directly in async FastAPI routes blocks the single-threaded event loop, severely degrading concurrent request handling.
- **Matplotlib Memory Leaks**: In-memory plotting without a guaranteed `plt.close()` clean-up block holds onto figure memory and will eventually crash the server.
- **Missing Database Indexes**: Queries on allocations/edges and metrics are un-indexed, resulting in slow $O(N)$ sequential table scans.

### 4. API Design & Reliability
- **Lack of Correlation IDs**: Troubleshooting concurrent requests is difficult without a unified request correlation identifier (`X-Correlation-ID`) across logs.
- **Unstructured Caching & Failures**: Caching matches exact strings, and API failures are not modeled gracefully, leading to 500 errors if Gemini times out.

### 5. Streamlit UX & Rendering
- **Excessive Network Calls**: Streamlit runs the script from top to bottom on every user action. The client performs redundant HTTP requests to `/api/simulation/state` on every render.
- **API Disconnect Fragility**: The interface crashes completely if the FastAPI server is unreachable.

---

## 🛠️ Refactoring Implementation Plan

1. **FastAPI Dependency Injection**: Replace imports of `container` in route files with `Depends` functions for clean, overrideable dependency resolution.
2. **Context-Aware Correlation IDs**: Introduce middleware to attach a ContextVar correlation ID to every logging statement and response header.
3. **Async DB Operations**: Wrap blocking SQLAlchemy sessions in `asyncio.to_thread` calls in the repositories.
4. **Matplotlib Safety**: Explicitly set the non-GUI `Agg` backend and isolate figure generation inside `try...finally` blocks.
5. **Database Indexing**: Add indexes on `edges` search columns (`from_node`, `to_node`) and metadata timestamp columns in migrations.
6. **Strict Input Sanitization**: Validate process/resource IDs in Pydantic models using regex constraints (`^[a-zA-Z0-9_-]+$`).
7. **Streamlit UX Improvement**: Cache client instances and handle HTTP errors gracefully with user-friendly retry banners.
8. **Multi-stage Docker builds**: Minimize runner image footprint.
