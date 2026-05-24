from flask import Flask, render_template, request, send_file
import mysql.connector
from user_agents import parse
from datetime import datetime
import requests
import pandas as pd
import os

app = Flask(__name__)

# DATABASE CONNECTION
db = mysql.connector.connect(
    host=os.environ.get("DB_HOST"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    database=os.environ.get("DB_NAME"),
    port=int(os.environ.get("DB_PORT", 3306)),
    ssl_disabled=False
)

cursor = db.cursor()

# HOME PAGE
@app.route('/')
def home():

    # GET USER IP
    ip = request.headers.get(
        'X-Forwarded-For',
        request.remote_addr
    )

    # USER AGENT DETAILS
    user_agent_string = request.headers.get('User-Agent')
    user_agent = parse(user_agent_string)

    browser = user_agent.browser.family
    operating_system = user_agent.os.family
    device = user_agent.device.family

    # LOCATION TRACKING
    try:
        response = requests.get(
            f'http://ip-api.com/json/{ip}'
        ).json()

        country = response.get('country', 'Unknown')
        city = response.get('city', 'Unknown')

    except:
        country = 'Unknown'
        city = 'Unknown'

    visit_time = datetime.now()

    # INSERT DATA
    sql = """
    INSERT INTO visitors
    (
        ip_address,
        browser,
        operating_system,
        device,
        country,
        city,
        visit_time
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        ip,
        browser,
        operating_system,
        device,
        country,
        city,
        visit_time
    )

    cursor.execute(sql, values)
    db.commit()

    return render_template('index.html')


# DASHBOARD
@app.route('/dashboard')
def dashboard():

    cursor.execute(
        "SELECT * FROM visitors ORDER BY id DESC"
    )

    visitors = cursor.fetchall()

    # UNIQUE VISITOR COUNT
    cursor.execute(
        "SELECT COUNT(DISTINCT ip_address) FROM visitors"
    )

    unique_visitors = cursor.fetchone()[0]

    return render_template(
        'dashboard.html',
        visitors=visitors,
        unique_visitors=unique_visitors
    )


# EXPORT CSV
@app.route('/export')
def export_csv():

    query = "SELECT * FROM visitors"

    df = pd.read_sql(query, db)

    file_name = "visitors.csv"

    df.to_csv(file_name, index=False)

    return send_file(
        file_name,
        as_attachment=True
    )


if __name__ == '__main__':
    app.run(debug=True)