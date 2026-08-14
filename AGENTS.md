# CryptoArb AI Coding Instructions

Code quality is more important than speed.

## Architecture Rules

- Keep Streamlit presentation code in `app.py` and business logic outside it.
- Keep external API calls in `api/`.
- Keep arbitrage calculations in `arbitrage/`.
- Keep ML logic in `ml/`.
- Keep Gemini and prompt logic in `llm/`.
- Keep SQLAlchemy models in `database/`.
- Keep reusable helpers in `utils/`.
- Use only native Streamlit components for the maintained frontend. Do not add
  HTML, CSS, JavaScript, frontend frameworks, or component build tools.

## Style Rules

- Follow PEP 8.
- Use type hints and module/public-function docstrings.
- Avoid magic numbers and duplicated logic.
- Use logging instead of `print()` in services.
- Do not replace unavailable live data with fake prices, opportunities, or news.

## AI Rules

Gemini may only generate natural language. It must not calculate prices,
profits, percentages, predictions, or other numerical values.
