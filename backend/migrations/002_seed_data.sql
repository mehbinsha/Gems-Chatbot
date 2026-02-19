INSERT OR IGNORE INTO admin_users (email, password_hash)
VALUES (
    'admin@example.com',
    'scrypt:32768:8:1$dXiPbkZAaNs4uO9x$6dc60ca81e264d3a32e403152b480d2f77a41c8b56162a8c095dfce50b1974ff54043189c49f31e62e1d512880cdab3748559d8df04447e993518e5fb4d019d2'
);

INSERT OR IGNORE INTO intents (tag, patterns, responses)
VALUES
(
    'greeting',
    '["hi","hello","hey","good morning"]',
    '["Hello. How can I help you today?","Hi there. What can I do for you?"]'
),
(
    'admission',
    '["admission process","how can I apply","eligibility for admission"]',
    '["Admissions open during the academic cycle. Apply online or visit the office.","Please submit the application form with required documents."]'
),
(
    'fallback',
    '[]',
    '["I did not understand that. Could you rephrase?","Please clarify your question and I will help."]'
);
