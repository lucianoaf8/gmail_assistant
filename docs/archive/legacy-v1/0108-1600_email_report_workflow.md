# Email Classification Report Workflow

This document captures the exact process used on 2025-09-19 to build docs/email_classification_report.md from the classified email database.

## 1. Identify the Active Database
- Located the classified dataset at 	rash/database_old/production/emails_classified.db.
- Confirmed schema with PRAGMA table_info(emails) to ensure classification fields (primary_category, domain_category, priority_level, etc.) are present.

## 2. Generate Aggregate Metrics with SQLite
The workflow executes a Python script that:

### Summary
`sql
SELECT COUNT(*), MIN(parsed_date), MAX(parsed_date)
FROM emails;
`

### Primary Category Breakdown
`sql
SELECT primary_category,
       COUNT(*) AS total,
       ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM emails), 1) AS pct,
       ROUND(AVG(confidence_score), 2) AS avg_conf
FROM emails
GROUP BY primary_category
ORDER BY total DESC;
`

### Domain Category Breakdown
`sql
SELECT domain_category,
       COUNT(*) AS total,
       ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM emails), 1) AS pct,
       ROUND(AVG(confidence_score), 2) AS avg_conf
FROM emails
GROUP BY domain_category
ORDER BY total DESC;
`

### Recent 6 Months Snapshot
`sql
SELECT year_month,
       COUNT(*) AS total_emails,
       SUM(CASE WHEN primary_category = 'Newsletter' THEN 1 ELSE 0 END) AS newsletters,
       SUM(CASE WHEN primary_category = 'Service_Notification' THEN 1 ELSE 0 END) AS service_notifications
FROM emails
GROUP BY year_month
ORDER BY year_month DESC
LIMIT 6;
`

### Priority & Action Matrix
`sql
SELECT action_required,
       priority_level,
       COUNT(*) AS total,
       SUM(CASE WHEN source_type = 'Human' THEN 1 ELSE 0 END) AS human_count
FROM emails
GROUP BY action_required, priority_level
ORDER BY priority_level DESC, total DESC;
`

### Low-Confidence Hotspots
`sql
SELECT primary_category,
       COUNT(*) AS low_count
FROM emails
WHERE confidence_score < 0.4
GROUP BY primary_category
ORDER BY low_count DESC;
`

### Source Mix
`sql
SELECT source_type,
       COUNT(*) AS total,
       ROUND(AVG(automated_score), 2) AS avg_auto,
       ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM emails), 1) AS pct
FROM emails
GROUP BY source_type
ORDER BY total DESC;
`

### High-Frequency Senders
`sql
SELECT sender,
       sender_frequency,
       primary_category,
       domain_category
FROM emails
WHERE sender_frequency >= 50
GROUP BY sender
ORDER BY sender_frequency DESC;
`

### Recent High-Priority Alerts
`sql
SELECT parsed_date,
       sender,
       subject,
       action_required,
       priority_level,
       source_type,
       confidence_score
FROM emails
WHERE priority_level = 'High'
ORDER BY parsed_date DESC
LIMIT 10;
`

## 3. Markdown Assembly
- Script escapes | characters so sender/subject strings render correctly inside tables.
- Sections appended in this order:
  1. Summary bullets
  2. Primary Category Breakdown table
  3. Domain Coverage table
  4. Recent 6 Months table
  5. Priority & Action Matrix
  6. Low-Confidence Hotspots
  7. Source Mix
  8. High-Frequency Senders (≥ 50 emails)
  9. Recent High-Priority Alerts (latest 10)

## 4. Script Invocation
- Temporary script _build_report.py stored under docs/, executed with:
  `ash
  python docs/_build_report.py
  `
- Output written to docs/email_classification_report.md and the helper script deleted.

## 5. Verification
- Spot-checked resulting Markdown tables. Aggregates match the documentation statistics (e.g., Newsletter 814 emails at 29.2%).

## Reuse Tips
- Update the DB_PATH constant in the script if the database moves.
- Run the Python block whenever you refresh classifications.
- Consider embedding this logic into a permanent CLI utility to avoid temp scripts.
