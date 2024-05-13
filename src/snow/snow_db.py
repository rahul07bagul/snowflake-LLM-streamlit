import json
from snowflake.snowpark import Session
from snow.snow_llm import summerize_articles
from snow.snow_util import get_session 
from datetime import datetime
from snowflake.connector import DictCursor

session = get_session()

# Function to serialize authors list as JSON if necessary
def serialize_authors(authors):
    return json.dumps(authors) if authors else None

# Function to insert articles using Snowpark
def insert_articles_db(session, articles):
    print("Inserting articles in snowflake....")
    # Prepare data for insertion
    data_to_insert = [
        {
            "article_id": article.id,
            "title": article.title,
            "publishBy": article.by,
            "score": article.score,
            "posted_time": datetime.fromtimestamp(article.posted_time).strftime('%Y-%m-%d %H:%M:%S'),
            "image_url": article.image_url,
            "language": article.language,
            "summary": article.summary,
            "url": article.url,
            "hn_link": article.hn_link
        }
        for article in articles
    ]
    
    # Create a DataFrame
    df = session.create_dataframe(data_to_insert)
    
    # Insert data into the table
    try:
        df.write.save_as_table(table_name="articles", mode="append")
    except Exception as e:
        print("Failed to insert data:", e)

def get_session():
    return session

def insert_articles(articles_list):
    try:
        articles_list = summerize_articles(session,articles_list)
        insert_articles_db(session, articles_list)
    finally:
        print("Done")
        session.close()

def get_data():
    df = session.sql("SELECT * FROM articles LIMIT 10")
    return df

def search_data(searchterm):
    try:
        query = f"""SELECT TITLE, SUMMARY, URL  FROM ARTICLES WHERE TITLE ILIKE '%{searchterm}%'"""
        results = session.sql(query).collect()
        return results
    except:
        print("Exception")
