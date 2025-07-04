-- Query to get the current term for display in Grafana dashboard
-- This can be used in a Text panel or Stat panel
SELECT value as current_term
FROM metadata
WHERE key = 'current_term';

-- Query to get last updated time
SELECT value as last_updated
FROM metadata
WHERE key = 'last_updated';

-- Query to get all metadata for dashboard information
SELECT 
    CASE 
        WHEN key = 'current_term' THEN 'Current Term'
        WHEN key = 'last_updated' THEN 'Last Updated'
        WHEN key = 'current_year' THEN 'Academic Year'
        WHEN key = 'current_quarter_name' THEN 'Quarter'
        ELSE key
    END as label,
    value
FROM metadata
WHERE key IN ('current_term', 'last_updated', 'current_year', 'current_quarter_name')
ORDER BY 
    CASE key
        WHEN 'current_term' THEN 1
        WHEN 'last_updated' THEN 2
        WHEN 'current_year' THEN 3
        WHEN 'current_quarter_name' THEN 4
        ELSE 5
    END;

-- Query for a single stat panel showing the current term
SELECT 
    value as "Current Term"
FROM metadata
WHERE key = 'current_term';

-- Query for dashboard title or header with dynamic content
SELECT 
    CONCAT('Drexel Course Scheduler - ', value) as dashboard_title
FROM metadata
WHERE key = 'current_term';