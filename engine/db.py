import os
import sqlite3
import csv

con = sqlite3.connect("jarvis.db")
cursor = con.cursor()

# Create contacts table
cursor.execute('''CREATE TABLE IF NOT EXISTS contacts 
                  (id integer primary key, name VARCHAR(200), mobile_no VARCHAR(255), 
                   email VARCHAR(255) NULL, address VARCHAR(255) NULL)''')

# Create system commands table
cursor.execute('''CREATE TABLE IF NOT EXISTS sys_command 
                  (id integer primary key, name VARCHAR(100), path VARCHAR(1000))''')

# Create web commands table
cursor.execute('''CREATE TABLE IF NOT EXISTS web_command 
                  (id integer primary key, name VARCHAR(100), url VARCHAR(1000))''')

# Create info table
cursor.execute('''CREATE TABLE IF NOT EXISTS info 
                  (name VARCHAR(100), designation VARCHAR(50), mobileno VARCHAR(40), 
                   email VARCHAR(200), city VARCHAR(300))''')

con.commit()

# Import contacts from CSV if file exists
try:
    if os.path.exists('contacts.csv'):
        desired_columns_indices = [0, 18]
        with open('contacts.csv', 'r', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                selected_data = [row[i] for i in desired_columns_indices if i < len(row)]
                if len(selected_data) >= 2:
                    cursor.execute(''' INSERT INTO contacts (id, name, mobile_no) 
                                     VALUES (null, ?, ?);''', tuple(selected_data))
        con.commit()
except Exception as e:
    print(f"Error importing contacts: {e}")

con.close()
