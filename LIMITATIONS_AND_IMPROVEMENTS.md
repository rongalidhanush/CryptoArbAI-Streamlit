# Limitations and improvements

- Public APIs may rate-limit, delay, or fail. The dashboard deliberately reports
  this instead of showing stale placeholder market data.
- API quotes do not guarantee executable liquidity or fill prices; validate order
  books, withdrawal status, and regional availability before acting.
- Fee schedules are the original static assumptions and should be maintained from
  verified exchange schedules before production trading use.
- The optional LSTM path needs a trained local model; otherwise prediction uses
  the existing momentum method and is not financial advice.
- Use PostgreSQL and a managed secret store for persistent production deployment.
