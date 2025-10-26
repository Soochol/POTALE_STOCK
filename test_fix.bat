@echo off
echo ====================================
echo Block Duplication Fix - Test Script
echo ====================================
echo.

echo [1/3] Clearing database...
sqlite3 data\database\stock_data.db "DELETE FROM dynamic_block_detection; DELETE FROM seed_pattern;"
echo OK - Database cleared
echo.

echo [2/3] Running pattern detection...
.venv\Scripts\python.exe scripts\rule_based_detection\detect_patterns.py --ticker 025980 --config presets\examples\test_simple_conditions.yaml --from-date 2015-01-01
echo.

echo [3/3] Verifying results...
echo.
echo --- Pattern count ---
sqlite3 data\database\stock_data.db "SELECT COUNT(*) as pattern_count FROM seed_pattern WHERE ticker='025980';"
echo.
echo --- Dynamic block count (should be 0) ---
sqlite3 data\database\stock_data.db "SELECT COUNT(*) as block_count FROM dynamic_block_detection WHERE ticker='025980';"
echo.
echo --- Pattern details (first 5) ---
sqlite3 data\database\stock_data.db "SELECT pattern_name, json_array_length(block_features) as blocks FROM seed_pattern WHERE ticker='025980' LIMIT 5;"
echo.
echo ====================================
echo Test Complete!
echo ====================================
pause
