from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict
import json
import re
import os
from pathlib import Path
from app.ai_advisor import generate_ai_response

router = APIRouter()

# Load courses from JSON file instead of hardcoding
def load_courses_from_json():
    """Load courses from the processed JSON file"""
    try:
        # Path to the processed courses JSON file
        json_path = Path(__file__).parent.parent / "processing_csv" / "processed_courses_2022_onwards.json"
        
        if not json_path.exists():
            # Fallback to sample file if main file doesn't exist
            json_path = Path(__file__).parent.parent / "processing_csv" / "processed_courses_sample.json"
            if not json_path.exists():
                print("❌ No course data files found. Run the CSV processor first.")
                return []
        
        with open(json_path, 'r', encoding='utf-8') as f:
            courses_data = json.load(f)
        
        print(f"✅ Loaded {len(courses_data)} courses from {json_path.name}")
        return courses_data
        
    except Exception as e:
        print(f"❌ Error loading courses from JSON: {e}")
        return []

def get_all_courses():
    """Helper function to get all courses from JSON file"""
    return load_courses_from_json()

def enhance_course_data(course):
    """Add missing fields that were in the hardcoded data but not in processed data"""
    enhanced = course.copy()
    
    # Add fields that were in hardcoded data but might be missing in processed data
    enhanced.setdefault('short_title', course.get('title', ''))
    # Remove description since it's not available
    enhanced.setdefault('credits', 4.0)  # Assume 4 credits for every course
    enhanced.setdefault('component', 'LEC')  # Default to Lecture
    enhanced.setdefault('repeatable', False)
    enhanced.setdefault('consent_required', False)
    enhanced.setdefault('prerequisites', {"required": [], "recommended": []})
    enhanced.setdefault('hub_requirements', [])
    
    return enhanced

@router.get("/api/ai/models")
async def list_ai_models():
    """Return available AI models from the configured Google client for debugging."""
    try:
        import google.generativeai as genai
        from app.config import Config

        if not Config.GOOGLE_API_KEY:
            raise HTTPException(status_code=400, detail="GOOGLE_API_KEY not configured on server")

        genai.configure(api_key=Config.GOOGLE_API_KEY)
        models = genai.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/courses/")
async def list_courses():
    """Get all courses from JSON file"""
    courses = get_all_courses()
    enhanced_courses = [enhance_course_data(course) for course in courses]
    return {"courses": enhanced_courses, "total": len(enhanced_courses)}

@router.get("/api/courses/{course_id}")
async def get_course(course_id: str):
    """Get a specific course by ID"""
    courses = get_all_courses()
    course = next((c for c in courses if c["id"] == course_id), None)
    if not course:
        # Also try searching by code as fallback
        course = next((c for c in courses if c.get("code") == course_id), None)
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return enhance_course_data(course)

@router.get("/api/courses/search/")
async def search_courses(q: str = "", department: str = None, level: str = None):
    """Search courses by query with optional filters"""
    courses = get_all_courses()
    
    if not q and not department and not level:
        enhanced_courses = [enhance_course_data(course) for course in courses]
        return {"courses": enhanced_courses, "total": len(enhanced_courses)}
    
    query = q.lower() if q else ""
    results = []
    
    for course in courses:
        # Text search
        text_match = True
        if query:
            text_match = (
                query in course.get("code", "").lower() or
                query in course.get("title", "").lower() or
                query in course.get("subject", "").lower() or
                query in course.get("catalog_number", "").lower() or
                query in course.get("department", "").lower()
            )
        
        # Department filter
        dept_match = True
        if department:
            dept_match = (
                department.lower() in course.get("department", "").lower() or
                department.lower() in course.get("academic_group", "").lower() or
                department.lower() in course.get("academic_org", "").lower()
            )
        
        # Level filter
        level_match = True
        if level:
            level_match = level.lower() in course.get("level", "").lower()
        
        if text_match and dept_match and level_match:
            results.append(enhance_course_data(course))
    
    return {"courses": results, "total": len(results)}

@router.get("/api/departments/")
async def list_departments():
    """Get all unique departments"""
    courses = get_all_courses()
    departments = set()
    
    for course in courses:
        dept = course.get('department')
        if dept and dept != '':
            departments.add(dept)
        # Also include academic org and group as departments
        org = course.get('academic_org')
        if org and org != '':
            departments.add(org)
        group = course.get('academic_group')
        if group and group != '':
            departments.add(group)
    
    return {"departments": sorted(list(departments))}

@router.get("/api/subjects/")
async def list_subjects():
    """Get all unique subjects"""
    courses = get_all_courses()
    subjects = set()
    
    for course in courses:
        subject = course.get('subject')
        if subject and subject != '':
            subjects.add(subject)
    
    return {"subjects": sorted(list(subjects))}

