# Chatbot Setup Guide

## Current Status
✅ Chatbot is now working with **fallback responses** (rule-based)
⚠️ AI-powered responses require a Google API key

## How the Chatbot Works Now

### Without API Key (Current State)
The chatbot provides intelligent rule-based responses for common questions:
- Finding and searching courses
- Planning semesters
- Getting career recommendations
- Researching professors
- General navigation help

### With API Key (Enhanced Mode)
When you add a Google API key, the chatbot will use Google Gemini AI for:
- More natural, conversational responses
- Better understanding of complex questions
- Context-aware answers based on conversation history

## Adding Your Google API Key (Optional)

### Step 1: Get a Free API Key
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your new API key

### Step 2: Add to Backend
1. Open `backend/.env` file
2. Replace the empty value with your key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```
3. Save the file

### Step 3: Restart Backend
```bash
cd backend
# Stop the current backend (Ctrl+C)
# Restart it
python -m uvicorn app.main:app --reload
```

## Testing the Chatbot

Try asking these questions:
- "How do I search for courses?"
- "Where can I plan my semesters?"
- "How do I get career recommendations?"
- "Where can I find professor information?"
- "How do I export my plan to PDF?"

The chatbot should provide helpful navigation directions!

## Troubleshooting

### Chatbot shows error message
- Check that the backend is running on http://localhost:8000
- Check browser console for network errors
- Verify the frontend can reach the backend

### Chatbot gives generic responses
- This is normal without an API key
- The fallback responses are designed to be helpful
- Add an API key for AI-enhanced responses

### API key not working
- Verify the key is correctly copied (no extra spaces)
- Check that the `.env` file is in the `backend/` directory
- Restart the backend after adding the key
- Check backend logs for API key validation messages

## Features

The chatbot is knowledgeable about:
- All 5 main pages (Home, Explorer, Planner, Progress, Professors)
- How to use each feature
- Navigation instructions
- Course search and filtering
- Semester planning workflow
- Career advisor usage
- Professor research tools

## Security Note
⚠️ Never commit your actual API key to Git!
- The `.env` file is in `.gitignore`
- Only the `.env.example` file should be committed
- Keep your API key private
