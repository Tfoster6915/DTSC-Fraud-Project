import re

CRIME_PATTERNS = {
    "phishing": ["phishing", "spoofing", "email scam", "email fraud", "fake email", "smishing", "vishing"],
    "extortion": ["extortion", "blackmail", "ransom demand"],
    "personal_data_breach": ["data breach", "information leak", "personal data exposure"],
    "non_payment_non_delivery": ["non-payment", "non delivery", "failed delivery", "did not pay", "didn't pay"],
    "investment": ["investment fraud", "ponzi scheme", "pyramid scheme", "securities fraud"],
    "tech_support": ["tech support scam", "fake tech help", "technical support fraud"],
    "business_email_compromise": ["business email compromise", "bec scam", "ceo fraud"],
    "identity_theft": ["identity theft", "id theft", "stolen identity", "identity fraud"],
    "employment": ["employment scam", "job scam", "fake job posting"],
    "confidence_romance": ["romance scam", "dating scam", "catfishing"],
    "government_impersonation": ["government impersonation", "fake irs", "fake police", "fake fbi"],
    "credit_card_check_fraud": ["credit card fraud", "check fraud", "bank fraud"],
    "harassment_stalking": ["harassment", "stalking", "cyberstalking"],
    "real_estate": ["real estate fraud", "property scam", "mortgage fraud"],
    "advanced_fee": ["advanced fee scam", "upfront fee", "prepayment scam"],
    "crimes_against_children": ["child exploitation", "child abuse", "child pornography"],
    "lottery_sweepstakes_inheritance": ["lottery scam", "sweepstakes fraud", "inheritance scam"],
    "ransomware": ["ransomware", "malware ransom"],
    "overpayment": ["overpayment scam", "refund scam"],
    "ipr_copyright_counterfeit": ["copyright infringement", "counterfeit goods", "fake products"],
    "threats_of_violence": ["threats", "violence threats"],
    "sim_swap": ["sim swap", "sim hijacking"],
    "botnet": ["botnet", "ddos network"],
    "malware": ["malware", "virus infection", "trojan"],
    "cryptocurrency": ["crypto scam", "bitcoin fraud", "cryptocurrency scam", "crypto theft"]
}

FRAUD_REGEX = {k: re.compile("|".join([re.escape(term) for term in v]), re.I) for k, v in CRIME_PATTERNS.items()}