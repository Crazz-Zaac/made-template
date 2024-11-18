import pandas as pd
import os
import requests
import zipfile
from sqlalchemy import create_engine, Table, Column, String, Integer, Float, MetaData


# fetch the data
def fetch_data(url):
    response = requests.get(url)
    data = pd.read_excel(url, sheet_name="Figure S5.1.2", usecols="P:S", skiprows=1)
    return data


def clean_and_validate_data(data):
    data = data.dropna()
    columns_to_rename = {
        "ISO3": "Country Code",
        "GDP per capita (US$, thousands)": "GDP per Capita",
        "Share of government sustainable\nbonds": "Bond Issuance Share",
    }
    data = data.rename(columns=columns_to_rename)

    print(data.columns)

    # country code should be ISO 3166-1 alpha-3
    data = data[data["Country Code"].str.len() == 3]

    # GDP should be a positive decimal and not empty
    # data = data["GDP per Capita"].str.replace(",", "").str.replace(".", "").str.isnumeric()
    data = data[data["GDP per Capita"].astype(float) > 0]

    # Bond issuance share should be a decimal between 0 and 1 (inclusive)
    data = data[data["Bond Issuance Share"].between(0, 1, inclusive="both")]

    return data


def create_database_engine(db_path="data/country-stats.sqlite"):
    """Creates and returns an SQLAlchemy engine."""
    return create_engine(f"sqlite:///{db_path}")


def create_tables(data):
    """Defines two tables and returns the table structures."""
    metadata = MetaData()
    tables = {
        "gdpPerCapita": Table(
            "gdpPerCapita",
            metadata,
            Column("Country Code", String),
            Column("GDP per Capita", Float),
        ),
        "bondIssuance": Table(
            "bondIssuance",
            metadata,
            Column("Country Code", String),
            Column("Bond Issuance Share", Float),
        ),
    }
    return tables


def save_to_database(data, tables, engine):
    """Saves the data to the database."""
    for table_name, table in tables.items():
        table_columns = [column.name for column in table.columns]
        
        data[table_columns].to_sql(table_name, engine, if_exists="replace", index=False)


if __name__ == "__main__":
    url = "https://thedocs.worldbank.org/en/doc/7d852628d96b9411d43e5d36d5dff941-0050062022/original/Graphs-Chapter-5-02082022.xlsx"
    data = fetch_data(url)

    # clean and prepare the data
    df = clean_and_validate_data(data)

    # create the database engine
    engine = create_database_engine()
    
    # create the tables
    tables = create_tables(df)
    
    # save the data to the database
    save_to_database(df, tables, engine)
    
    print("Data saved to SQLite database.")
    
    