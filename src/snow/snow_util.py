from snowflake.snowpark import Session
import json

# Path to the JSON config file
config_file_path = 'config.json'

# Function to load the configuration
def load_config(path):
    with open(path, 'r') as file:
        config = json.load(file)
    return config

# Load the configuration
config = load_config(config_file_path)
session = ''
connection_parameters = {
    "account": config['SNOWFLAKE_ACCOUNT'],
    "host": config['SNOWFLAKE_HOST'],
    "user": config['SNOWFLAKE_USER'],
    "password": config['SNOWFLAKE_PASSWORD'],
    "warehouse": config['SNOWFLAKE_WAREHOUSE'],
    "database": config['SNOWFLAKE_DATABASE'],
    "schema": config['SNOWFLAKE_SCHEMA'],
    "role": config['SNOWFLAKE_ROLE']
}

databases = [
    'FROSTY_SAMPLE',
    'NEWS',
    'SALESFORCE'
]

schema = {
    'FROSTY_SAMPLE': ['CYBERSYN_FINANCIAL'],
    'NEWS': ['DAILY_NEWS'],
    'SALESFORCE': ['PERMISSIONSET']
}

view_table = {
    'FROSTY_SAMPLE.CYBERSYN_FINANCIAL': ['FINANCIAL_ENTITY_ANNUAL_TIME_SERIES','FINANCIAL_ENTITY_ATTRIBUTES_LIMITED'],
    'NEWS.DAILY_NEWS': ['ARTICLES'],
    'SALESFORCE.PERMISSIONSET': ['PERMISSIONSETASSIGNMENT']
}

# Function to create a Snowpark session
def create_session():
    return Session.builder.configs(connection_parameters).create()

def get_session():
    return session

def list_databases(session):
    #databases = session.sql("SHOW DATABASES").collect()
    #database_names = [row.name for row in databases]
    return databases

def list_schemas(session, database_name):
    #schemas = session.sql(f"SHOW SCHEMAS IN {database_name}").collect()
    #schema_names = [row.name for row in schemas]
    return schema.get(database_name)

def list_tables(db_schema_name):
    return view_table.get(db_schema_name)

session = create_session()
