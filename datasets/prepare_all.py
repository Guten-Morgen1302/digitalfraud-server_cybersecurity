"""
ShieldGuard Dataset Preparation Script
Run: python datasets/prepare_all.py
Downloads all public datasets + generates synthetic Hinglish data.
"""
import os, json, random
import pandas as pd

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

print("=== Step 1: HuggingFace Datasets ===")
try:
    from datasets import load_dataset
    ds = load_dataset("cybersectony/PhishingEmailDetectionv2.0", split="train")
    pd.DataFrame(ds).to_csv("data/raw/phishing_emails.csv", index=False)
    print(f"✓ Phishing emails: {len(ds)} samples")
except Exception as e:
    print(f"✗ Phishing emails: {e}")

try:
    from datasets import load_dataset
    sms = load_dataset("ealvaradob/phishing-dataset", "sms_dataset", split="train")
    pd.DataFrame(sms).to_csv("data/raw/sms_phishing.csv", index=False)
    print(f"✓ SMS phishing: {len(sms)} samples")
except Exception as e:
    print(f"✗ SMS phishing: {e}")

print("\n=== Step 2: Kaggle Datasets (Manual) ===")
print("Run these commands after: kaggle configure (add API key)")
kaggle_cmds = [
    "kaggle datasets download -d narayanyadav/fraud-call-india-dataset -p data/raw/",
    "kaggle datasets download -d teeconnie/scam-and-non-scam-call-conversation-dataset -p data/raw/",
    "kaggle datasets download -d junioralive/india-spam-sms-classification -p data/raw/",
    "kaggle datasets download -d xhlulu/140k-real-and-fake-faces -p data/raw/",
]
for cmd in kaggle_cmds:
    print(f"  {cmd}")

print("\n=== Step 3: GitHub Vishing Dataset ===")
os.system("git clone https://github.com/kimdesok/Text-classification-of-voice-phishing-transcipts data/raw/vishing_github 2>/dev/null || echo 'Already cloned'")

print("\n=== Step 4: Synthetic Hinglish Generator ===")
SCAM_TEMPLATES = [
    "Namaskar, main {officer} bol raha hun {dept} se. Aapke naam pe {crime} ka case registered hai. Abhi {amount} transfer karo warna digital arrest ho jayega.",
    "Sir aapka {bank} account band hone wala hai. KYC update ke liye abhi OTP share karo {phone} pe.",
    "Congratulations! Aapne {prize} jeeta hai. Claim karne ke liye {amount} processing fee aur PAN number bhejo.",
    "Main {name} hun, CBI officer. Aapke Aadhaar se {crime} hua hai. Digital arrest se bachne ke liye {amount} online transfer karo.",
    "URGENT: Aapka {bank} UPI band ho raha hai. Abhi OTP share karo verify karne ke liye.",
    "Ye {dept} se call hai. Aapke account mein suspicious activity detect hui. Turant {amount} safe account mein transfer karo.",
    "{bank} Alert: Aapka account suspend ho jayega. KYC update ke liye abhi click karo: http://bit.ly/fake{num}",
    "Lottery winner! Aapne {prize} jeeta. Processing ke liye {amount} pay karo. OTP: {otp_num}",
]

LEGIT_TEMPLATES = [
    "{bank} se call kar raha hun. Aapki EMI {amount} ki due hai {date} ko. Please samay pe pay karein.",
    "Hello, main {company} ka customer service hun. Aapki complaint #{num} resolve ho gayi hai.",
    "{bank} Alert: Aapke account mein {amount} credited hua. Balance check karein app se.",
    "Namaste! Aapka {company} subscription renew hone wala hai {date} ko. Koi problem ho to batao.",
    "Sir, aapke {bank} credit card ka bill {amount} hai. Due date {date} hai.",
    "Aapki {company} delivery {date} ko hogi. Track karein: {company}.com/track/{num}",
]

FILL = {
    "officer": ["Rajesh Kumar", "Amit Singh", "Priya Sharma", "Suresh Verma", "DCP Agarwal"],
    "dept": ["CBI", "ED", "Income Tax", "Cyber Cell", "RBI", "TRAI"],
    "crime": ["money laundering", "tax evasion", "drug trafficking", "UPI fraud", "identity theft"],
    "amount": ["50,000", "1,00,000", "25,000", "2,00,000", "75,000", "10,000"],
    "bank": ["SBI", "HDFC", "ICICI", "Axis", "PNB", "Kotak", "BOB"],
    "phone": ["+91-9XXXXXXXX", "this number", "1800-XXX-XXXX"],
    "prize": ["iPhone 15 Pro", "₹10 lakh lottery", "Honda City car", "foreign trip", "₹50,000 cash"],
    "name": ["SP Verma", "DCP Agarwal", "SSP Mishra", "Officer Sharma"],
    "company": ["Amazon", "Flipkart", "Swiggy", "Zomato", "Jio", "Airtel"],
    "date": ["15 May", "20 May", "31 May", "10 June"],
    "num": [str(random.randint(1000, 9999)) for _ in range(20)],
    "otp_num": [str(random.randint(100000, 999999)) for _ in range(20)],
}

def fill_template(template):
    result = template
    for k, options in FILL.items():
        result = result.replace(f"{{{k}}}", random.choice(options))
    return result

synthetic = []
for template in SCAM_TEMPLATES:
    for _ in range(250):
        synthetic.append({"text": fill_template(template), "label": 1, "lang": "hinglish"})

for template in LEGIT_TEMPLATES:
    for _ in range(334):
        synthetic.append({"text": fill_template(template), "label": 0, "lang": "hinglish"})

random.shuffle(synthetic)
pd.DataFrame(synthetic).to_csv("data/raw/synthetic_hinglish.csv", index=False)
print(f"✓ Synthetic Hinglish: {len(synthetic)} samples ({sum(1 for s in synthetic if s['label']==1)} scam, {sum(1 for s in synthetic if s['label']==0)} legit)")

print("\n✅ Done! Next: python datasets/combine.py")
