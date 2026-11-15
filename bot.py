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
    """Filters out empty, blank, or placeholder names."""
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
    # Updated to your exact file name
    csv_filename = "Pakistan Restaurants Leads - Verified Emails.csv"
    
    rows = []
    try:
        with open(csv_filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            # Safely capture existing columns
            fieldnames = list(reader.fieldnames) if reader.fieldnames else []
            
            # Automatically inject missing tracking columns if they don't exist
            if 'Status' not in fieldnames:
                fieldnames.append('Status')
            if 'DateSent' not in fieldnames:
                fieldnames.append('DateSent')
                
            for row in reader:
                # Ensure every row has the tracking columns, even if empty
                row.setdefault('Status', '')
                row.setdefault('DateSent', '')
                rows.append(row)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_filename}. Make sure it is uploaded to the repository.")
        return
            
    # Filter for unsent emails
    pending_rows = [row for row in rows if row.get('Status') != 'Sent']
    batch = pending_rows[:batch_limit]
    
    if not batch:
        print("No pending emails left in the CSV. Exiting.")
        return

    print(f"Starting batch of {len(batch)} emails...")
    processed_count = 0
    
    for row in batch:
        recipient = row.get('Email', '').strip()
        # Extracts from the 'Name' column found in your new CSV
        raw_name = row.get('Name', '')
        
        if not recipient:
            continue # Skip if the email field itself is totally blank
        
        # Apply the fallback if the restaurant name is missing or invalid
        rest_name = raw_name.strip() if is_valid_name(raw_name) else "your restaurant"
        body = random.choice(TEMPLATES).format(restaurant=rest_name)
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = "A quick question about your menu"
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            # 1. Open micro-connection
            server = smtplib.SMTP("smtp.zoho.com", 587)
            server.starttls()
            server.login(sender_email, app_password)
            
            # 2. Send and immediately disconnect
            server.send_message(msg)
            server.quit() 
            
            print(f"Sent to: {recipient} (Used name: {rest_name})")
            
            # 3. Save progress to memory instantly
            row['Status'] = 'Sent'
            row['DateSent'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            processed_count += 1
            
            # 4. Write back to the CSV instantly
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            # 5. Rate limit: 2 minutes (120 seconds)
            if processed_count < len(batch):
                print("Waiting 2 minutes before the next email...")
                time.sleep(120)
                
        except Exception as e:
            print(f"Failed to send to {recipient}. Error: {e}")
            if processed_count < len(batch):
                time.sleep(120)

if __name__ == "__main__":
    run_batch_mailer(batch_limit=25)
