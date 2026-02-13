# Simple Tasks Manager - Dictionary Based (Organized by Date)

from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SimpleTaskManager:
    """Simple task manager organized by date in a dictionary"""
    
    def __init__(self):
        # Dictionary structure: {"2025-11-17": [task1, task2], "2025-11-18": [task3]}
        self.tasks: Dict[str, List[Dict]] = {}
        self.task_id_counter = 1
    
    # ==================== ADD TASK ====================
    def add_task(self, title: str, description: str = "", due_date: str = "", due_time: str = "") -> str:
        """Add a new task organized by date"""
        try:
            # If no date provided, use today
            if not due_date:
                due_date = datetime.now().strftime("%Y-%m-%d")
            
            # Create task object
            task = {
                "id": self.task_id_counter,
                "title": title,
                "description": description,
                "due_time": due_time,  # Format: HH:MM
                "completed": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add to dictionary by date
            if due_date not in self.tasks:
                self.tasks[due_date] = []
            self.tasks[due_date].append(task)
            self.task_id_counter += 1
            
            time_info = f" at {due_time}" if due_time else ""
            return f"Task '{title}' added for {due_date}{time_info}"
        except Exception as e:
            return f"Error adding task: {str(e)}"
    
    # ==================== GET CURRENT DATE ====================
    def get_current_date(self) -> str:
        """Get current date in YYYY-MM-DD format"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_current_date_time(self) -> str:
        """Get current date and time"""
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        return f"Date: {date}, Time: {time}"
    
    # ==================== GET TASKS BY DATE ====================
    def get_tasks_by_date(self, date: str) -> str:
        """Get all tasks for a specific date"""
        if date not in self.tasks or not self.tasks[date]:
            return f"No tasks found for {date}"
        
        response = f"Tasks for {date}:\n"
        for task in self.tasks[date]:
            status = "✓" if task["completed"] else "○"
            time_info = f" at {task['due_time']}" if task['due_time'] else ""
            response += f"{status} [{task['id']}] {task['title']}{time_info}\n"
        
        return response
    
    # ==================== GET TODAY'S TASKS ====================
    def get_today_tasks(self) -> str:
        """Get tasks for today"""
        today = self.get_current_date()
        return self.get_tasks_by_date(today)
    
    # ==================== GET TOMORROW'S TASKS ====================
    def get_tomorrow_tasks(self) -> str:
        """Get tasks for tomorrow"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        return self.get_tasks_by_date(tomorrow)
    
    # ==================== GET TASKS FOR SPECIFIC DATE ====================
    def get_tasks_for_date(self, date_str: str) -> str:
        """Get tasks for a specific date (converts 'tomorrow', 'today', etc.)"""
        today = self.get_current_date()
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        date_str_lower = date_str.lower()
        
        if "tomorrow" in date_str_lower:
            target_date = tomorrow
        elif "today" in date_str_lower:
            target_date = today
        else:
            target_date = date_str
        
        return self.get_tasks_by_date(target_date)
    
    # ==================== GET UPCOMING TASKS ====================
    def get_upcoming_tasks(self, days: int = 7) -> str:
        """Get upcoming tasks for next N days"""
        upcoming_dates = []
        for i in range(days):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            upcoming_dates.append(date)
        
        result = "Upcoming tasks:\n"
        found_any = False
        
        for date in upcoming_dates:
            if date in self.tasks and self.tasks[date]:
                result += f"\n{date}:\n"
                for task in self.tasks[date]:
                    if not task["completed"]:
                        status = "✓" if task["completed"] else "○"
                        time_info = f" at {task['due_time']}" if task['due_time'] else ""
                        result += f"  {status} [{task['id']}] {task['title']}{time_info}\n"
                        found_any = True
        
        if not found_any:
            return "No upcoming tasks scheduled"
        
        return result
    
    # ==================== GET ALL TASKS ====================
    def get_all_tasks(self) -> str:
        """Get all tasks organized by date"""
        if not self.tasks:
            return "No tasks found. You have a clear schedule!"
        
        result = "All tasks:\n"
        for date in sorted(self.tasks.keys()):
            if self.tasks[date]:
                result += f"\n{date}:\n"
                for task in self.tasks[date]:
                    status = "✓" if task["completed"] else "○"
                    time_info = f" at {task['due_time']}" if task['due_time'] else ""
                    result += f"  {status} [{task['id']}] {task['title']}{time_info}\n"
        
        return result
    
    # ==================== SEARCH TASKS ====================
    def search_tasks(self, keyword: str) -> str:
        """Search tasks by keyword across all dates"""
        results = []
        for date, task_list in self.tasks.items():
            for task in task_list:
                if keyword.lower() in task["title"].lower():
                    results.append((date, task))
        
        if not results:
            return f"No tasks found with keyword '{keyword}'"
        
        response = f"Found {len(results)} tasks with '{keyword}':\n"
        for date, task in results:
            status = "✓" if task["completed"] else "○"
            time_info = f" at {task['due_time']}" if task['due_time'] else ""
            response += f"{status} [{task['id']}] {task['title']} ({date}){time_info}\n"
        
        return response
    
    # ==================== COMPLETE TASK ====================
    def complete_task(self, task_id: int) -> str:
        """Mark task as complete"""
        for date, task_list in self.tasks.items():
            for task in task_list:
                if task["id"] == task_id:
                    task["completed"] = True
                    return f"Task '{task['title']}' marked as complete ✓"
        return f"Task #{task_id} not found"
    
    # ==================== DELETE TASK ====================
    def delete_task(self, task_id: int) -> str:
        """Delete a task"""
        for date, task_list in self.tasks.items():
            for i, task in enumerate(task_list):
                if task["id"] == task_id:
                    title = task["title"]
                    task_list.pop(i)
                    # Remove empty date entries
                    if not task_list:
                        del self.tasks[date]
                    return f"Task '{title}' deleted"
        return f"Task #{task_id} not found"


# ==================== GLOBAL INSTANCE ====================
task_manager = SimpleTaskManager()


# ==================== HELPER FUNCTIONS ====================

def add_task(title: str, description: str = "", due_date: str = "", due_time: str = "") -> str:
    """Add task"""
    return task_manager.add_task(title, description, due_date, due_time)

def get_current_date() -> str:
    """Get current date"""
    return task_manager.get_current_date()

def get_current_date_time() -> str:
    """Get current date and time"""
    return task_manager.get_current_date_time()

def get_today_tasks() -> str:
    """Get today's tasks"""
    return task_manager.get_today_tasks()

def get_tomorrow_tasks() -> str:
    """Get tomorrow's tasks"""
    return task_manager.get_tomorrow_tasks()

def get_tasks_for_date(date_str: str) -> str:
    """Get tasks for a specific date (handles 'today', 'tomorrow', or YYYY-MM-DD)"""
    return task_manager.get_tasks_for_date(date_str)

def get_tasks_by_date(date: str) -> str:
    """Get tasks for a specific date (YYYY-MM-DD format)"""
    return task_manager.get_tasks_by_date(date)

def get_upcoming_tasks(days: int = 7) -> str:
    """Get upcoming tasks"""
    return task_manager.get_upcoming_tasks(days)

def get_all_tasks() -> str:
    """Get all tasks"""
    return task_manager.get_all_tasks()

def search_tasks(keyword: str) -> str:
    """Search tasks"""
    return task_manager.search_tasks(keyword)

def complete_task(task_id: int) -> str:
    """Complete task"""
    return task_manager.complete_task(task_id)

def delete_task(task_id: int) -> str:
    """Delete task"""
    return task_manager.delete_task(task_id)


# ==================== EXPORT FOR AGENT ====================
__all__ = [
    'task_manager',
    'add_task',
    'get_current_date',
    'get_current_date_time',
    'get_today_tasks',
    'get_tomorrow_tasks',
    'get_tasks_for_date',
    'get_tasks_by_date',
    'get_upcoming_tasks',
    'get_all_tasks',
    'search_tasks',
    'complete_task',
    'delete_task'
]