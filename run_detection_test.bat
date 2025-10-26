@echo off
REM Block Duplication Fix - Detection Test
REM Date: 2025-10-26

echo ========================================
echo Pattern Detection Test (Fixed Version)
echo ========================================
echo.

echo [Step 1/4] Clearing database...
sqlite3 data\database\stock_data.db "DELETE FROM dynamic_block_detection;"
sqlite3 data\database\stock_data.db "DELETE FROM seed_pattern;"
echo OK - Database cleared
echo.

echo [Step 2/4] Running pattern detection...
echo Command: detect_patterns.py --ticker 025980 --from-date 2015-01-01
echo.
.venv\Scripts\python.exe scripts\rule_based_detection\detect_patterns.py --ticker 025980 --config presets\examples\test_simple_conditions.yaml --from-date 2015-01-01

echo.
echo [Step 3/4] Verifying results...
echo.

echo --- Pattern Count ---
sqlite3 data\database\stock_data.db "SELECT COUNT(*) as 'Total Patterns' FROM seed_pattern WHERE ticker='025980';"

echo.
echo --- Dynamic Block Count (should be 0) ---
sqlite3 data\database\stock_data.db "SELECT COUNT(*) as 'Dynamic Blocks (Should be 0)' FROM dynamic_block_detection WHERE ticker='025980';"

echo.
echo --- Block Distribution ---
sqlite3 data\database\stock_data.db "SELECT pattern_name, json_array_length(block_features) as block_count FROM seed_pattern WHERE ticker='025980' ORDER BY detection_date LIMIT 10;"

echo.
echo --- Total Blocks in JSON ---
sqlite3 data\database\stock_data.db "SELECT SUM(json_array_length(block_features)) as 'Total Blocks in JSON' FROM seed_pattern WHERE ticker='025980';"

echo.
echo [Step 4/4] Checking for duplicates...
sqlite3 data\database\stock_data.db "SELECT COUNT(*) as 'Duplicate Blocks (Should be 0)' FROM dynamic_block_detection WHERE ticker='025980' GROUP BY block_id, started_at HAVING COUNT(*) > 1;"

echo.
echo ========================================
echo Test Complete!
echo ========================================
echo.
echo Expected Results:
echo   - Total Patterns: 64
echo   - Dynamic Blocks: 0 (disabled to prevent duplication)
echo   - Total Blocks in JSON: ~90
echo   - Duplicate Blocks: 0
echo.
