import os
import csv
import smtplib
import random
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Updated concise templates with links
TEMPLATES = [
    "Hi,\n\nI was looking at {restaurant} and wanted to show how our interactive 3D menus can elevate your dining experience.\nCheck out a quick demo: https://www.instagram.com/reels/Dd6kcBeujb8/\nLearn more at www.plated3d.tech.\n\nBest,\nAli",
    
    "Hello,\n\nWe help restaurants like {restaurant} stand out and increase order sizes with QR-code 3D menus.\nSee it in action here: https://www.instagram.com/reels/Dd6kcBeujb8/\nVisit www.plated3d.tech to upgrade your menu.\n\nCheers,\nAli",
    
    "Greetings,\n\nWould {restaurant} be open to upgrading to a 3D interactive menu? It takes customers seconds to scan and view.\nWatch how it works: https://www.instagram.com/reels/Dd6kcBeujb8/\nDiscover more at www.plated3d.tech.\n\nThanks,\nAli",
    
    "Hi there,\n\nI noticed {restaurant} and thought our 3D AR menus would perfectly showcase your amazing dishes.\nDemo the technology: https://www.instagram.com/reels/Dd6kcBeujb8/\nDetails at www.plated3d.tech.\n\nBest,\nAli"
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
    csv_filename = "Pakistan Restaurants Leads - Verified Emails.csv"
    
    rows = []
    try:
        with open(csv_filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = list(reader.fieldnames) if reader.fieldnames else []
            
            if 'Status' not in fieldnames:
                fieldnames.append('Status')
            if 'DateSent' not in fieldnames:
                fieldnames.append('DateSent')
                
            for row in reader:
                row.setdefault('Status', '')
                row.setdefault('DateSent', '')
                rows.append(row)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_filename}. Make sure it is uploaded to the repository.")
        return
            
    pending_rows = [row for row in rows if row.get('Status') != 'Sent']
    batch = pending_rows[:batch_limit]
    
    if not batch:
        print("No pending emails left in the CSV. Exiting.")
        return

    print(f"Starting batch of {len(batch)} emails...")
    processed_count = 0
    
    for row in batch:
        recipient = row.get('Email', '').strip()
        raw_name = row.get('Name', '')
        
        if not recipient:
            continue
        
        rest_name = raw_name.strip() if is_valid_name(raw_name) else "your restaurant"
        body = random.choice(TEMPLATES).format(restaurant=rest_name)
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = "A quick question about your menu"
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP("smtp.zoho.com", 587)
            server.starttls()
            server.login(sender_email, app_password)
            
            server.send_message(msg)
            server.quit() 
            
            print(f"Sent to: {recipient} (Used name: {rest_name})")
            
            row['Status'] = 'Sent'
            row['DateSent'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            processed_count += 1
            
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            if processed_count < len(batch):
                print("Waiting 2 minutes before the next email...")
                time.sleep(120)
                
        except Exception as e:
            print(f"Failed to send to {recipient}. Error: {e}")
            if processed_count < len(batch):
                time.sleep(120)

if __name__ == "__main__":
    run_batch_mailer(batch_limit=25)
