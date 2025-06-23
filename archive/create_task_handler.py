#!/usr/bin/env python3
"""
CREATE_TASK Handler for MGA Bot
Insert this before the 'elif intent == "HELP"' line (around line 467)
"""

# Add these functions after the record_time_entry function (around line 260)

def create_task(task_content: str, project_id: Optional[str] = None, 
                priority: str = "mittel", tags: List[str] = None,
                behörde: Optional[str] = None, gemeinde: Optional[str] = None,
                created_by: str = None) -> bool:
    """Create a new task in Supabase"""
    if not supabase_client:
        logger.error("❌ Supabase client not initialized")
        return False
        
    try:
        task_data = {
            'content': task_content,
            'priority': priority,
            'created_by': created_by
        }
        
        # Add optional fields
        if project_id:
            task_data['project_id'] = project_id
        if tags:
            task_data['tags'] = tags
        if behörde:
            task_data['behörde'] = behörde
        if gemeinde:
            task_data['gemeinde'] = gemeinde
            
        result = supabase_client.table('tasks').insert(task_data).execute()
        
        logger.info(f"✅ Task created: {task_content[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating task: {e}")
        return False

def extract_tirol_tags(text: str) -> List[str]:
    """Extract Tirol-specific tags from text"""
    tags = []
    
    # Check for Tirol-specific keywords
    tirol_keywords = {
        'TBO': ['tbo', 'bauordnung', 'tiroler bauordnung'],
        'Stellplatz': ['stellplatz', 'parkplatz', 'tiefgarage'],
        'Schneelast': ['schneelast', 'schnee', 'dachlast'],
        'Behörde': ['bh', 'gemeinde', 'bauamt', 'bezirkshauptmannschaft'],
        'ÖBA': ['öba', 'bauaufsicht', 'örtliche bauaufsicht'],
        'Widmung': ['widmung', 'umwidmung', 'bauland'],
        'Hanglage': ['hang', 'hanglage', 'böschung'],
        'WLV': ['wlv', 'wildbach', 'lawine', 'gefahrenzone']
    }
    
    text_lower = text.lower()
    for tag, keywords in tirol_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            tags.append(tag)
            
    return tags

# Add this handler before 'elif intent == "HELP"' (around line 467)

            elif intent == "CREATE_TASK":
                # Extract task data
                task_content = ai_result.get("task_description", ai_result.get("content", ""))
                priority = ai_result.get("priority", "mittel").lower()
                project_identifier = ai_result.get("project_identifier")
                
                # Extract Tirol-specific info
                tags = extract_tirol_tags(task_content)
                behörde = ai_result.get("behörde")
                gemeinde = ai_result.get("gemeinde")
                
                # Find project if specified
                project_id = None
                project_name = None
                if project_identifier:
                    project = find_project_by_identifier(project_identifier)
                    if project:
                        project_id = project['id']
                        project_name = project['name']
                
                # Create task
                created_by = f"{user_name} ({user_id})"
                if create_task(task_content, project_id, priority, tags, behörde, gemeinde, created_by):
                    # Build response message
                    priority_emoji = {"hoch": "🔴", "mittel": "🟡", "niedrig": "🟢"}.get(priority, "🟡")
                    
                    response = f"✅ **Aufgabe erstellt!**\\n\\n"
                    response += f"{priority_emoji} **Priorität:** {priority.capitalize()}\\n"
                    response += f"📝 **Aufgabe:** {task_content}\\n"
                    
                    if project_name:
                        response += f"📁 **Projekt:** {project_name}\\n"
                    if tags:
                        response += f"🏷️ **Tags:** {', '.join(tags)}\\n"
                    if behörde:
                        response += f"🏛️ **Behörde:** {behörde}\\n"
                    if gemeinde:
                        response += f"📍 **Gemeinde:** {gemeinde}\\n"
                        
                    response += f"\\n💡 **Tipp:** Alle Aufgaben im Portal unter [portal.marcelgladbach.com/tasks](https://portal.marcelgladbach.com/tasks)"
                    
                    send_telegram_message(chat_id, response)
                else:
                    send_telegram_message(chat_id, "❌ **Fehler beim Erstellen der Aufgabe.**\\n\\nBitte versuchen Sie es erneut.")