from flask import Flask, request, render_template_string, jsonify
import json
import os

app = Flask(__name__)

# Path to the clients data file
data_file = os.path.join(os.path.dirname(__file__), 'data', 'clients.json')

# Load client data
def load_clients():
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save client data
def save_clients(clients):
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)

# Generate meeting preparation summary
def generate_summary(client):
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
    return summary.strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    clients = load_clients()
    client_names = [client['name'] for client in clients]

    if request.method == 'POST':
        client_name = request.form.get('client_name', '').strip()

        # Find the client
        client = None
        for c in clients:
            if c['name'] == client_name:
                client = c
                break

        if client:
            summary = generate_summary(client)
            return render_template_string(HTML_TEMPLATE, client_names=client_names, summary=summary, selected_client=client_name)
        else:
            error = f"לקוח בשם '{client_name}' לא נמצא ברשימה."
            return render_template_string(HTML_TEMPLATE, client_names=client_names, error=error, selected_client=client_name)

    return render_template_string(HTML_TEMPLATE, client_names=client_names)

@app.route('/manage-clients', methods=['GET', 'POST'])
def manage_clients():
    clients = load_clients()
    message = None
    error = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_update':
            client_name = request.form.get('client_name', '').strip()
            last_meeting_date = request.form.get('last_meeting_date', '').strip()
            products_text = request.form.get('products', '').strip()
            issues_text = request.form.get('open_issues', '').strip()

            if not client_name:
                error = "שם הלקוח הוא שדה חובה."
            else:
                # Parse products and issues (comma-separated)
                products = [p.strip() for p in products_text.split(',') if p.strip()]
                open_issues = [i.strip() for i in issues_text.split(',') if i.strip()]

                # Check if client already exists
                existing_client = None
                for i, c in enumerate(clients):
                    if c['name'] == client_name:
                        existing_client = i
                        break

                client_data = {
                    "name": client_name,
                    "last_meeting_date": last_meeting_date,
                    "products": products,
                    "open_issues": open_issues
                }

                if existing_client is not None:
                    # Update existing client
                    clients[existing_client] = client_data
                    message = f"הלקוח '{client_name}' עודכן בהצלחה."
                else:
                    # Add new client
                    clients.append(client_data)
                    message = f"הלקוח '{client_name}' נוסף בהצלחה."

                # Save to file
                save_clients(clients)

        elif action == 'delete':
            client_name = request.form.get('delete_client_name')
            clients = [c for c in clients if c['name'] != client_name]
            save_clients(clients)
            message = f"הלקוח '{client_name}' נמחק בהצלחה."

    return render_template_string(MANAGE_TEMPLATE, clients=clients, message=message, error=error)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>סוכן הכנת פגישות - BD Agent</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            direction: rtl;
        }

        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            width: 100%;
            max-width: 600px;
            text-align: center;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
            font-weight: 300;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }

        .form-group {
            margin-bottom: 25px;
        }

        select, button {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
        }

        select:focus, button:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        select {
            background: white;
            cursor: pointer;
        }

        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            margin-top: 10px;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        .summary {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 25px;
            margin-top: 25px;
            text-align: right;
            white-space: pre-line;
            line-height: 1.6;
            font-size: 15px;
        }

        .summary-title {
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            font-size: 18px;
        }

        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            border-radius: 10px;
            padding: 15px;
            margin-top: 25px;
            text-align: center;
        }

        .logo {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 24px;
            margin-bottom: 20px;
        }

        @media (max-width: 768px) {
            .container {
                margin: 20px;
                padding: 30px 20px;
            }

            h1 {
                font-size: 2em;
            }
        }

        .nav-link:hover {
            background: #667eea !important;
            color: white !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">BD</div>
        <h1>סוכן הכנת פגישות</h1>
        <p class="subtitle">בחר לקוח וקבל סיכום הכנה לפגישה</p>

        <div style="text-align: center; margin-bottom: 30px;">
            <a href="/manage-clients" class="nav-link" style="display: inline-block; padding: 10px 20px; background: #f8f9fa; color: #667eea; text-decoration: none; border-radius: 10px; font-weight: 500; transition: all 0.3s ease;">ניהול לקוחות →</a>
        </div>

        <form method="post">
            <div class="form-group">
                <select name="client_name" required>
                    <option value="">בחר לקוח...</option>
                    {% for name in client_names %}
                    <option value="{{ name }}" {% if selected_client == name %}selected{% endif %}>{{ name }}</option>
                    {% endfor %}
                </select>
            </div>
            <button type="submit">הכן סיכום פגישה</button>
        </form>

        {% if summary %}
        <div class="summary">
            <div class="summary-title">סיכום הכנה לפגישה</div>
            {{ summary }}
        </div>
        {% endif %}

        {% if error %}
        <div class="error">
            {{ error }}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

MANAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ניהול לקוחות - BD Agent</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            direction: rtl;
        }

        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .logo {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 24px;
            margin-bottom: 20px;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
            font-weight: 300;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }

        .nav {
            text-align: center;
            margin-bottom: 30px;
        }

        .nav a {
            display: inline-block;
            padding: 10px 20px;
            background: #f8f9fa;
            color: #667eea;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .nav a:hover {
            background: #667eea;
            color: white;
        }

        .form-section, .clients-section {
            margin-bottom: 40px;
        }

        .section-title {
            color: #333;
            font-size: 1.5em;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }

        input, textarea, button {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
            font-family: inherit;
        }

        input:focus, textarea:focus, button:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        textarea {
            resize: vertical;
            min-height: 80px;
        }

        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            margin-top: 10px;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        .message {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
        }

        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
        }

        .clients-list {
            display: grid;
            gap: 20px;
        }

        .client-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
            position: relative;
        }

        .client-name {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }

        .client-detail {
            margin-bottom: 5px;
            color: #666;
        }

        .client-detail strong {
            color: #333;
        }

        .delete-btn {
            position: absolute;
            top: 10px;
            left: 10px;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 5px 10px;
            font-size: 12px;
            cursor: pointer;
            transition: background 0.3s ease;
        }

        .delete-btn:hover {
            background: #c82333;
        }

        .help-text {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }

        @media (max-width: 768px) {
            .container {
                margin: 10px;
                padding: 20px;
            }

            h1 {
                font-size: 2em;
            }

            .clients-list {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">BD</div>
            <h1>ניהול לקוחות</h1>
            <p class="subtitle">הוסף, ערוך ומחק לקוחות במערכת</p>
        </div>

        <div class="nav">
            <a href="/">← חזרה להכנת פגישות</a>
        </div>

        {% if message %}
        <div class="message">
            {{ message }}
        </div>
        {% endif %}

        {% if error %}
        <div class="error">
            {{ error }}
        </div>
        {% endif %}

        <div class="form-section">
            <h2 class="section-title">הוסף/ערוך לקוח</h2>
            <form method="post">
                <input type="hidden" name="action" value="add_update">
                <div class="form-group">
                    <label for="client_name">שם הלקוח *</label>
                    <input type="text" id="client_name" name="client_name" required placeholder="הכנס שם לקוח">
                </div>
                <div class="form-group">
                    <label for="last_meeting_date">תאריך פגישה אחרון</label>
                    <input type="date" id="last_meeting_date" name="last_meeting_date">
                </div>
                <div class="form-group">
                    <label for="products">מוצרים שהם מוכרים</label>
                    <textarea id="products" name="products" placeholder="הכנס מוצרים מופרדים בפסיקים (למשל: שפתונים, צלליות, יסוד)"></textarea>
                    <div class="help-text">הפרד בין מוצרים בפסיקים</div>
                </div>
                <div class="form-group">
                    <label for="open_issues">בעיות פתוחות</label>
                    <textarea id="open_issues" name="open_issues" placeholder="הכנס בעיות פתוחות מופרדות בפסיקים (למשל: עיכובים במשלוחים, משא ומתן על מחירים)"></textarea>
                    <div class="help-text">הפרד בין בעיות בפסיקים</div>
                </div>
                <button type="submit">שמור לקוח</button>
            </form>
        </div>

        <div class="clients-section">
            <h2 class="section-title">לקוחות קיימים</h2>
            {% if clients %}
            <div class="clients-list">
                {% for client in clients %}
                <div class="client-card">
                    <form method="post" style="display: inline;" onsubmit="return confirm('האם אתה בטוח שברצונך למחוק לקוח זה?');">
                        <input type="hidden" name="action" value="delete">
                        <input type="hidden" name="delete_client_name" value="{{ client.name }}">
                        <button type="submit" class="delete-btn">מחק</button>
                    </form>
                    <div class="client-name">{{ client.name }}</div>
                    <div class="client-detail"><strong>תאריך פגישה אחרון:</strong> {{ client.last_meeting_date }}</div>
                    <div class="client-detail"><strong>מוצרים:</strong> {{ client.products | join(', ') }}</div>
                    <div class="client-detail"><strong>בעיות פתוחות:</strong> {{ client.open_issues | join(', ') }}</div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <p>אין לקוחות במערכת עדיין.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)