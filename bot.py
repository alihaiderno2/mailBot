import os
import csv
import smtplib
import random
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Define your rotating templates here
TEMPLATES = [
    "Hello,\n\nI was looking at {restaurant} and wanted to share a quick idea about your menu.\n\nBest,\nAli",
    "Hi there,\n\nWe help businesses like {restaurant} transition to interactive 3D menus.\n\nCheers,\nAli",
    "Greetings,\n\nI noticed {restaurant} recently and wanted to connect regarding a 3D web experience for your customers.\n\nThanks,\nAli",
    "Hello,\n\nWould {restaurant} be open to upgrading its digital presence with an interactive QR menu?\n\nBest,\nAli"
]

def run_batch_mailer(batch_limit=25):
    sender_email = os.environ.get("BOT_EMAIL")
    app_password = os.environ.get("BOT_PASSWORD")
    csv_filename = "contacts.csv"
    
    # Read the CSV
    rows = []
    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
            
    # Filter for unsent emails
    pending_rows = [row for row in rows if row.get('Status') != 'Sent']
    batch = pending_rows[:batch_limit]
    
    if not batch:
        print("No pending emails left in the CSV. Exiting.")
        return

    try:
        print(f"Connecting to SMTP. Sending {len(batch)} emails...")
        server = smtplib.SMTP("smtp.zoho.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        
        for row in batch:
            recipient = row['Email']
            
            # Use placeholder if restaurant name is missing or blank
            raw_name = row.get('Restaurant', '').strip()
            rest_name = raw_name if raw_name else "your restaurant"
            
            # Randomly select a template and inject the name
            body = random.choice(TEMPLATES).format(restaurant=rest_name)
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient
            msg['Subject'] = "A quick question about your menu" # Or randomize subjects too
            msg.attach(MIMEText(body, 'plain'))
            
            server.send_message(msg)
            print(f"Sent to: {recipient}")
            
            # Mark as sent in memory
            row['Status'] = 'Sent'
            row['DateSent'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Wait 30-60 seconds between emails to heavily avoid spam filters
            time.sleep(random.randint(30, 60))
            
        server.quit()
        
        # Write the updated rows back to the CSV
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            
        print("Batch complete. CSV updated.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Send up to 25 emails per run
    run_batch_mailer(batch_limit=25)
