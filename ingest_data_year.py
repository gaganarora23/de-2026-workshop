#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm
import click

dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]


def ingest_data(url: str, engine, target_table: str, chunksize: int = 100000, month: int) :
    
    df_iter = pd.read_csv(
        url,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunksize
    )

    first_chunk = next(df_iter)

    if month == 1:
        first_chunk.head(0).to_sql(
            name=target_table,
            con=engine,
            if_exists="replace"
        )

        print(f"Table {target_table} created")

    first_chunk.to_sql(
        name=target_table,
        con=engine,
        if_exists="append"
    )

    print(f"Inserted first chunk: {len(first_chunk)}")

    for df_chunk in tqdm(df_iter):
        df_chunk.to_sql(
            name=target_table,
            con=engine,
            if_exists="append"
        )
        print(f"Inserted chunk: {len(df_chunk)}")

    print(f'done ingesting to {target_table}')

@click.command()
@click.option('--pg_user', default='root', help='PostgreSQL username')
@click.option('--pg_pass', default='root', help='PostgreSQL password')
@click.option('--pg_host', default='localhost', help='PostgreSQL host')
@click.option('--pg_port', default='5432', help='PostgreSQL port')
@click.option('--pg_db', default='ny_taxi', help='PostgreSQL database')
@click.option('--year', type=int, default=2021, help='Year for data')
@click.option('--chunksize', type=int, default=100000, help='Chunk size for ingestion')
@click.option('--target_table', default='yellow_taxi_data', help='Target table name')
def main(pg_user, pg_pass, pg_host, pg_port, pg_db, year, chunksize, target_table):
    engine = create_engine(f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')
    url_prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow'

    for month in range(1, 13):
        url = f'{url_prefix}/yellow_tripdata_{year:04d}-{month:02d}.csv.gz'
        print(f'Ingesting data for {year}-{month:02d} from {url}')
        ingest_data(
            url=url,
            engine=engine,
            target_table=target_table,
            chunksize=chunksize,
            month=month
        )

if __name__ == '__main__':
    main()