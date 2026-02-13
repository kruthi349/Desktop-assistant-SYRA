# Simple Tasks & Calendar Module - List-Based Storage

import json
from datetime import datetime
from typing import List, Dict, Optional

class SimpleTaskManager:
    """Simple task/calendar manager using just a list"""
    
    def __init__(self):
        self.tasks: List[Dict] = []
        self.task_id_counter = 1
    
    # ==================== ADD TASK ====================
    def add_task(self, title: str, description: str = "", due_date: str = "", due_time: str = "") -> str:
        """Add a new task to the list"""
        try:
            task = {
                "id": self.task_id_counter,
                "title": title,
                "description": description,
                "due_date": due_date,  # Format: YYYY-MM-DD
                "due_time": due_time,  # Format: HH:MM
                "completed": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.tasks.append(task)
            self.task_id_counter += 1
            
            if due_date and due_time:
                return f"Task '{title}' added for {due_date} at {due_time}"
            elif due_date:
                return f"Task '{title}' added for {due_date}"
            else:
                return f"Task '{title}' added"
        except Exception as e:
            return f"Error adding task: {str(e)}"
    
    # ==================== VIEW ALL TASKS ====================
    def get_all_tasks(self) -> str:
        """Get all tasks"""
        if not self.tasks:
            return "No tasks found. You have a clear schedule!"
        
        response = f"You have {len(self.tasks)} tasks:\n"
        for task in self.tasks:
            status = "✓" if task["completed"] else "○"
            due_info = ""
            if task["due_date"]:
                due_info = f" - Due: {task['due_date']}"
                if task["due_time"]:
                    due_info += f" at {task['due_time']}"
            response += f"{status} [{task['id']}] {task['title']}{due_info}\n"
        return response
    
    # ==================== VIEW TODAY'S TASKS ====================
    def get_today_tasks(self) -> str:
        """Get tasks for today"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_tasks = [t for t in self.tasks if t["due_date"] == today and not t["completed"]]
        
        if not today_tasks:
            return f"No tasks for today ({today}). You're all set!"
        
        response = f"Your tasks for today ({today}):\n"
        for task in today_tasks:
            time_info = f" at {task['due_time']}" if task['due_time'] else ""
            response += f"• {task['title']}{time_info}\n"
        return response
    
    # ==================== VIEW UPCOMING TASKS ====================
    def get_upcoming_tasks(self) -> str:
        """Get upcoming tasks (next 7 days)"""
        today = datetime.now().strftime("%Y-%m-%d")
        upcoming = [t for t in self.tasks if t["due_date"] >= today and not t["completed"]]
        
        if not upcoming:
            return "No upcoming tasks scheduled."
        
        response = "Your upcoming tasks:\n"
        for task in upcoming:
            time_info = f" at {task['due_time']}" if task['due_time'] else ""
            response += f"• {task['title']} - {task['due_date']}{time_info}\n"
        return response
    
    # ==================== SEARCH TASKS ====================
    def search_tasks(self, keyword: str) -> str:
        """Search tasks by keyword"""
        results = [t for t in self.tasks if keyword.lower() in t["title"].lower()]
        
        if not results:
            return f"No tasks found with keyword '{keyword}'"
        
        response = f"Found {len(results)} tasks with '{keyword}':\n"
        for task in results:
            status = "✓" if task["completed"] else "○"
            response += f"{status} [{task['id']}] {task['title']}\n"
        return response
    
    # ==================== MARK TASK COMPLETE ====================
    def complete_task(self, task_id: int) -> str:
        """Mark task as complete"""
        for task in self.tasks:
            if task["id"] == task_id:
                task["completed"] = True
                return f"Task '{task['title']}' marked as complete ✓"
        return f"Task #{task_id} not found"
    
    # ==================== DELETE TASK ====================
    def delete_task(self, task_id: int) -> str:
        """Delete a task"""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                title = task["title"]
                self.tasks.pop(i)
                return f"Task '{title}' deleted"
        return f"Task #{task_id} not found"
    
    # ==================== GET CURRENT DATE/TIME ====================
    def get_current_date_time(self) -> str:
        """Get current date and time"""
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        return f"Date: {date}, Time: {time}"


# ==================== GLOBAL INSTANCE ====================
task_manager = SimpleTaskManager()


# ==================== HELPER FUNCTIONS ====================

def add_task(title: str, description: str = "", due_date: str = "", due_time: str = "") -> str:
    """Add task"""
    return task_manager.add_task(title, description, due_date, due_time)

def get_all_tasks() -> str:
    """Get all tasks"""
    return task_manager.get_all_tasks()

def get_today_tasks() -> str:
    """Get today's tasks"""
    return task_manager.get_today_tasks()

def get_upcoming_tasks() -> str:
    """Get upcoming tasks"""
    return task_manager.get_upcoming_tasks()

def search_tasks(keyword: str) -> str:
    """Search tasks"""
    return task_manager.search_tasks(keyword)

def complete_task(task_id: int) -> str:
    """Complete task"""
    return task_manager.complete_task(task_id)

def delete_task(task_id: int) -> str:
    """Delete task"""
    return task_manager.delete_task(task_id)

def get_current_date_time() -> str:
    """Get current date/time"""
    return task_manager.get_current_date_time()


# ==================== EXPORT FOR AGENT ====================
__all__ = [
    'task_manager',
    'add_task',
    'get_all_tasks',
    'get_today_tasks',
    'get_upcoming_tasks',
    'search_tasks',
    'complete_task',
    'delete_task',
    'get_current_date_time'
]