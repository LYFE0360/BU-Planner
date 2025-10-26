# BU Course Planner

An interactive course planning tool for Boston University students with AI-powered features.

## Overview

This is a full-stack web application that helps BU students:
- Browse and search through the course catalog
- Plan their semester schedule with drag-and-drop interface
- Get AI-powered career recommendations
- Track degree progress
- Research professors and generate cold emails
- Chat with an AI assistant for course planning help

## Project Status

**Current State**: Fully functional and ready for use
**Last Updated**: October 26, 2025
**Environment**: Replit

## Tech Stack

### Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **UI Components**: Lucide React icons, React Flow for visualizations
- **Features**: Drag-and-drop course planning, AI chatbot widget

### Backend
- **Framework**: FastAPI (Python)
- **AI Integration**: Google Gemini API
- **Data Processing**: Pandas for course data
- **Research Data**: OpenAlex API for professor research
- **CORS**: Configured for Replit domains

### Development Environment
- **Frontend Port**: 5000 (webview)
- **Backend Port**: 8000 (console)
- **Node.js**: v20
- **Python**: v3.11

## Key Features

### 1. AI Chatbot 🤖
- Floating chat widget on all pages
- Powered by Google Gemini API
- Helps with course planning, prerequisites, and academic advising
- Maintains conversation history
- Located in bottom-right corner of every page

### 2. Course Catalog
- Browse 1000+ BU courses
- Search by department, level, or keywords
- View course details including prerequisites

### 3. Semester Planner
- Drag-and-drop interface
- Multi-semester planning
- Prerequisite validation
- Export to PDF

### 4. AI Career Advisor
- Analyzes career goals
- Recommends optimal course paths
- Calculates skill coverage percentage
- Works for any career path

### 5. Professor Research
- View professor research areas
- OpenAlex integration for publication data
- AI-generated cold email templates

## Project Architecture

```
BU-Planner/
├── frontend/                  # React TypeScript app
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   │   ├── Chatbot.tsx   # AI chatbot widget
│   │   │   ├── Layout.tsx    # Main layout
│   │   │   └── ...
│   │   ├── pages/            # Route pages
│   │   ├── services/         # API integration
│   │   │   └── api.ts        # Axios config with Replit domain handling
│   │   └── store/            # Zustand state
│   ├── vite.config.ts        # Vite config (port 5000, allow all hosts)
│   └── package.json
│
├── backend/                   # FastAPI Python app
│   ├── app/
│   │   ├── routes.py         # API endpoints including /api/chatbot/
│   │   ├── ai_advisor.py     # Google Gemini integration
│   │   ├── config.py         # Environment configuration
│   │   ├── openalex_service.py  # Professor research
│   │   └── professor_data.py
│   ├── data/                 # Course data
│   ├── processing_csv/       # Course data processing
│   └── requirements.txt
│
└── replit.md                 # This file
```

## Recent Changes

### October 26, 2025
- ✅ Configured for Replit environment
- ✅ Updated Vite to bind to 0.0.0.0:5000 with allowedHosts
- ✅ Updated backend CORS to allow all origins (Replit proxy)
- ✅ Frontend API URL auto-detects Replit domains
- ✅ Added AI chatbot feature with floating widget
- ✅ Created /api/chatbot/ endpoint for AI conversations
- ✅ Integrated chatbot into all pages via App.tsx
- ✅ Set up workflows for frontend and backend
- ✅ Configured deployment settings

## Environment Variables

### Backend (.env)
```
GOOGLE_API_KEY=your_api_key_here  # Required for AI features
DEBUG=True
```

To get your Google API key:
1. Visit https://aistudio.google.com/app/apikey
2. Sign in and create an API key
3. Add it to Replit Secrets as GOOGLE_API_KEY

### Frontend (.env - optional)
```
VITE_API_URL=http://localhost:8000  # Auto-detected in Replit
```

## API Endpoints

### Courses
- `GET /api/courses/` - List all courses
- `GET /api/courses/{id}` - Get course details
- `GET /api/courses/search/` - Search courses
- `GET /api/departments/` - List departments
- `GET /api/subjects/` - List subjects

### AI Features
- `POST /api/ai-advisor/` - Get career recommendations
- `POST /api/chatbot/` - Chat with AI assistant
- `POST /api/gemini/` - Direct Gemini API access

### Professors
- `GET /api/professors/` - List professors
- `GET /api/professors/{name}` - Professor details with research
- `POST /api/professors/cold-email` - Generate email template

## Running Locally

The app runs automatically in Replit, but for local development:

### Frontend
```bash
cd frontend
npm install
npm run dev  # Runs on port 5000
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host localhost --port 8000 --reload
```

## Deployment

Configured for Replit Autoscale deployment:
- Frontend serves from dist/ folder
- Backend runs with Gunicorn for production
- Both services deployed together

## User Preferences

None specified yet.

## Known Issues & Future Enhancements

### Current Limitations
- AI features require Google API key
- Course data is static (loaded from JSON)
- No user authentication (planned)

### Planned Features
- User accounts and saved plans
- Course enrollment integration
- Real-time course availability
- Mobile app version

## Support

For issues or questions:
1. Check the chatbot for quick help
2. Review API documentation at `/docs` (FastAPI auto-docs)
3. Contact development team

## Notes for Developers

- Frontend uses Vite's HMR for fast development
- Backend auto-reloads on file changes
- CORS is permissive for Replit environment
- API base URL auto-detects Replit domain structure
- Chatbot appears on all routes via App.tsx wrapper
- LSP diagnostics are minor (mostly import warnings)
