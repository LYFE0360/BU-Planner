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
    from app.ai_advisor import generate_ai_response
    
    user_message = request.get("message", "")
    chat_history = request.get("history", [])
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    courses = get_all_courses()
    course_count = len(courses)
    
    website_knowledge = f"""
WEBSITE STRUCTURE & NAVIGATION:
The BU Course Planner has 5 main sections accessible from the top navigation bar:

1. HOME (/) - Landing page
   - Overview of the application
   - Quick links to all features
   - "Browse Courses" button → goes to Explorer
   - "Plan Your Semester" button → goes to Planner
   - "Get AI Recommendations" button → goes to Progress
   - "View Professors" button → goes to Professors page

2. EXPLORER (/explorer) - Course Catalog Browser
   - Search bar to search courses by name, code, or keywords
   - Filter by department dropdown
   - Filter by level (Introductory, Intermediate, Advanced, Graduate)
   - Shows all {course_count} BU courses
   - Click any course card to see full details in a modal

3. PLANNER (/planner) - Semester Planning Tool
   - Drag-and-drop interface for planning courses
   - Add semesters with "Add Semester" button
   - Drag courses from catalog to semester boards
   - Export plan to PDF with "Export to PDF" button
   - Visual prerequisite flow diagram
   - Prerequisites are validated automatically

4. PROGRESS (/progress) - AI Career Advisor
   - Two modes: "Browse Career Paths" and "AI Custom Advisor"
   - Browse preset career paths (Software Engineer, Data Scientist, etc.)
   - OR enter ANY custom career goal for AI recommendations
   - AI analyzes your goal and recommends optimal courses
   - Shows skill coverage percentage
   - Displays required skills for the career
   - Click "Get Recommendations" to use AI (requires API key)

5. PROFESSORS (/professors) - Professor Research
   - Browse all BU professors
   - Filter by department
   - Click professor name to see research details
   - View publications from OpenAlex
   - Generate AI-powered cold emails to professors
   - See research areas and collaborators

FEATURES:
✅ AI-Powered Career Recommendations - Get personalized course suggestions for ANY career goal
✅ Course Search & Filtering - Find courses by department, level, keywords
✅ Drag-and-Drop Planning - Visual semester planning interface
✅ Prerequisite Validation - Automatic checking of course prerequisites
✅ PDF Export - Download your semester plan
✅ Professor Research - View professor publications and research areas
✅ AI Cold Email Generator - Create professional emails to professors
✅ This AI Chatbot - Get help navigating the site and planning courses

HOW TO USE KEY FEATURES:
- To plan a semester: Go to Planner → Add Semester → Drag courses from left sidebar
- To search courses: Go to Explorer → Use search bar or filters
- To get career advice: Go to Progress → Choose preset career OR enter custom goal → Click "Get Recommendations"
- To research professors: Go to Professors → Click on a professor name
- To export your plan: Go to Planner → Click "Export to PDF" button

DATA AVAILABLE:
- {course_count} BU courses from 2022 onwards
- Course codes, titles, credits, levels, departments
- Professor information with OpenAlex research data
- AI-powered analysis using Google Gemini
"""

    context = f"""You are an AI assistant for the BU Course Planner website. You help Boston University students with course planning and navigating the website.

{website_knowledge}

Previous conversation:
{chr(10).join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-5:]])}

Current user question: {user_message}

INSTRUCTIONS:
- Be helpful, friendly, and conversational
- Give specific navigation directions (e.g., "Click on 'Planner' in the top menu")
- If asked about location of features, reference the navigation structure above
- Suggest relevant features based on user needs
- Keep responses concise but informative
- If asked about courses, mention specific course codes when relevant
- Guide users to the right page for their needs"""
    
    try:
        response = await generate_ai_response(context)
        return {
            "response": response.get("result", ""),
            "model": response.get("model", ""),
            "message": user_message
        }
    except HTTPException as e:
        if "GOOGLE_API_KEY" in str(e.detail):
            raise HTTPException(
                status_code=503,
                detail="AI chatbot is not configured. The Google API key is missing. Please contact an administrator."
            )
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")