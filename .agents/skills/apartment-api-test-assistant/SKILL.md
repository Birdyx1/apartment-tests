---
name: apartment-api-test-assistant
description: Complete and evaluate API automation for this Smart Apartment project, from contract inventory and test planning to pytest implementation, execution, and failure analysis. Use for API test work in apartment-tests, not unrelated repositories or UI/performance testing.
---

# Apartment API Test Assistant

Use this skill to help complete, review, and evaluate API automation in `apartment-tests/`. Adapt the useful stages from the supplied Skills package (API inventory, optional relationship mapping, test planning, code generation, test execution, and failure analysis), but fit them to this repository instead of importing its framework or commands literally.

## Inspect current project evidence

Read the relevant current files before deciding what is missing or making changes:

- API contract: `../smartApartment-main/docs/` or the project-provided API documents.
- Backend implementation: `../smartApartment-main/backend/` when available.
- Test framework: `config.py`, `conftest.py`, `apis/`, `core/`, `helpers/`, `tests/`, `pytest.ini`, and `requirements.txt`.
- Learning history and known issues: the parent `WIKI.md`, plus relevant project docs such as `docs/ai-test-pilot/apartment-api-matrix.md`.

## Use MCP as an evidence source

Discover the MCP tools available in the current session before planning an integration; tool availability varies by host. For this project, browser/network observation is the most direct MCP aid for API testing:

- Use an available Playwright MCP to open the local frontend, inspect the accessible UI, and list filtered network requests when a user flow or request contract is unclear. Treat browser traffic as **observed runtime behavior**, not approved expected behavior; compare it with the API document, backend controller/DTO, and human-confirmed requirement.
- Prefer request summaries (method, path, status). Do not read authorization headers, cookies, captcha payloads, or full network bodies by default. If a body is necessary to identify a field, inspect only the minimum relevant data and redact credentials, personal data, and tokens before recording it.
- Use a source-control/CI MCP only when a concrete PR or build is in scope. Report its revision and build identity; do not treat stale diagnostics as current.
- A database MCP is optional and is not a replacement for API assertions. Only use it when the user has identified an isolated test database and the task requires read-only data context. Default to no SQL mutation, no production access, and no database-based expected result unless the product contract explicitly requires it.
- Record which fact came from MCP and when it was observed. MCP calls can accelerate discovery and evidence collection, but test plans, expected outcomes, destructive actions, and code changes remain subject to the project guardrails below.

See `docs/ai-test-pilot/mcp-test-workflow.md` for the current project mapping and a verified local browser-to-API example.

Paths may differ. Discover them rather than assuming they exist. Recheck source files before relying on an older matrix or Wiki entry.

## Keep expected behavior evidence-based

Treat human-confirmed requirements as the expected behavior. Use API documents to describe the documented contract, backend code to report observed implementation, existing tests and fixtures to learn project conventions, and runtime responses as execution evidence. These sources are not interchangeable.

When they disagree, show the discrepancy with file paths and relevant symbols or line numbers, mark the expected behavior as unresolved, and ask for the smallest decision needed. Never turn an implementation quirk, a failing response, or an existing assertion into the correct product contract without confirmation. Do not invent routes, request fields, role permissions, status codes, or business messages.

Keep documented behavior, implementation observations, and approved expected behavior separate. Mark unresolved contract differences. A coverage matrix must distinguish explicit test assertions from setup/cleanup performed by fixtures.

## Complete API automation

When asked to complete an API test area, inspect its endpoints and existing code, then identify the smallest useful missing pieces. Work through this adapted pipeline:

1. **Inventory:** Record method/path, auth and ownership, parameters/body, response shape, important behavior, current wrapper/test coverage, cleanup, evidence, and unresolved questions. Treat OpenAPI/Swagger and backend code as sources to compare, not interchangeable truths.
2. **Relationship mapping (optional):** Map resource and fixture dependencies only when a scenario crosses multiple resources or cleanup/order is hard to reason about. Do not add a graph for a simple endpoint.
3. **Test plan:** Prioritize a small number of high-value cases. Consider validation, state transitions, ownership/security boundaries, and concurrency when relevant. Keep assumptions visible and test data isolated with reliable cleanup.
4. **Project-shaped implementation:** Add only the needed API wrapper, fixture, and pytest scenario using this project's existing `apis/`, `core/`, root `conftest.py`, `helpers/`, `tests/`, and assertion conventions. Do not introduce the supplied package's alternate `tests/api/`, builder/assertion framework, environment layout, or database checks unless the repository has deliberately adopted them.
5. **Execution:** Prefer a targeted pytest run for new or changed cases; broaden to the suite when requested or justified. Inspect actual output and, where available, current Allure/Jenkins results. Do not use a blocking `allure serve` workflow by default; this project already uses Jenkins and Allure reporting.
6. **Failure analysis:** Classify failures as contract ambiguity, product behavior, test-code defect, environment/setup, or test-data/cleanup issue. Use request/response evidence, pytest output, and Allure details when available. Recommend a narrow repair; never disguise a product defect by weakening assertions.

When asked to **补全**, implement the scoped missing test automation and run the targeted check when the environment permits. When asked to **评测/检查**, first assess and report findings; do not silently rewrite code. If expected behavior is unresolved, document the test-design options and leave that assertion undecided rather than inventing a result.

Do not assume a database assertion is needed when the project tests the API contract. Do not generate a full test suite when one focused case closes the requested gap.

For a **whole-project audit**, inventory backend controller groups, API wrapper modules, test modules, pytest collection, available contract documents, CI/Allure evidence, and known defects. Map coverage by business domain and mark unmapped endpoints as candidates for review rather than declaring them untested solely from a filename mismatch. State whether the audit is a static inventory or a line-by-line assertion review, and do not extrapolate from one sample to the whole suite.

## Evaluate test quality

For a review, evaluate each dimension as **OK**, **Gap**, or **Unclear**, and attach a file/test/evidence reference:

- **Contract fidelity:** endpoint, fields, auth/ownership, expected HTTP and business outcomes match an approved contract.
- **Risk coverage:** important happy path, negative/boundary cases, state transitions, and relevant role/ownership cases are represented.
- **Assertion strength:** tests verify business data and meaningful outcomes, not just that a request ran or returned an HTTP response.
- **Isolation and cleanup:** data is unique, setup is deterministic, teardown removes only owned test data, and tests do not depend on execution order.
- **Maintainability:** API calls reuse the existing client/wrapper/fixture patterns without duplicated framework layers.
- **Execution evidence:** report exact test scope and observed results; distinguish collection from execution and local results from CI results.

Summarize the highest-severity gaps first. Do not invent an overall percentage or call the framework “complete” unless the scope and evidence support that conclusion.

## Project-specific guardrails

- Reuse `ApiClient`, existing role clients and fixtures, and `assert_response` where appropriate. Avoid duplicate login/request logic and unrelated refactors.
- Do not weaken or remove an assertion merely to make a known product defect pass. Preserve known defects in regression unless the user changes that policy.
- Do not commit, push, deploy, modify Jenkins configuration, or change external systems unless explicitly requested. Do not expose tokens, passwords, captcha values, or other secrets.

## Learning record

When asked to maintain learning progress, update the parent `WIKI.md` with completed work, evidence, unresolved items, and next step. Do not mark work complete based only on a proposed plan; use the user's run output or a verified local run as evidence.
