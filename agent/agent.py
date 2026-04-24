import json
import os
import sys

# Force UTF-8 output so Hebrew prints correctly on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')

# Path to the clients data file
data_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'clients.json')

# Load client data
try:
    with open(data_file, 'r', encoding='utf-8') as f:
        clients = json.load(f)
except FileNotFoundError:
    print("שגיאה: קובץ הנתונים לא נמצא.")
    exit(1)

# Ask for client name
client_name = input("הכנס שם לקוח: ")

# Find the client
client = None
for c in clients:
    if c['name'] == client_name:
        client = c
        break

# Print summary or not found
if client:
    products = ', '.join(client['products'])
    issues = ', '.join(client['open_issues'])
    summary = f"""
הכנה לפגישה עם {client['name']}:

תאריך פגישה אחרון: {client['last_meeting_date']}
מוצרים שהם מוכרים: {products}
בעיות פתוחות: {issues}

הצעות הכנה:
- סקור את המוצרים החדשים שלנו שיכולים להתאים
- הכן הצעות לפתרון הבעיות הפתוחות
- בדוק מחירים ועדכונים בשוק
"""
    print(summary)
else:
    print(f"לקוח בשם '{client_name}' לא נמצא ברשימה.")