import sqlite3
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import os
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class TaskAnalysis:
    """Data class for task analysis records"""
    id: Optional[int] = None
    task_text: str = ""
    suggested_date: str = ""
    confidence: float = 0.0
    urgency_score: int = 0
    keywords: str = ""  # JSON string
    reasoning: str = ""
    user_approved: bool = False
    final_due_date: Optional[str] = None
    trello_card_id: Optional[str] = None
    trello_checklist_id: Optional[str] = None
    trello_item_id: Optional[str] = None
    board_name: Optional[str] = None
    card_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    exported_to_calendar: bool = False

class DatabaseManager:
    """SQLite database manager for AI Checklist Due Dates"""
    
    def __init__(self, db_path: str = "ai_checklist.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with self.get_connection() as conn:
                # Main analysis table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS task_analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_text TEXT NOT NULL,
                        suggested_date TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        urgency_score INTEGER NOT NULL,
                        keywords TEXT,
                        reasoning TEXT,
                        user_approved BOOLEAN DEFAULT FALSE,
                        final_due_date TEXT,
                        trello_card_id TEXT,
                        trello_checklist_id TEXT,
                        trello_item_id TEXT,
                        board_name TEXT,
                        card_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        exported_to_calendar BOOLEAN DEFAULT FALSE
                    )
                """)
                
                # User preferences table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Export history table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS export_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER,
                        export_type TEXT NOT NULL,
                        export_data TEXT,
                        exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT,
                        FOREIGN KEY (task_id) REFERENCES task_analyses (id)
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_task_analyses_trello_ids 
                    ON task_analyses(trello_card_id, trello_item_id)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_task_analyses_dates 
                    ON task_analyses(suggested_date, created_at)
                """)
                
                logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_analysis(self, analysis_data: Dict[str, Any], trello_data: Optional[Dict] = None) -> int:
        """Save AI analysis to database"""
        try:
            with self.get_connection() as conn:
                # Prepare data
                keywords_json = json.dumps(analysis_data.get('keywords_found', []))
                
                query = """
                    INSERT INTO task_analyses (
                        task_text, suggested_date, confidence, urgency_score,
                        keywords, reasoning, trello_card_id, trello_checklist_id,
                        trello_item_id, board_name, card_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = (
                    analysis_data.get('task_text', ''),
                    analysis_data.get('suggested_date', ''),
                    analysis_data.get('confidence', 0.0),
                    analysis_data.get('urgency_score', 0),
                    keywords_json,
                    analysis_data.get('reasoning', ''),
                    trello_data.get('card_id') if trello_data else None,
                    trello_data.get('checklist_id') if trello_data else None,
                    trello_data.get('item_id') if trello_data else None,
                    trello_data.get('board_name') if trello_data else None,
                    trello_data.get('card_name') if trello_data else None
                )
                
                cursor = conn.execute(query, params)
                task_id = cursor.lastrowid
                
                logger.info(f"Saved analysis for task ID: {task_id}")
                return task_id
                
        except sqlite3.Error as e:
            logger.error(f"Error saving analysis: {e}")
            raise
    
    def update_user_approval(self, task_id: int, approved: bool, final_due_date: Optional[str] = None) -> bool:
        """Update user approval status and final due date"""
        try:
            with self.get_connection() as conn:
                query = """
                    UPDATE task_analyses 
                    SET user_approved = ?, final_due_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                
                conn.execute(query, (approved, final_due_date, task_id))
                
                if conn.total_changes > 0:
                    logger.info(f"Updated approval for task ID: {task_id}")
                    return True
                else:
                    logger.warning(f"No task found with ID: {task_id}")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"Error updating approval: {e}")
            return False
    
    def get_analyses(self, limit: int = 100, approved_only: bool = False) -> List[TaskAnalysis]:
        """Get task analyses from database"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT * FROM task_analyses 
                    {} 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """.format("WHERE user_approved = 1" if approved_only else "")
                
                cursor = conn.execute(query, (limit,))
                rows = cursor.fetchall()
                
                analyses = []
                for row in rows:
                    # Parse keywords JSON
                    keywords = json.loads(row['keywords']) if row['keywords'] else []
                    
                    analysis = TaskAnalysis(
                        id=row['id'],
                        task_text=row['task_text'],
                        suggested_date=row['suggested_date'],
                        confidence=row['confidence'],
                        urgency_score=row['urgency_score'],
                        keywords=keywords,
                        reasoning=row['reasoning'],
                        user_approved=bool(row['user_approved']),
                        final_due_date=row['final_due_date'],
                        trello_card_id=row['trello_card_id'],
                        trello_checklist_id=row['trello_checklist_id'],
                        trello_item_id=row['trello_item_id'],
                        board_name=row['board_name'],
                        card_name=row['card_name'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        exported_to_calendar=bool(row['exported_to_calendar'])
                    )
                    analyses.append(analysis)
                
                return analyses
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving analyses: {e}")
            return []
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary for dashboard"""
        try:
            with self.get_connection() as conn:
                # Total analyses
                total = conn.execute("SELECT COUNT(*) as count FROM task_analyses").fetchone()['count']
                
                # Approved analyses
                approved = conn.execute(
                    "SELECT COUNT(*) as count FROM task_analyses WHERE user_approved = 1"
                ).fetchone()['count']
                
                # Average confidence
                avg_confidence = conn.execute(
                    "SELECT AVG(confidence) as avg FROM task_analyses"
                ).fetchone()['avg'] or 0
                
                # Urgency distribution
                urgency_dist = conn.execute("""
                    SELECT urgency_score, COUNT(*) as count 
                    FROM task_analyses 
                    GROUP BY urgency_score 
                    ORDER BY urgency_score
                """).fetchall()
                
                # Recent activity (last 7 days)
                recent = conn.execute("""
                    SELECT COUNT(*) as count 
                    FROM task_analyses 
                    WHERE created_at >= datetime('now', '-7 days')
                """).fetchone()['count']
                
                # Export statistics
                exported = conn.execute(
                    "SELECT COUNT(*) as count FROM task_analyses WHERE exported_to_calendar = 1"
                ).fetchone()['count']
                
                return {
                    'total_analyses': total,
                    'approved_analyses': approved,
                    'approval_rate': (approved / total * 100) if total > 0 else 0,
                    'average_confidence': round(avg_confidence, 2),
                    'urgency_distribution': {row['urgency_score']: row['count'] for row in urgency_dist},
                    'recent_activity': recent,
                    'exported_count': exported
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting analytics: {e}")
            return {}
    
    def save_export_record(self, task_id: int, export_type: str, success: bool = True, 
                          export_data: Optional[Dict] = None, error_message: Optional[str] = None):
        """Save export history record"""
        try:
            with self.get_connection() as conn:
                query = """
                    INSERT INTO export_history (task_id, export_type, export_data, success, error_message)
                    VALUES (?, ?, ?, ?, ?)
                """
                
                export_data_json = json.dumps(export_data) if export_data else None
                
                conn.execute(query, (task_id, export_type, export_data_json, success, error_message))
                
                # Update main task record if successful
                if success and export_type == 'calendar':
                    conn.execute(
                        "UPDATE task_analyses SET exported_to_calendar = 1 WHERE id = ?",
                        (task_id,)
                    )
                
                logger.info(f"Export record saved for task {task_id}")
                
        except sqlite3.Error as e:
            logger.error(f"Error saving export record: {e}")
    
    def search_analyses(self, query: str, limit: int = 50) -> List[TaskAnalysis]:
        """Search analyses by task text"""
        try:
            with self.get_connection() as conn:
                search_query = """
                    SELECT * FROM task_analyses 
                    WHERE task_text LIKE ? OR reasoning LIKE ? OR card_name LIKE ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """
                
                search_term = f"%{query}%"
                cursor = conn.execute(search_query, (search_term, search_term, search_term, limit))
                rows = cursor.fetchall()
                
                analyses = []
                for row in rows:
                    keywords = json.loads(row['keywords']) if row['keywords'] else []
                    
                    analysis = TaskAnalysis(
                        id=row['id'],
                        task_text=row['task_text'],
                        suggested_date=row['suggested_date'],
                        confidence=row['confidence'],
                        urgency_score=row['urgency_score'],
                        keywords=keywords,
                        reasoning=row['reasoning'],
                        user_approved=bool(row['user_approved']),
                        final_due_date=row['final_due_date'],
                        trello_card_id=row['trello_card_id'],
                        trello_checklist_id=row['trello_checklist_id'],
                        trello_item_id=row['trello_item_id'],
                        board_name=row['board_name'],
                        card_name=row['card_name'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        exported_to_calendar=bool(row['exported_to_calendar'])
                    )
                    analyses.append(analysis)
                
                return analyses
                
        except sqlite3.Error as e:
            logger.error(f"Error searching analyses: {e}")
            return []
    
    def delete_analysis(self, task_id: int) -> bool:
        """Delete analysis and related records"""
        try:
            with self.get_connection() as conn:
                # Delete related export records first
                conn.execute("DELETE FROM export_history WHERE task_id = ?", (task_id,))
                
                # Delete main analysis record
                cursor = conn.execute("DELETE FROM task_analyses WHERE id = ?", (task_id,))
                
                if cursor.rowcount > 0:
                    logger.info(f"Deleted analysis {task_id}")
                    return True
                else:
                    logger.warning(f"No analysis found with ID {task_id}")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"Error deleting analysis: {e}")
            return False
    
    def get_preferences(self) -> Dict[str, str]:
        """Get all user preferences"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT key, value FROM user_preferences")
                rows = cursor.fetchall()
                
                return {row['key']: row['value'] for row in rows}
                
        except sqlite3.Error as e:
            logger.error(f"Error getting preferences: {e}")
            return {}
    
    def set_preference(self, key: str, value: str):
        """Set user preference"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (key, value))
                
                logger.info(f"Set preference {key}")
                
        except sqlite3.Error as e:
            logger.error(f"Error setting preference: {e}")
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def get_database_size(self) -> Dict[str, Any]:
        """Get database size and table statistics"""
        try:
            file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            with self.get_connection() as conn:
                tables = {
                    'task_analyses': conn.execute("SELECT COUNT(*) as count FROM task_analyses").fetchone()['count'],
                    'user_preferences': conn.execute("SELECT COUNT(*) as count FROM user_preferences").fetchone()['count'],
                    'export_history': conn.execute("SELECT COUNT(*) as count FROM export_history").fetchone()['count']
                }
                
                return {
                    'file_size_bytes': file_size,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'table_counts': tables
                }
                
        except Exception as e:
            logger.error(f"Error getting database size: {e}")
            return {}

# Utility functions
def create_sample_data(db_manager: DatabaseManager):
    """Create sample data for testing"""
    sample_analyses = [
        {
            'task_text': 'Fix critical login bug ASAP',
            'suggested_date': '2025-09-22',
            'confidence': 0.9,
            'urgency_score': 10,
            'keywords_found': ['critical', 'bug', 'asap'],
            'reasoning': 'High urgency detected from critical keywords'
        },
        {
            'task_text': 'Review quarterly report next week',
            'suggested_date': '2025-09-28',
            'confidence': 0.7,
            'urgency_score': 6,
            'keywords_found': ['quarterly', 'next week'],
            'reasoning': 'Medium priority timeline detected'
        },
        {
            'task_text': 'Plan team meeting',
            'suggested_date': '2025-09-28',
            'confidence': 0.3,
            'urgency_score': 3,
            'keywords_found': [],
            'reasoning': 'No specific timeline indicators found'
        }
    ]
    
    for analysis in sample_analyses:
        db_manager.save_analysis(analysis)

def test_database():
    """Test database functionality"""
    print("🗄️  DATABASE MANAGER TEST")
    print("=" * 40)
    
    # Initialize database
    db = DatabaseManager("test_ai_checklist.db")
    
    # Create sample data
    create_sample_data(db)
    print("✅ Sample data created")
    
    # Test retrieval
    analyses = db.get_analyses(limit=10)
    print(f"✅ Retrieved {len(analyses)} analyses")
    
    if analyses:
        # Test approval
        first_task = analyses[0]
        success = db.update_user_approval(first_task.id, True, '2025-09-25')
        print(f"✅ Approval update: {success}")
    
    # Test analytics
    stats = db.get_analytics_summary()
    print(f"✅ Analytics: {stats}")
    
    # Test search
    search_results = db.search_analyses("critical")
    print(f"✅ Search results: {len(search_results)} found")
    
    # Test preferences
    db.set_preference("default_timeline", "7")
    prefs = db.get_preferences()
    print(f"✅ Preferences: {prefs}")
    
    # Database info
    db_info = db.get_database_size()
    print(f"✅ Database size: {db_info}")
    
    print("\n🎉 Database test completed successfully!")

if __name__ == "__main__":
    test_database()