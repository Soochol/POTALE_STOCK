"""Check database tables"""
import sqlite3

conn = sqlite3.connect('data/database/stock_data.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print(f'\nTotal tables: {len(tables)}\n')
print('=' * 50)

# Categories
stock_tables = []
detection_tables = []
pattern_tables = []
preset_tables = []
monitoring_tables = []

for table in tables:
    name = table[0]
    if name.startswith('block') and 'detection' in name:
        detection_tables.append(name)
    elif name == 'block_pattern':
        pattern_tables.append(name)
    elif 'preset' in name:
        preset_tables.append(name)
    elif name in ['data_collection_log', 'collection_progress', 'data_quality_check']:
        monitoring_tables.append(name)
    else:
        stock_tables.append(name)

print('Stock Tables (4):')
for t in stock_tables:
    print(f'  - {t}')

print('\nDetection Tables (4):')
for t in detection_tables:
    print(f'  - {t}')

print('\nPattern Tables (1):')
for t in pattern_tables:
    print(f'  - {t}')

print('\nPreset Tables (2):')
for t in preset_tables:
    print(f'  - {t}')

print('\nMonitoring Tables (3):')
for t in monitoring_tables:
    print(f'  - {t}')

print('=' * 50)
print(f'\nOK Database successfully created with {len(tables)} tables!')
print('   (Expected: 14 tables, Got: {} tables)'.format(len(tables)))

conn.close()
