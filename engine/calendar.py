import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import time
from langchain_core.tools import tool # Keep this import

# Try importing from engine.command and eel, with fallback for agent-only usage
try:
    from engine.command import speak
except ImportError:
    print("Warning: engine.command.speak not found. Reminders will only print to console.")
    def speak(message):
        pass # Dummy speak function

try:
    import eel
except ImportError:
    print("Warning: eel not found. UI notifications will not be displayed.")
    class DummyEel:
        def showNotification(self, message):
            pass
    eel = DummyEel()


# ==================== Database Setup ====================

class CalendarDB:
    """Handle calendar database operations"""
    
    def __init__(self, db_name="jarvis.db"):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """Initialize calendar tables"""
        con = sqlite3.connect(self.db_name)
        cursor = con.cursor()
        
        # Create events table
        cursor.execute('''CREATE TABLE IF NOT EXISTS calendar_events
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            time TIME NOT NULL,
            category VARCHAR(100),
            reminder_minutes INTEGER DEFAULT 15,
            is_completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Create reminders table
        cursor.execute('''CREATE TABLE IF NOT EXISTS event_reminders
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            reminder_time TIMESTAMP NOT NULL,
            is_sent BOOLEAN DEFAULT 0,
            FOREIGN KEY(event_id) REFERENCES calendar_events(id) ON DELETE CASCADE
        )''')
        
        con.commit()
        con.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_name)
    
    # ==================== CRUD Operations ====================
    
    def add_event(self, title: str, date: str, time: str, description: str = "", 
                  category: str = "General", reminder_minutes: int = 15) -> int:
        """
        Add new event to calendar
        Args:
            title: Event title
            date: YYYY-MM-DD format
            time: HH:MM format
            description: Event description
            category: Event category
            reminder_minutes: Minutes before event to remind
        Returns:
            Event ID
        """
        try:
            con = self.get_connection()
            cursor = con.cursor()
            
            cursor.execute('''
                INSERT INTO calendar_events 
                (title, description, date, time, category, reminder_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, description, date, time, category, reminder_minutes))
            
            event_id = cursor.lastrowid
            con.commit()
            
            # Calculate and create reminder
            self._create_reminder(con, event_id, date, time, reminder_minutes)
            
            con.close()
            return event_id
        except Exception as e:
            print(f"Error adding event: {e}")
            return None
    
    def _create_reminder(self, con, event_id: int, date: str, time: str, reminder_minutes: int):
        """Create reminder for event"""
        try:
            cursor = con.cursor()
            event_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            reminder_time = event_datetime - timedelta(minutes=reminder_minutes)
            
            cursor.execute('''
                INSERT INTO event_reminders (event_id, reminder_time)
                VALUES (?, ?)
            ''', (event_id, reminder_time.isoformat()))
            
            con.commit()
        except Exception as e:
            print(f"Error creating reminder: {e}")
    
    def get_all_events(self, date: Optional[str] = None) -> List[Dict]:
        """
        Get all events or events for specific date
        Args:
            date: YYYY-MM-DD format (optional)
        Returns:
            List of events
        """
        try:
            con = self.get_connection()
            cursor = con.cursor()
            
            if date:
                cursor.execute('''
                    SELECT id, title, description, date, time, category, is_completed
                    FROM calendar_events
                    WHERE date = ? AND is_completed = 0
                    ORDER BY time ASC
                ''', (date,))
            else:
                cursor.execute('''
                    SELECT id, title, description, date, time, category, is_completed
                    FROM calendar_events
                    WHERE is_completed = 0
                    ORDER BY date ASC, time ASC
                    LIMIT 50
                ''')
            
            columns = [description[0] for description in cursor.description]
            events = [dict(zip(columns, row)) for row in cursor.fetchall()]
            con.close()
            
            return events
        except Exception as e:
            print(f"Error getting events: {e}")
            return []
    
    def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """Get upcoming events for next N days"""
        try:
            con = self.get_connection()
            cursor = con.cursor()
            
            today = datetime.now().strftime("%Y-%m-%d")
            future_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            
            cursor.execute('''
                SELECT id, title, description, date, time, category, is_completed
                FROM calendar_events
                WHERE date BETWEEN ? AND ? AND is_completed = 0
                ORDER BY date ASC, time ASC
            ''', (today, future_date))
            
            columns = [description[0] for description in cursor.description]
            events = [dict(zip(columns, row)) for row in cursor.fetchall()]
            con.close()
            
            return events
        except Exception as e:
            print(f"Error getting upcoming events: {e}")
            return []
    
    def update_event(self, event_id: int, **kwargs) -> bool:
        """Update event details"""
        try:
            con = self.get_connection()
            cursor = con.cursor()
            
            allowed_fields = ['title', 'description', 'date', 'time', 'category', 'reminder_minutes']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not updates:
                return False
            
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            update_sql = f"UPDATE calendar_events SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            
            cursor.execute(update_sql, list(updates.values()) + [event_id])
            con.commit()
            con.close()
            
            return True
        except Exception as e:
            print(f"Error updating event: {e}")
            return False
    
    def delete_event(self, event_id: int) -> bool:
        """Delete event"""
        try:
            con = self.get_connection()
            cursor = con.cursor()
            
            cursor.execute('DELETE FROM calendar_events WHERE id = ?', (event_id,))
            con.commit()
            con.close()
            
            return True
        except Exception as e:
            print(f"Error deleting event: {e}")
            return False
    
    def mark_event_completed(self, event_id: int) -> bool:
        """Mark event as completed"""
        try:
            con = self.get_connection()
            cursor = con.cursor()
            
            cursor.execute('''
                UPDATE calendar_events 
                SET is_completed = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (event_id,))
            
            con.commit()
            con.close()
            return True
        except Exception as e:
            print(f"Error marking event completed: {e}")
            return False
    
    def search_events(self, keyword: str) -> List[Dict]:
        """Search events by title or description"""
        try:
            con = self.get_connection()
            cursor = con.cursor()
            
            search_pattern = f"%{keyword}%"
            cursor.execute('''
                SELECT id, title, description, date, time, category, is_completed
                FROM calendar_events
                WHERE (title LIKE ? OR description LIKE ?) AND is_completed = 0
                ORDER BY date ASC, time ASC
            ''', (search_pattern, search_pattern))
            
            columns = [description[0] for description in cursor.description]
            events = [dict(zip(columns, row)) for row in cursor.fetchall()]
            con.close()
            
            return events
        except Exception as e:
            print(f"Error searching events: {e}")
            return []


# ==================== Calendar Manager ====================

class CalendarManager:
    """Manage calendar operations and reminders"""
    
    def __init__(self):
        self.db = CalendarDB()
        self.reminder_thread = None
        self.running = False
    
    def add_event_voice(self, title: str, date: str, time: str, category: str = "General") -> str:
        """Add event via voice command"""
        try:
            event_id = self.db.add_event(title, date, time, category=category)
            if event_id:
                message = f"Event '{title}' added for {date} at {time}. You will be reminded 15 minutes before."
                print(message)
                return message
            else:
                return "Failed to add event"
        except Exception as e:
            print(f"Error: {e}")
            return f"Error adding event: {str(e)}"
    
    def view_today_events(self) -> str:
        """Get today's events"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            events = self.db.get_all_events(today)
            
            if not events:
                return "No events scheduled for today"
            
            message = f"You have {len(events)} events today:\n"
            for event in events:
                message += f"\n• {event['title']} at {event['time']}"
                if event['description']:
                    message += f" - {event['description']}"
            
            return message
        except Exception as e:
            return f"Error getting today's events: {str(e)}"
    
    def view_upcoming_events(self, days: int = 7) -> str:
        """Get upcoming events"""
        try:
            events = self.db.get_upcoming_events(days)
            
            if not events:
                return f"No events scheduled for the next {days} days"
            
            message = f"You have {len(events)} upcoming events in the next {days} days:\n"
            for event in events:
                message += f"\n• {event['date']} - {event['title']} at {event['time']}"
                if event['description']:
                    message += f" - {event['description']}"
            
            return message
        except Exception as e:
            return f"Error getting upcoming events: {str(e)}"
    
    def get_event_details(self, event_id: int) -> str:
        """Get specific event details"""
        try:
            events = self.db.get_all_events() # This gets ALL events, might be inefficient if DB is large
            event = next((e for e in events if e['id'] == event_id), None)
            
            if not event:
                return "Event not found"
            
            details = f"Event: {event['title']}\n"
            details += f"Date: {event['date']}\n"
            details += f"Time: {event['time']}\n"
            if event['description']:
                details += f"Description: {event['description']}\n"
            details += f"Category: {event['category']}\n"
            details += f"Status: {'Completed' if event['is_completed'] else 'Pending'}"
            
            return details
        except Exception as e:
            return f"Error getting event details: {str(e)}"
    
    def start_reminder_service(self):
        """Start background reminder service"""
        if not self.running:
            self.running = True
            self.reminder_thread = threading.Thread(target=self._reminder_loop, daemon=True)
            self.reminder_thread.start()
            print("Reminder service started")
    
    def stop_reminder_service(self):
        """Stop reminder service"""
        self.running = False
        print("Reminder service stopped")
    
    def _reminder_loop(self):
        """Background loop for checking reminders"""
        while self.running:
            try:
                self._check_and_send_reminders()
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in reminder loop: {e}")
    
    def _check_and_send_reminders(self):
        """Check and send due reminders"""
        try:
            con = self.db.get_connection()
            cursor = con.cursor()
            
            now = datetime.now().isoformat()
            
            # Get pending reminders
            cursor.execute('''
                SELECT r.id, r.event_id, e.title, e.date, e.time
                FROM event_reminders r
                JOIN calendar_events e ON r.event_id = e.id
                WHERE r.is_sent = 0 AND r.reminder_time <= ?
                ORDER BY r.reminder_time ASC
            ''', (now,))
            
            reminders = cursor.fetchall()
            
            for reminder in reminders:
                reminder_id, event_id, title, date, event_time = reminder
                
                # Send reminder
                message = f"Reminder: {title} is scheduled for {date} at {event_time}"
                print(f"[REMINDER] {message}")
                
                try:
                    speak(message)
                    eel.showNotification(message)
                except Exception as ex:
                    print(f"Could not speak or show UI reminder for event {title}: {ex}. But it's logged.")
                
                # Mark as sent
                cursor.execute('''
                    UPDATE event_reminders
                    SET is_sent = 1
                    WHERE id = ?
                ''', (reminder_id,))
                con.commit()
            
            con.close()
        except Exception as e:
            print(f"Error checking reminders: {e}")


# ==================== Calendar Tools for Agent ====================

calendar_manager = CalendarManager()

@tool
def add_calendar_event(title: str, date: str, time: str, description: str = "", category: str = "General") -> str:
    """
    Add event to calendar
    Args:
        title: Event title
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour)
        description: Event description (optional)
        category: Event category like Meeting, Birthday, Reminder, Personal (optional)
    """
    return calendar_manager.add_event_voice(title, date, time, category)

@tool
def view_calendar_today() -> str:
    """View all events scheduled for today"""
    return calendar_manager.view_today_events()

@tool
def view_calendar_upcoming(days: int = 7) -> str:
    """
    View upcoming events
    Args:
        days: Number of days to look ahead (default 7)
    """
    return calendar_manager.view_upcoming_events(days)

@tool
def search_calendar_events(keyword: str) -> str:
    """
    Search events in calendar
    Args:
        keyword: Search term for event title or description
    """
    try:
        events = calendar_manager.db.search_events(keyword)
        if not events:
            return f"No events found matching '{keyword}'"
        
        result = f"Found {len(events)} events matching '{keyword}':\n"
        for event in events:
            result += f"• {event['date']} {event['time']} - {event['title']}\n"
        return result
    except Exception as e:
        return f"Error searching events: {str(e)}"

@tool
def complete_calendar_event(event_id: int) -> str:
    """Mark an event as completed"""
    try:
        if calendar_manager.db.mark_event_completed(event_id):
            return f"Event {event_id} marked as completed"
        else:
            return f"Could not mark event {event_id} as completed"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def delete_calendar_event(event_id: int) -> str:
    """Delete an event from calendar"""
    try:
        if calendar_manager.db.delete_event(event_id):
            return f"Event {event_id} deleted successfully"
        else:
            return f"Could not delete event {event_id}"
    except Exception as e:
        return f"Error: {str(e)}"

# Initialize and start reminder service when module is imported
calendar_manager.start_reminder_service()