# AI Advisor endpoint
@router.post("/api/ai-advisor/")
async def ai_career_advisor(request: dict):
    """AI-powered career advisor"""
    from app.ai_advisor import get_career_recommendations

    career_goal = request.get("career_goal", "")
    major = request.get("major", "Computer Science")
    
    if not career_goal:
        raise HTTPException(status_code=400, detail="Career goal is required")
    
    courses = get_all_courses()
    recommendations = get_career_recommendations(
        career_goal=career_goal,
        available_courses=courses,
        current_major=major
    )
    
    return recommendations

# Professor endpoints
@router.get("/api/professors/")
async def get_professors(department: str = None):
    """Get all professors, optionally filtered by department"""
    from app.professor_data import get_all_professors, get_professors_by_department
    
    if department and department.lower() != "all":
        professors = get_professors_by_department(department)
    else:
        # Return ALL professors from all departments
        professors = get_all_professors()
    
    return {"professors": professors, "total": len(professors)}

@router.post("/api/gemini/")
async def gemini_endpoint(body: dict = Body(...)):
    """Handle requests to the Gemini AI model."""
    prompt = body.get('prompt')
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    model = body.get('model')  # optional
    # Log incoming prompt for debugging (avoid logging sensitive data in production)
    print(f"/api/gemini/ called; model={model}")
    result = await generate_ai_response(prompt, model)

    # `generate_ai_response` returns {'result': text, ...} on success.
    # If the text itself contains JSON (e.g., career recommendation JSON), parse and return it
    text = None
    if isinstance(result, dict):
        text = result.get('result')
    elif isinstance(result, str):
        text = result

    if text:
        # Try to parse JSON blob from the text
        try:
            parsed = json.loads(text)
            # If parsed is a dict and contains career recommendation keys, return it as structured JSON
            if isinstance(parsed, dict):
                return parsed
            # otherwise return as-is
            return {"result": parsed, "model": result.get('model') if isinstance(result, dict) else None}
        except Exception:
            # Not a plain JSON body; try to extract JSON substring
            try:
                m = re.search(r"\{.*\}", text, re.DOTALL)
                if m:
                    parsed = json.loads(m.group())
                    if isinstance(parsed, dict):
                        return parsed
            except Exception:
                pass

    return result

@router.get("/api/professors/{professor_name}")
async def get_professor_details(professor_name: str):
    """Get detailed professor information including OpenAlex data"""
    from app.professor_data import get_professor_by_name
    from app.openalex_service import (
        get_author_data,
        get_author_works,
        get_coauthors,
        generate_research_summary
    )
    
    professor = get_professor_by_name(professor_name)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    
    oaid = professor.get('oaid', '')
    if oaid:
        author_data = get_author_data(oaid)
        works = get_author_works(oaid, limit=10)
        coauthors = get_coauthors(oaid, limit=10)
        
        if author_data:
            research_summary = generate_research_summary(author_data, works)
            
            return {
                "professor": professor,
                "openalex_data": author_data,
                "recent_works": works,
                "coauthors": coauthors,
                "research_summary": research_summary
            }
    
    return {"professor": professor}

@router.post("/api/professors/cold-email")
async def generate_professor_email(request: dict):
    """Generate personalized cold email to professor"""
    from app.professor_data import get_professor_by_name
    from app.openalex_service import (
        get_author_data,
        get_author_works,
        generate_research_summary,
        generate_cold_email
    )
    
    professor_name = request.get("professor_name", "")
    student_interests = request.get("student_interests", "")
    course_context = request.get("course_context", "")
    
    professor = get_professor_by_name(professor_name)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    
    oaid = professor.get('oaid', '')
    if not oaid:
        raise HTTPException(status_code=400, detail="Professor has no OpenAlex ID")
    
    author_data = get_author_data(oaid)
    works = get_author_works(oaid, limit=10)
    
    if not author_data:
        raise HTTPException(status_code=500, detail="Could not fetch research data")
    
    research_summary = generate_research_summary(author_data, works)
    
    email = generate_cold_email(
        professor_name=professor_name,
        research_summary=research_summary,
        student_interests=student_interests,
        course_context=course_context
    )
    
    return {
        "email": email,
        "professor": professor_name,
        "research_areas": [c.get('display_name') for c in author_data.get('x_concepts', [])[:5]]
    }

