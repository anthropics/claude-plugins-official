# GetAnswers Ask

Ask a question against your AI knowledge base.

## Usage

```
/getanswers-ask [question] [--kb knowledge-base-id]
```

## What This Does

1. Sends question to GetAnswers AI
2. Retrieves relevant sources from knowledge base
3. Generates accurate answer with citations
4. Shows confidence score and sources

## Example Output

```
Question: "How do I reset my password?"

Answer:
To reset your password, follow these steps:

1. Go to the login page and click "Forgot Password"
2. Enter your email address
3. Check your inbox for the reset link (expires in 1 hour)
4. Click the link and enter your new password
5. Password must be at least 8 characters with 1 number

Confidence: 95% ✅

Sources:
├── help-center/account/password-reset.md (similarity: 0.94)
├── faq/authentication.md (similarity: 0.87)
└── user-guide/getting-started.md (similarity: 0.72)

Related Questions:
- How do I enable two-factor authentication?
- Why isn't my password reset email arriving?
- How do I change my email address?
```
