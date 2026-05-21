from fastapi import FastAPI, HTTPException
import mysql.connector
import os
import time

app = FastAPI()

def get_connection():

    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

@app.get("/health")
def health():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return {"status": "healthy", "version": os.getenv("APP_VERSION", "1.0.0")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users")
def get_users():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, email FROM users")

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return [
    {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"]
    }
    for user in users
]