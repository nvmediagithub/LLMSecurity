# LLMSecurity Lab

LLMSecurity Lab is a clean-architecture, feature-first platform for testing the resilience of LLMs against prompt-injection attacks. It automates test execution, applies defense-in-depth pipelines, and visualises results via CLI and PyQt UI.

## Highlights
- **Defense Pipeline** – nine modular layers (L1–L9) configured via YAML profiles.
- **Test Runner & A/B mode** – compare behaviour with and without protections, collect rich metrics.
- **Multiple model connections** – switch between dummy/local clients and remote providers (OpenRouter) through declarative settings.
- **Reporting** – export CSV/JSON/HTML summaries, including layer contribution and false positives.
- **PyQt UI** – researcher/demo friendly dashboard with live status, filters, and A/B toggles.

## Project Layout
```
src/llm_security
├── core/                # shared services (config loader)
├── shared/              # reserved for common helpers
└── features/            # feature-first modules
    ├── defense/         # Defense Pipeline (L1–L9)
    ├── models/          # model clients & connection service
    ├── testing/         # prompt tests, runner, evaluator
    ├── reporting/       # metrics aggregator and exporters
    └── ui/              # PyQt presentation layer
```

Key configuration files:
- `config/profiles.yaml` – defense profiles.
- `config/policy.yaml` – policy rules for L4.
- `config/llm_connections.yaml` – LLM connection settings (provider, auth via env vars).
- `data/prompt_tests.yaml` – prompt-injection scenarios and control tests.

## Quick Start
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .

# List available LLM connections
llm-security-cli connections

# Run tests with a profile/connection
llm-security-cli run --profile strict_demo --connection dummy

# Launch the PyQt UI
llm-security-ui
```

> Install PyQt6 for the GUI component: `pip install PyQt6`.

## Documentation
- Architecture overview: `docs/architecture.md`
- Requirements summary (DOC1/DOC2): `docs/requirements_summary.md`
- Agent policy & safety guardrails: `AGENTS.md`
- Feature guides: `docs/features/*.md`

## Roadmap Ideas
1. Wire in production guard models (OpenAI Moderation, Llama Guard) for L2/L7.
2. Extend connection service with additional providers (Azure OpenAI, local backends).
3. Enrich UI with layer-level drill-down and report export buttons.