@router.post("/api/chatbot/")
async def chatbot_conversation(request: dict):
    """AI chatbot for course planning assistance"""
    from app.config import Config
    
    user_message = request.get("message", "")
    chat_history = request.get("history", [])
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    courses = get_all_courses()
    course_count = len(courses)
    
    # Get sample departments and subjects for better responses
    departments = set()
    for course in courses[:50]:  # Sample first 50 courses
        if dept := course.get('department'):
            departments.add(dept)
    dept_list = ", ".join(sorted(list(departments))[:10])
    
    website_knowledge = f"""
WEBSITE STRUCTURE & NAVIGATION:
The BU Course Planner has 5 main sections accessible from the top navigation bar:

1. HOME (/) - Landing page with overview and quick access buttons
2. EXPLORER (/explorer) - Browse and search {course_count} BU courses with filters
3. PLANNER (/planner) - Drag-and-drop semester planning with PDF export
4. PROGRESS (/progress) - AI career advisor for personalized course recommendations
5. PROFESSORS (/professors) - Research faculty publications and generate cold emails

KEY FEATURES & HOW TO USE THEM:

📚 COURSE SEARCH (Explorer page):
- Use the search bar to find courses by name, code, or keyword
- Filter by department: {dept_list}, and more
- Filter by level: Introductory, Intermediate, Advanced, Graduate
- Click any course card to see full details

📅 SEMESTER PLANNING (Planner page):
- Click "Add Semester" button to create a new semester
- Drag courses from the left sidebar into semester boards
- Prerequisites are validated automatically
- Export your plan to PDF with the "Export to PDF" button
- Visual prerequisite flow shows course dependencies

🎯 CAREER ADVISOR (Progress page):
- Choose from preset career paths OR enter a custom career goal
- AI analyzes your goal and recommends optimal courses
- See required skills and skill coverage percentage
- Click "Get Recommendations" to get AI-powered advice

👨‍🏫 PROFESSOR RESEARCH (Professors page):
- Browse all BU professors by department
- Click a professor's name to see their research and publications
- View research areas from OpenAlex database
- Generate AI-powered professional cold emails

NAVIGATION TIPS:
- All main pages are accessible from the top navigation bar
- Home page has quick action buttons for each feature
- Use the chatbot (me!) anytime for help navigating
"""
    
    # Provide rule-based responses for common questions when API is not available
    def get_fallback_response(message: str) -> str:
        msg_lower = message.lower()
        
        # Navigation questions
        if any(word in msg_lower for word in ['find', 'search', 'look for', 'where']) and 'course' in msg_lower:
            return "To search for courses, go to the **Explorer** page (click 'Explorer' in the top menu). You can use the search bar to find courses by name or code, and use the filters to narrow by department or level."
        
        if 'plan' in msg_lower and any(word in msg_lower for word in ['semester', 'schedule']):
            return "To plan your semesters, go to the **Planner** page (click 'Planner' in the top menu). Click 'Add Semester' to create a semester, then drag courses from the left sidebar into your semester boards. You can export your plan to PDF when done!"
        
        if 'career' in msg_lower or 'recommendation' in msg_lower:
            return "For career advice and course recommendations, go to the **Progress** page (click 'Progress' in the top menu). You can browse preset career paths or enter your own custom career goal to get AI-powered course recommendations!"
        
        if 'professor' in msg_lower or 'faculty' in msg_lower:
            return "To research professors, go to the **Professors** page (click 'Professors' in the top menu). You can browse by department, view their publications, and even generate professional cold emails to reach out to them."
        
        if 'export' in msg_lower or 'pdf' in msg_lower:
            return "To export your semester plan to PDF, go to the **Planner** page and click the 'Export to PDF' button at the top. Make sure you've added some courses to your semesters first!"
        
        if any(word in msg_lower for word in ['navigate', 'use', 'how', 'help', 'guide']):
            return f"""I can help you navigate the BU Course Planner! Here are the main sections:

📚 **Explorer** - Search and browse {course_count} courses
📅 **Planner** - Drag-and-drop semester planning
🎯 **Progress** - Get AI career recommendations
👨‍🏫 **Professors** - Research faculty and publications

What would you like to do? I can give you specific directions!"""
        
        # Default response
        return f"""I'm here to help you navigate the BU Course Planner! The site has 5 main sections:

• **Home** - Overview and quick links
• **Explorer** - Search {course_count} BU courses
• **Planner** - Plan your semesters with drag-and-drop
• **Progress** - Get AI career advice
• **Professors** - Research faculty

What would you like help with? Ask me about finding courses, planning semesters, career recommendations, or researching professors!"""
    
    # Check if API key is configured
    if not Config.GOOGLE_API_KEY:
        # Provide helpful fallback response
        fallback = get_fallback_response(user_message)
        return {
            "response": fallback,
            "model": "fallback",
            "message": user_message
        }
    
    # Use AI if API key is available
    from app.ai_advisor import generate_ai_response
    
    context = f"""You are an AI assistant for the BU Course Planner website. You help Boston University students with course planning and navigating the website.

{website_knowledge}

Previous conversation:
{chr(10).join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-5:]])}

Current user question: {user_message}

INSTRUCTIONS:
- Be helpful, friendly, and conversational
- Give specific navigation directions (e.g., "Click on 'Explorer' in the top menu")
- Reference the exact page names and button labels from the website structure above
- Suggest relevant features based on user needs
- Keep responses concise (2-4 sentences) but informative
- Use emojis sparingly for visual appeal
- If asked about courses, mention that there are {course_count} courses available
- Guide users to the right page for their needs with clear step-by-step directions"""
    
    try:
        response = await generate_ai_response(context)
        return {
            "response": response.get("result", ""),
            "model": response.get("model", ""),
            "message": user_message
        }
    except Exception as e:
        # If AI fails, use fallback
        fallback = get_fallback_response(user_message)
        return {
            "response": fallback,
            "model": "fallback",
            "message": user_message
        }