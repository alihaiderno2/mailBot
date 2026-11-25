import os
import csv
import smtplib
import random
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Concise follow-up templates
FOLLOWUP_TEMPLATES = [
    "Hi,\n\nJust floating this to the top of your inbox—would {restaurant} be interested in a quick look at how our 3D menus work?\nDemo: https://www.instagram.com/reels/Dd6kcBeujb8/ | www.plated3d.tech\n\nBest,\nCasey",
    
    "Hello,\n\nFollowing up on my last note about bringing interactive 3D QR menus to {restaurant}. Happy to build a quick sample dish for you to test.\nDetails at www.plated3d.tech.\n\nCheers,\nCasey",
    
    "Hi there,\n\nQuick follow-up—did you get a chance to check out the 3D menu demo for {restaurant}?\nWatch it here: https://www.instagram.com/reels/Dd6kcBeujb8/\n\nThanks,\nCasey",
    
    "Greetings,\n\nJust checking in to see if {restaurant} is exploring any menu upgrades this month. Our 3D AR menus take seconds for diners to scan.\nMore at www.plated3d.tech.\n\nBest,\nCasey"
]

def is_valid_name(name):
    if not name:
        return False
    invalid_markers = ['null', 'none', 'nan', 'na', 'n/a', 'missing', 'undefined']
    clean_name = str(name).strip().lower()
    if clean_name in invalid_markers or len(clean_name) < 2:
        return False
    return True

def is_ready_for_followup(date_sent_str, min_days=3):
    """Returns True if at least `min_days` have passed since the initial email."""
    if not date_sent_str:
        return False
    try:
        sent_dt = datetime.strptime(date_sent_str.strip(), "%Y-%m-%d %H:%M")
        return datetime.now() - sent_dt >= timedelta(days=min_days)
    except ValueError:
        return False

def run_followup_mailer(batch_limit=25, wait_days=3):
    sender_email = os.environ.get("BOT_EMAIL")
    app_password = os.environ.get("BOT_PASSWORD")
    csv_filename = "Pakistan Restaurants Leads - Verified Emails.csv"
    
    rows = []
    try:
        with open(csv_filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = list(reader.fieldnames) if reader.fieldnames else []
            
            # Auto-inject follow-up tracking columns
            for col in ['Status', 'DateSent', 'FollowUpStatus', 'FollowUpDate']:
                if col not in fieldnames:
                    fieldnames.append(col)
                
            for row in reader:
                row.setdefault('Status', '')
                row.setdefault('DateSent', '')
                row.setdefault('FollowUpStatus', '')
                row.setdefault('FollowUpDate', '')
                rows.append(row)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_filename}.")
        return

    # Filter: Initial email sent, follow-up NOT sent, and at least `wait_days` have passed
    pending_followups = [
        row for row in rows
        if row.get('Status') == 'Sent'
        and row.get('FollowUpStatus') != 'Sent'
        and is_ready_for_followup(row.get('DateSent', ''), min_days=wait_days)
    ]
    
    batch = pending_followups[:batch_limit]
    
    if not batch:
        print("No contacts are currently ready for a follow-up. Exiting.")
        return

    print(f"Starting follow-up batch of {len(batch)} emails...")
    processed_count = 0
    
    for row in batch:
        recipient = row.get('Email', '').strip()
        raw_name = row.get('Name', '')
        
        if not recipient:
            continue
        
        rest_name = raw_name.strip() if is_valid_name(raw_name) else "your restaurant"
        body = random.choice(FOLLOWUP_TEMPLATES).format(restaurant=rest_name)
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = "Re: A quick question about your menu"
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP("smtp.zoho.com", 587)
            server.starttls()
            server.login(sender_email, app_password)
            
            server.send_message(msg)
            server.quit()
            
            print(f"Follow-up sent to: {recipient} (Used name: {rest_name})")
            
            row['FollowUpStatus'] = 'Sent'
            row['FollowUpDate'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            processed_count += 1
            
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            if processed_count < len(batch):
                print("Waiting 2 minutes before the next follow-up...")
                time.sleep(120)
                
        except Exception as e:
            print(f"Failed to send follow-up to {recipient}. Error: {e}")
            if processed_count < len(batch):
                time.sleep(120)

if __name__ == "__main__":
    run_followup_mailer(batch_limit=25, wait_days=3)
