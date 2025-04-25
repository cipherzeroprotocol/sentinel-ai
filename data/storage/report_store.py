"""
Report storage module for Sentinel AI

This module handles storage and retrieval of security analysis reports.
"""

import os
import sys
import json
import logging
from datetime import datetime
import sqlite3
import pathlib

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReportStore:
    """
    Report storage system for security analysis reports
    
    This class manages storage and retrieval of security reports, using
    both SQLite for metadata and file storage for full reports.
    """
    
    def __init__(self, db_path=None, reports_dir=None):
        """
        Initialize the ReportStore
        
        Args:
            db_path (str, optional): Path to SQLite database
            reports_dir (str, optional): Directory for storing report files
        """
        # Set up database path
        if db_path is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
            db_path = os.path.join(data_dir, "sentinel.db")
        
        # Set up reports directory
        if reports_dir is None:
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports", "data")
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
        
        self.db_path = db_path
        self.reports_dir = reports_dir
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create reports table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                address TEXT NOT NULL,
                risk_score INTEGER,
                created_at TIMESTAMP NOT NULL,
                summary TEXT
            )
            ''')
            
            # Create analysis table for specific analysis results
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                risk_score INTEGER,
                summary TEXT,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            )
            ''')
            
            # Create index on address for faster lookups
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_reports_address ON reports(address)
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def save_report(self, report_id, report_data):
        """
        Save a report to storage
        
        Args:
            report_id (str): Unique report ID
            report_data (dict): Report data to save
            
        Returns:
            bool: Success status
        """
        try:
            # Save full report to file
            self._save_report_file(report_id, report_data)
            
            # Save metadata to database
            self._save_report_metadata(report_id, report_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving report {report_id}: {str(e)}")
            return False
    
    def _save_report_file(self, report_id, report_data):
        """
        Save full report to file
        
        Args:
            report_id (str): Unique report ID
            report_data (dict): Report data to save
        """
        file_path = os.path.join(self.reports_dir, f"{report_id}.json")
        
        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2)
    
    def _save_report_metadata(self, report_id, report_data):
        """
        Save report metadata to database
        
        Args:
            report_id (str): Unique report ID
            report_data (dict): Report data to save
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Extract main report metadata
            address = report_data.get("address", "")
            risk_score = report_data.get("risk_score", 0)
            created_at = report_data.get("created_at", datetime.now().isoformat())
            
            # Extract summary
            executive_summary = report_data.get("executive_summary", "")
            if isinstance(executive_summary, str):
                # Strip HTML tags
                summary = executive_summary.replace("<p>", "").replace("</p>", " ")
                summary = summary.replace("<strong>", "").replace("</strong>", "")
                summary = summary.replace("<ul>", "").replace("</ul>", "")
                summary = summary.replace("<li>", "- ").replace("</li>", " ")
                # Truncate if needed
                summary = summary[:1000] if len(summary) > 1000 else summary
            else:
                summary = "Report generated successfully."
            
            # Insert main report record
            cursor.execute(
                "INSERT OR REPLACE INTO reports (id, address, risk_score, created_at, summary) VALUES (?, ?, ?, ?, ?)",
                (report_id, address, risk_score, created_at, summary)
            )
            
            # Save analysis results
            if "results" in report_data and isinstance(report_data["results"], dict):
                for analysis_type, result in report_data["results"].items():
                    if result:
                        analysis_id = f"{report_id}_{analysis_type}"
                        analysis_risk_score = result.get("risk_score", 0)
                        analysis_summary = result.get("summary", "")
                        
                        cursor.execute(
                            """INSERT OR REPLACE INTO analysis_results 
                               (id, report_id, analysis_type, risk_score, summary) 
                               VALUES (?, ?, ?, ?, ?)""",
                            (analysis_id, report_id, analysis_type, analysis_risk_score, analysis_summary)
                        )
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error saving report metadata: {str(e)}")
            raise
            
        finally:
            conn.close()
    
    def get_report(self, report_id):
        """
        Get a report by ID
        
        Args:
            report_id (str): Report ID to retrieve
            
        Returns:
            dict: Report data or None if not found
        """
        try:
            file_path = os.path.join(self.reports_dir, f"{report_id}.json")
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Report file not found: {report_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving report {report_id}: {str(e)}")
            return None
    
    def get_reports_for_address(self, address):
        """
        Get all reports for an address
        
        Args:
            address (str): Address to get reports for
            
        Returns:
            list: List of report metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, address, risk_score, created_at, summary FROM reports WHERE address = ? ORDER BY created_at DESC",
                (address,)
            )
            
            reports = []
            for row in cursor.fetchall():
                reports.append(dict(row))
            
            conn.close()
            return reports
            
        except Exception as e:
            logger.error(f"Error retrieving reports for address {address}: {str(e)}")
            return []
    
    def get_all_reports(self, limit=100, offset=0):
        """
        Get all reports with pagination
        
        Args:
            limit (int): Maximum number of reports to return
            offset (int): Offset for pagination
            
        Returns:
            list: List of report metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT id, address, risk_score, created_at, summary 
                   FROM reports ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (limit, offset)
            )
            
            reports = []
            for row in cursor.fetchall():
                reports.append(dict(row))
            
            conn.close()
            return reports
            
        except Exception as e:
            logger.error(f"Error retrieving all reports: {str(e)}")
            return []
    
    def search_reports(self, query, limit=50):
        """
        Search for reports
        
        Args:
            query (str): Search query (address or keywords)
            limit (int): Maximum number of results
            
        Returns:
            list: List of matching report metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Search in address field or summary
            search_param = f"%{query}%"
            cursor.execute(
                """SELECT id, address, risk_score, created_at, summary 
                   FROM reports 
                   WHERE address LIKE ? OR summary LIKE ? 
                   ORDER BY created_at DESC LIMIT ?""",
                (search_param, search_param, limit)
            )
            
            reports = []
            for row in cursor.fetchall():
                reports.append(dict(row))
            
            conn.close()
            return reports
            
        except Exception as e:
            logger.error(f"Error searching reports for '{query}': {str(e)}")
            return []
    
    def get_high_risk_reports(self, risk_threshold=75, limit=20):
        """
        Get high risk reports
        
        Args:
            risk_threshold (int): Minimum risk score to consider high risk
            limit (int): Maximum number of results
            
        Returns:
            list: List of high risk report metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT id, address, risk_score, created_at, summary 
                   FROM reports 
                   WHERE risk_score >= ? 
                   ORDER BY risk_score DESC, created_at DESC LIMIT ?""",
                (risk_threshold, limit)
            )
            
            reports = []
            for row in cursor.fetchall():
                reports.append(dict(row))
            
            conn.close()
            return reports
            
        except Exception as e:
            logger.error(f"Error retrieving high risk reports: {str(e)}")
            return []
    
    def delete_report(self, report_id):
        """
        Delete a report
        
        Args:
            report_id (str): ID of report to delete
            
        Returns:
            bool: Success status
        """
        try:
            # Delete file
            file_path = os.path.join(self.reports_dir, f"{report_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First delete analysis results
            cursor.execute("DELETE FROM analysis_results WHERE report_id = ?", (report_id,))
            
            # Then delete main report
            cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting report {report_id}: {str(e)}")
            return False
    
    def get_report_count(self):
        """
        Get total number of reports
        
        Returns:
            int: Report count
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM reports")
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            logger.error(f"Error getting report count: {str(e)}")
            return 0


if __name__ == "__main__":
    # Example usage
    store = ReportStore()
    
    # Example report
    report_data = {
        "id": "test-report-123",
        "address": "5KWGzE5gQW5Kj3pVCv5tELmKb7P7uSbQSdr4VnKWFYgS",
        "created_at": datetime.now().isoformat(),
        "risk_score": 85,
        "executive_summary": "<p>This is a test report summary</p>",
        "results": {
            "ico": {
                "risk_score": 80,
                "summary": "High risk token with suspicious patterns"
            },
            "money_laundering": {
                "risk_score": 90,
                "summary": "Strong indicators of money laundering activity"
            }
        }
    }
    
    # Save the report
    success = store.save_report(report_data["id"], report_data)
    print(f"Report saved: {success}")
    
    # Retrieve the report
    retrieved_report = store.get_report(report_data["id"])
    print(f"Retrieved report: {retrieved_report['id']}")
    
    # Get all reports for address
    address_reports = store.get_reports_for_address(report_data["address"])
    print(f"Reports for address: {len(address_reports)}")