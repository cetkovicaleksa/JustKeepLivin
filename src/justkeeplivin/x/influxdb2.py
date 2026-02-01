from flask import Flask, current_app
from influxdb_client import InfluxDBClient, Point, WriteApi, QueryApi
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.flux_table import TableList

influx: InfluxDBClient | None = None
write_api: WriteApi | None = None
query_api: QueryApi | None = None

DEFAULT_BUCKET: str = ""

def write(point: Point, bucket: str | None = None):
    assert write_api, "InfluxDb not initialized. Call init_app()"

    write_api.write(
        bucket=bucket or DEFAULT_BUCKET,
        record=point
    )

def query(query: str, **params) -> TableList:
    assert query_api, "InfluxDb not initialized. Call init_app()"

    return query_api.query(
        query,
        **params
    )

def init_app(app: Flask):
    global influx, write_api, query_api, DEFAULT_BUCKET

    DEFAULT_BUCKET = app.config['INFLUX_BUCKET']
    influx = InfluxDBClient(
        url=app.config['INFLUX_URL'],
        token=app.config['INFLUX_TOKEN'],
        org=app.config['INFLUX_ORG'],
    )
    write_api = influx.write_api(write_options=SYNCHRONOUS)
    query_api = influx.query_api()
