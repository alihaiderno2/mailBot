import os
import csv
import smtplib
import random
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TEMPLATES = [
    "Hello,\n\nI was looking at {restaurant} and wanted to share a quick idea about your menu.\n\nBest,\nAli",
    "Hi there,\n\nWe help businesses like {restaurant} transition to interactive 3D menus.\n\nCheers,\nAli",
    "Greetings,\n\nI noticed {restaurant} recently and wanted to connect regarding a 3D web experience for your customers.\n\nThanks,\nAli",
    "Hello,\n\nWould {restaurant} be open to upgrading its digital presence with an interactive QR menu?\n\nBest,\nAli"
]

def is_valid_name(name):
    if not name:
        return False
    invalid_markers = ['null', 'none', 'nan', 'na', 'n/a', 'missing', 'undefined']
    clean_name = str(name).strip().lower()
    if clean_name in invalid_markers or len(clean_name) < 2:
        return False
    return True

def run_batch_mailer(batch_limit=25):
    sender_email = os.environ.get("BOT_EMAIL")
    app_password = os.environ.get("BOT_PASSWORD")
    csv_filename = "contacts.csv"
    
    rows = []
    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
            
    pending_rows = [row for row in rows if row.get('Status') != 'Sent']
    batch = pending_rows[:batch_limit]
    
    if not batch:
        print("No pending emails left in the CSV. Exiting.")
        return

    print(f"Starting batch of {len(batch)} emails...")
    processed_count = 0
    
    for row in batch:
        recipient = row['Email']
        raw_name = row.get('Restaurant', '')
        
        # Apply the fallback if the name is missing or invalid
        rest_name = raw_name.strip() if is_valid_name(raw_name) else "your restaurant"
        body = random.choice(TEMPLATES).format(restaurant=rest_name)
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = "A quick question about your menu"
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            # 1. Connect fresh for EVERY email to avoid idle timeouts
            server = smtplib.SMTP("smtp.zoho.com", 587)
            server.starttls()
            server.login(sender_email, app_password)
            
            server.send_message(msg)
            server.quit() # Close connection immediately
            
            print(f"Sent to: {recipient} (Used name: {rest_name})")
            
            # 2. Update memory and save to CSV instantly
            row['Status'] = 'Sent'
            row['DateSent'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            processed_count += 1
            
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            # 3. Wait exactly 2 minutes (except after the final email)
            if processed_count < len(batch):
                print("Waiting 2 minutes before the next email...")
                time.sleep(120)
                
        except Exception as e:
            print(f"Failed to send to {recipient}. Error: {e}")
            # If an email fails, ensure we still wait before trying the next one
            if processed_count < len(batch):
                time.sleep(120)

if __name__ == "__main__":
    run_batch_mailer(batch_limit=25)
