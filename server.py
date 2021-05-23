import os
import csv
import datetime
from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)


# Configure database

db_file = Path('adjust-task-db.db')
db_file.touch(exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(db_file.absolute())
db = SQLAlchemy(app)


# DB model definition

class MetricsRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    channel = db.Column(db.String(32), nullable=False)
    country = db.Column(db.String(2), nullable=False)
    os = db.Column(db.String(16), nullable=False)
    impressions = db.Column(db.Integer, nullable=False)
    clicks = db.Column(db.Integer, nullable=False)
    installs = db.Column(db.Integer, nullable=False)
    spend = db.Column(db.Float, nullable=False)
    revenue = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'Record #{self.id}: {self.date} {self.channel} {self.country} {self.os}'


# Reload the database from the CSV on server startup

def reload_database():
    db.drop_all()
    db.create_all()
    with open('dataset.csv') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            row['date'] = datetime.datetime.strptime(
                row['date'],
                '%Y-%m-%d'
            )
            db.session.add(MetricsRecord(**row))
        db.session.commit()

reload_database()

print('Records in database:', MetricsRecord.query.count())


# Actual view

@app.route("/")
def show_metrics():
    metrics = MetricsRecord.query.all()
    return {
        'metrics': [
            {
                'date': metric.date.strftime('%Y-%m-%d'),
                'channel': metric.channel,
                'country': metric.country,
                'os': metric.os,
                'impressions': metric.impressions,
                'clicks': metric.clicks,
                'installs': metric.installs,
                'spend': metric.spend,
                'revenue': metric.revenue,
            }
            for metric in metrics
        ]
    }
