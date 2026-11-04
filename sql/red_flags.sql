-- 1. Laundering rate per payment format
-- AVG of a 0/1 column = share of laundering, same trick as in pandas
SELECT payment_format,
       COUNT(*) AS transactions,
       SUM(is_laundering) AS laundering,
       ROUND(AVG(is_laundering) * 100, 3) AS laundering_pct
FROM transactions
GROUP BY payment_format
ORDER BY laundering_pct DESC;

-- 2. Rule 1: structuring (USD payments just under 10,000)
SELECT COUNT(*) AS flagged,
       SUM(is_laundering) AS real_hits,
       ROUND(AVG(is_laundering) * 100, 2) AS hit_rate_pct
FROM transactions
WHERE payment_currency = 'US Dollar'
  AND amount_paid >= 9000
  AND amount_paid < 10000;

-- 3. Top 10 fan-out accounts (10 or more different receivers)
SELECT from_account,
       COUNT(DISTINCT to_account) AS receivers,
       COUNT(*) AS transactions,
       SUM(is_laundering) AS laundering
FROM transactions
GROUP BY from_account
HAVING COUNT(DISTINCT to_account) >= 10
ORDER BY receivers DESC
LIMIT 10;

-- 4. Rule 5: ACH payments from fan-out accounts
-- The subquery finds the fan-out accounts, the outer query keeps their ACH payments
SELECT COUNT(*) AS flagged,
       SUM(is_laundering) AS real_hits,
       ROUND(AVG(is_laundering) * 100, 2) AS hit_rate_pct
FROM transactions
WHERE payment_format = 'ACH'
  AND from_account IN (
      SELECT from_account
      FROM transactions
      GROUP BY from_account
      HAVING COUNT(DISTINCT to_account) >= 10
  );