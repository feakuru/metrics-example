import csv
import datetime
from pathlib import Path

from flask import (
    Flask,
    request,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    desc,
    func,
    and_,
)


app = Flask(__name__)


# Configure database

db_file = Path('adjust-task-db.db')
db_file.touch(exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(db_file.absolute())
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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


# Helper functions

def get_filter_arguments(request_arguments):
    """Get list of fields to filter rows by from comma-separated `str`."""
    result = []
    if 'date_from' in request_arguments:
        result.append(
            MetricsRecord.date >= datetime.datetime.strptime(
                request_arguments['date_from'],
                '%Y-%m-%d'
            ),
        )
    if 'date_to' in request_arguments:
        result.append(
            MetricsRecord.date <= datetime.datetime.strptime(
                request_arguments['date_to'],
                '%Y-%m-%d'
            ),
        )
    for field in ['channel', 'country', 'os']:
        if field in request_arguments:
            result.append(
                getattr(MetricsRecord, field).in_(
                    request_arguments[field].split(',')
                )
            )
    return and_(*result)


def get_group_by_clause(fields):
    """Get list of fields to group rows by from comma-separated `str`."""
    return [
        field
        for field in fields.split(',')
        if field in ['date', 'channel', 'country', 'os']
    ]


def get_metric_display(metric, fields):
    """Display specified fields from a row (individual or grouped) as a `dict`."""
    result = {}
    for field in fields.split(','):
        if field in [
                'date', 'channel', 'country',
                'os', 'impressions', 'clicks',
                'installs', 'spend', 'revenue', 'cpi']:
            result[field] = (
                getattr(metric, field)
                if field != 'date'
                else getattr(metric, field).strftime('%Y-%m-%d')
            )
    return result


def get_order_by_clause(order_by_fields):
    return [
        field if field[0] != '-' else desc(field[1:])
        for field in order_by_fields.split(',')
        if field.strip('-') in [
            'date', 'channel', 'country',
            'os', 'impressions', 'clicks',
            'installs', 'spend', 'revenue', 'cpi',
        ]
    ]


# Actual view

@app.route("/")
def show_metrics():
    metrics = MetricsRecord.query

    if 'group_by' in request.args:
        # Get grouped rows filtered via a HAVING clause
        metrics = metrics.with_entities(
            MetricsRecord.date,
            MetricsRecord.channel,
            MetricsRecord.country,
            MetricsRecord.os,
            func.sum(MetricsRecord.impressions).label('impressions'),
            func.sum(MetricsRecord.clicks).label('clicks'),
            func.sum(MetricsRecord.installs).label('installs'),
            func.sum(MetricsRecord.spend).label('spend'),
            func.sum(MetricsRecord.revenue).label('revenue'),
            (
                func.sum(MetricsRecord.spend)
                / func.sum(MetricsRecord.installs)
            ).label('cpi'),
            *[
                getattr(MetricsRecord, field)
                for field in get_group_by_clause(request.args['group_by'])
            ]
        ).group_by(
            *get_group_by_clause(request.args['group_by'])
        ).having(
            get_filter_arguments(request.args)
        )

    else:
        # Get individual rows with CPI counted at DB level
        metrics = metrics.with_entities(
            MetricsRecord.date,
            MetricsRecord.channel,
            MetricsRecord.country,
            MetricsRecord.os,
            MetricsRecord.impressions,
            MetricsRecord.clicks,
            MetricsRecord.installs,
            MetricsRecord.spend,
            MetricsRecord.revenue,
            (
                MetricsRecord.spend
                / MetricsRecord.installs
            ).label('cpi')
        ).filter(
            get_filter_arguments(request.args)
        )

    if 'order_by' in request.args:
        metrics = metrics.order_by(
            *get_order_by_clause(
                order_by_fields=request.args['order_by'],
            ),
        )

    # Display the results
    return {
        'metrics': [
            get_metric_display(
                metric,
                request.args.get(
                    'fields',
                    # Display all numeric fields by default
                    'impressions,clicks,installs,spend,revenue,cpi'
                ) + ','
                + request.args.get('group_by', '')
            )
            for metric in metrics
        ]
    }
