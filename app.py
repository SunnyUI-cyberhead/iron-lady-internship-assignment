from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import uuid
import os
from datetime import datetime, timedelta
import sqlite3
import csv
from io import StringIO, BytesIO
import pandas as pd
from werkzeug.utils import secure_filename
import openai
from typing import List, Dict, Optional
import logging

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'iron-lady-advanced-course-manager'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedCourseDatabase:
    def __init__(self, db_name='iron_lady_courses.db'):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with comprehensive schema"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                duration TEXT,
                instructor TEXT,
                category TEXT,
                price REAL DEFAULT 0,
                capacity INTEGER DEFAULT 30,
                enrolled INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft',
                rating REAL DEFAULT 0,
                total_ratings INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                prerequisites TEXT,
                learning_outcomes TEXT,
                course_image TEXT,
                difficulty_level TEXT DEFAULT 'intermediate'
            )
        ''')
        
        # Students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                created_at TEXT,
                total_courses INTEGER DEFAULT 0,
                completed_courses INTEGER DEFAULT 0
            )
        ''')
        
        # Enrollments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id TEXT PRIMARY KEY,
                student_id TEXT,
                course_id TEXT,
                enrollment_date TEXT,
                completion_date TEXT,
                progress REAL DEFAULT 0,
                grade TEXT,
                certificate_issued BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (student_id) REFERENCES students (id),
                FOREIGN KEY (course_id) REFERENCES courses (id)
            )
        ''')
        
        # Course ratings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_ratings (
                id TEXT PRIMARY KEY,
                course_id TEXT,
                student_id TEXT,
                rating INTEGER,
                review TEXT,
                created_at TEXT,
                FOREIGN KEY (course_id) REFERENCES courses (id),
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')
        
        # Analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id TEXT PRIMARY KEY,
                event_type TEXT,
                course_id TEXT,
                student_id TEXT,
                data TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insert sample data if database is empty
        self.populate_sample_data()
    
    def populate_sample_data(self):
        """Populate database with sample courses if empty"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM courses')
        if cursor.fetchone()[0] == 0:
            sample_courses = [
                {
                    'id': str(uuid.uuid4()),
                    'title': 'Executive Leadership Mastery',
                    'description': 'Comprehensive program for senior leaders focusing on strategic thinking, team management, and organizational transformation.',
                    'duration': '6 months',
                    'instructor': 'Dr. Sarah Johnson',
                    'category': 'Leadership',
                    'price': 2999.0,
                    'capacity': 25,
                    'enrolled': 18,
                    'status': 'active',
                    'rating': 4.8,
                    'total_ratings': 12,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'prerequisites': 'Management experience required',
                    'learning_outcomes': 'Strategic thinking, Team leadership, Change management',
                    'difficulty_level': 'advanced'
                },
                {
                    'id': str(uuid.uuid4()),
                    'title': 'Women in Leadership Certification',
                    'description': 'Empowering women professionals with leadership skills, confidence building, and career advancement strategies.',
                    'duration': '3 months',
                    'instructor': 'Michelle Rodriguez',
                    'category': 'Leadership',
                    'price': 1999.0,
                    'capacity': 30,
                    'enrolled': 22,
                    'status': 'active',
                    'rating': 4.9,
                    'total_ratings': 18,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'prerequisites': 'None',
                    'learning_outcomes': 'Leadership confidence, Career planning, Network building',
                    'difficulty_level': 'intermediate'
                },
                {
                    'id': str(uuid.uuid4()),
                    'title': 'Digital Transformation Strategy',
                    'description': 'Learn to lead digital initiatives and transform organizations in the digital age.',
                    'duration': '4 weeks',
                    'instructor': 'Alex Chen',
                    'category': 'Technical',
                    'price': 1499.0,
                    'capacity': 20,
                    'enrolled': 15,
                    'status': 'active',
                    'rating': 4.7,
                    'total_ratings': 8,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'prerequisites': 'Basic technology understanding',
                    'learning_outcomes': 'Digital strategy, Technology leadership, Innovation management',
                    'difficulty_level': 'intermediate'
                }
            ]
            
            for course in sample_courses:
                cursor.execute('''
                    INSERT INTO courses (id, title, description, duration, instructor, category, 
                                       price, capacity, enrolled, status, rating, total_ratings,
                                       created_at, updated_at, prerequisites, learning_outcomes, difficulty_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    course['id'], course['title'], course['description'], course['duration'],
                    course['instructor'], course['category'], course['price'], course['capacity'],
                    course['enrolled'], course['status'], course['rating'], course['total_ratings'],
                    course['created_at'], course['updated_at'], course['prerequisites'],
                    course['learning_outcomes'], course['difficulty_level']
                ))
        
        conn.commit()
        conn.close()

# Initialize database
db = AdvancedCourseDatabase()

class AIAssistant:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
    
    def generate_course_description(self, title: str, category: str) -> Dict:
        """Generate AI-powered course description and metadata"""
        if not self.api_key:
            return self._fallback_suggestions(title, category)
        
        try:
            prompt = f"""
            Generate a comprehensive course description and metadata for:
            Title: {title}
            Category: {category}
            
            Provide a JSON response with:
            - description: detailed course description (100-150 words)
            - duration: suggested duration 
            - learning_outcomes: list of 4-5 key learning outcomes
            - prerequisites: course prerequisites
            - difficulty_level: beginner/intermediate/advanced
            - suggested_price: price range
            """
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            import re
            response_text = response.choices[0].message.content
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            logger.warning(f"AI generation failed: {e}")
            return self._fallback_suggestions(title, category)
    
    def _fallback_suggestions(self, title: str, category: str) -> Dict:
        """Fallback suggestions when AI is unavailable"""
        suggestions = {
            'Leadership': {
                'description': 'Develop essential leadership skills through practical exercises, case studies, and expert guidance. This comprehensive program covers strategic thinking, team management, and organizational transformation.',
                'duration': '3-6 months',
                'learning_outcomes': ['Strategic Leadership', 'Team Management', 'Decision Making', 'Communication Skills'],
                'prerequisites': 'Basic management experience preferred',
                'difficulty_level': 'intermediate',
                'suggested_price': '1500-3000'
            },
            'Technical': {
                'description': 'Master cutting-edge technical skills with hands-on training and real-world projects. Stay ahead of industry trends and build practical expertise.',
                'duration': '4-12 weeks',
                'learning_outcomes': ['Technical Expertise', 'Problem Solving', 'Innovation', 'Implementation'],
                'prerequisites': 'Basic technical background',
                'difficulty_level': 'intermediate',
                'suggested_price': '1000-2500'
            }
        }
        
        return suggestions.get(category, suggestions['Leadership'])

ai_assistant = AIAssistant()

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/courses', methods=['GET'])
def get_courses():
    """Get all courses with filtering and sorting"""
    try:
        conn = sqlite3.connect(db.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get query parameters
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        status = request.args.get('status', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'DESC')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = 'SELECT * FROM courses WHERE 1=1'
        params = []
        
        if search:
            query += ' AND (title LIKE ? OR description LIKE ? OR instructor LIKE ?)'
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += f' ORDER BY {sort_by} {sort_order} LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        courses = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        count_query = query.split('ORDER BY')[0].replace('SELECT *', 'SELECT COUNT(*)')
        cursor.execute(count_query, params[:-2])  # Exclude limit/offset from count
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'courses': courses,
            'total_count': total_count,
            'page_info': {
                'limit': limit,
                'offset': offset,
                'has_more': offset + len(courses) < total_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting courses: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses', methods=['POST'])
def create_course():
    """Create a new course"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'description', 'duration', 'instructor']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        course_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO courses (id, title, description, duration, instructor, category,
                               price, capacity, status, created_at, updated_at, prerequisites,
                               learning_outcomes, difficulty_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            course_id, data['title'], data['description'], data['duration'],
            data['instructor'], data.get('category', 'General'),
            data.get('price', 0), data.get('capacity', 30),
            data.get('status', 'draft'), now, now,
            data.get('prerequisites', ''), data.get('learning_outcomes', ''),
            data.get('difficulty_level', 'intermediate')
        ))
        
        conn.commit()
        conn.close()
        
        # Log analytics
        log_analytics('course_created', course_id, data)
        
        return jsonify({'message': 'Course created successfully', 'course_id': course_id}), 201
        
    except Exception as e:
        logger.error(f"Error creating course: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<course_id>', methods=['PUT'])
def update_course(course_id):
    """Update a course"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        # Build update query dynamically
        set_clauses = []
        params = []
        
        updatable_fields = ['title', 'description', 'duration', 'instructor', 'category',
                          'price', 'capacity', 'status', 'prerequisites', 'learning_outcomes',
                          'difficulty_level']
        
        for field in updatable_fields:
            if field in data:
                set_clauses.append(f'{field} = ?')
                params.append(data[field])
        
        if not set_clauses:
            return jsonify({'error': 'No fields to update'}), 400
        
        set_clauses.append('updated_at = ?')
        params.append(datetime.now().isoformat())
        params.append(course_id)
        
        query = f'UPDATE courses SET {", ".join(set_clauses)} WHERE id = ?'
        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Course not found'}), 404
        
        conn.commit()
        conn.close()
        
        # Log analytics
        log_analytics('course_updated', course_id, data)
        
        return jsonify({'message': 'Course updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating course: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<course_id>', methods=['DELETE'])
def delete_course(course_id):
    """Delete a course"""
    try:
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Course not found'}), 404
        
        # Also delete related enrollments and ratings
        cursor.execute('DELETE FROM enrollments WHERE course_id = ?', (course_id,))
        cursor.execute('DELETE FROM course_ratings WHERE course_id = ?', (course_id,))
        
        conn.commit()
        conn.close()
        
        # Log analytics
        log_analytics('course_deleted', course_id, {})
        
        return jsonify({'message': 'Course deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting course: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<course_id>/enroll', methods=['POST'])
def enroll_student(course_id):
    """Enroll a student in a course"""
    try:
        data = request.get_json()
        student_name = data.get('student_name', 'Anonymous Student')
        student_email = data.get('student_email', f'student_{uuid.uuid4().hex[:8]}@example.com')
        
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        # Check course capacity
        cursor.execute('SELECT enrolled, capacity FROM courses WHERE id = ?', (course_id,))
        course_info = cursor.fetchone()
        
        if not course_info:
            conn.close()
            return jsonify({'error': 'Course not found'}), 404
        
        enrolled, capacity = course_info
        if enrolled >= capacity:
            conn.close()
            return jsonify({'error': 'Course is at full capacity'}), 400
        
        # Create or get student
        student_id = str(uuid.uuid4())
        cursor.execute('INSERT OR IGNORE INTO students (id, name, email, created_at) VALUES (?, ?, ?, ?)',
                      (student_id, student_name, student_email, datetime.now().isoformat()))
        
        # Create enrollment
        enrollment_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO enrollments (id, student_id, course_id, enrollment_date)
            VALUES (?, ?, ?, ?)
        ''', (enrollment_id, student_id, course_id, datetime.now().isoformat()))
        
        # Update course enrollment count
        cursor.execute('UPDATE courses SET enrolled = enrolled + 1 WHERE id = ?', (course_id,))
        
        conn.commit()
        conn.close()
        
        # Log analytics
        log_analytics('student_enrolled', course_id, {'student_id': student_id})
        
        return jsonify({
            'message': 'Student enrolled successfully',
            'enrollment_id': enrollment_id,
            'student_id': student_id
        })
        
    except Exception as e:
        logger.error(f"Error enrolling student: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/generate-course', methods=['POST'])
def generate_ai_course():
    """Generate AI-powered course suggestions"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        category = data.get('category', 'General')
        
        if not title:
            return jsonify({'error': 'Course title is required'}), 400
        
        suggestions = ai_assistant.generate_course_description(title, category)
        
        return jsonify({
            'suggestions': suggestions,
            'ai_powered': bool(ai_assistant.api_key)
        })
        
    except Exception as e:
        logger.error(f"Error generating AI course: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """Get dashboard analytics data"""
    try:
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('SELECT COUNT(*) FROM courses')
        total_courses = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(enrolled) FROM courses')
        total_students = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(DISTINCT instructor) FROM courses')
        total_instructors = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(rating) FROM courses WHERE rating > 0')
        avg_rating = cursor.fetchone()[0] or 0
        
        # Get category distribution
        cursor.execute('SELECT category, COUNT(*) as count FROM courses GROUP BY category')
        category_distribution = [{'category': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Get enrollment trends (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        cursor.execute('''
            SELECT DATE(enrollment_date) as date, COUNT(*) as enrollments
            FROM enrollments 
            WHERE enrollment_date >= ?
            GROUP BY DATE(enrollment_date)
            ORDER BY date
        ''', (thirty_days_ago,))
        enrollment_trends = [{'date': row[0], 'enrollments': row[1]} for row in cursor.fetchall()]
        
        # Get top performing courses
        cursor.execute('''
            SELECT title, enrolled, capacity, rating, 
                   CASE WHEN capacity > 0 THEN (enrolled * 100.0 / capacity) ELSE 0 END as fill_rate
            FROM courses 
            WHERE status = 'active'
            ORDER BY rating DESC, fill_rate DESC
            LIMIT 5
        ''')
        top_courses = []
        for row in cursor.fetchall():
            top_courses.append({
                'title': row[0],
                'enrolled': row[1],
                'capacity': row[2],
                'rating': row[3] or 0,
                'fill_rate': round(row[4], 1)
            })
        
        conn.close()
        
        return jsonify({
            'stats': {
                'total_courses': total_courses,
                'total_students': total_students,
                'total_instructors': total_instructors,
                'avg_rating': round(avg_rating, 1) if avg_rating else 0
            },
            'category_distribution': category_distribution,
            'enrollment_trends': enrollment_trends,
            'top_courses': top_courses
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/courses', methods=['GET'])
def export_courses():
    """Export courses to CSV or JSON"""
    try:
        format_type = request.args.get('format', 'json').lower()
        
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, description, duration, instructor, category, price, 
                   capacity, enrolled, status, rating, created_at, updated_at
            FROM courses
            ORDER BY created_at DESC
        ''')
        
        courses = cursor.fetchall()
        columns = ['id', 'title', 'description', 'duration', 'instructor', 'category', 
                  'price', 'capacity', 'enrolled', 'status', 'rating', 'created_at', 'updated_at']
        
        if format_type == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(courses)
            
            csv_data = output.getvalue()
            output.close()
            
            # Create file-like object for download
            csv_file = BytesIO()
            csv_file.write(csv_data.encode('utf-8'))
            csv_file.seek(0)
            
            conn.close()
            return send_file(
                csv_file,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'iron_lady_courses_{datetime.now().strftime("%Y%m%d")}.csv'
            )
        
        else:  # JSON format
            course_list = []
            for course in courses:
                course_dict = dict(zip(columns, course))
                course_list.append(course_dict)
            
            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_courses': len(course_list),
                'courses': course_list
            }
            
            conn.close()
            return jsonify(export_data)
    
    except Exception as e:
        logger.error(f"Error exporting courses: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/import/courses', methods=['POST'])
def import_courses():
    """Import courses from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'Only CSV files are supported'}), 400
        
        # Read and process CSV
        csv_content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # Validate required fields
                if not all(row.get(field) for field in ['title', 'instructor']):
                    errors.append(f"Row {row_num}: Missing required fields")
                    continue
                
                course_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT INTO courses (id, title, description, duration, instructor, category,
                                       price, capacity, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    course_id,
                    row.get('title', ''),
                    row.get('description', ''),
                    row.get('duration', ''),
                    row.get('instructor', ''),
                    row.get('category', 'General'),
                    float(row.get('price', 0)),
                    int(row.get('capacity', 30)),
                    row.get('status', 'draft'),
                    now, now
                ))
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Import completed. {imported_count} courses imported.',
            'imported_count': imported_count,
            'errors': errors[:10]  # Limit errors shown
        })
        
    except Exception as e:
        logger.error(f"Error importing courses: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bulk/update-status', methods=['PUT'])
def bulk_update_status():
    """Bulk update course status"""
    try:
        data = request.get_json()
        course_ids = data.get('course_ids', [])
        new_status = data.get('status', '')
        
        if not course_ids or not new_status:
            return jsonify({'error': 'Course IDs and status are required'}), 400
        
        valid_statuses = ['draft', 'active', 'completed', 'archived']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        # Build query with proper number of placeholders
        placeholders = ','.join(['?' for _ in course_ids])
        query = f'UPDATE courses SET status = ?, updated_at = ? WHERE id IN ({placeholders})'
        
        params = [new_status, datetime.now().isoformat()] + course_ids
        cursor.execute(query, params)
        
        updated_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Updated {updated_count} courses to {new_status} status',
            'updated_count': updated_count
        })
        
    except Exception as e:
        logger.error(f"Error bulk updating status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<course_id>/rate', methods=['POST'])
def rate_course(course_id):
    """Rate a course"""
    try:
        data = request.get_json()
        rating = data.get('rating', 0)
        review = data.get('review', '')
        student_id = data.get('student_id', str(uuid.uuid4()))
        
        if not 1 <= rating <= 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        # Check if course exists
        cursor.execute('SELECT id FROM courses WHERE id = ?', (course_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Course not found'}), 404
        
        # Add rating
        rating_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT OR REPLACE INTO course_ratings (id, course_id, student_id, rating, review, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (rating_id, course_id, student_id, rating, review, datetime.now().isoformat()))
        
        # Update course average rating
        cursor.execute('''
            SELECT AVG(rating) as avg_rating, COUNT(*) as total_ratings
            FROM course_ratings WHERE course_id = ?
        ''', (course_id,))
        
        avg_rating, total_ratings = cursor.fetchone()
        
        cursor.execute('''
            UPDATE courses SET rating = ?, total_ratings = ? WHERE id = ?
        ''', (round(avg_rating, 1), total_ratings, course_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Course rated successfully',
            'new_average_rating': round(avg_rating, 1),
            'total_ratings': total_ratings
        })
        
    except Exception as e:
        logger.error(f"Error rating course: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/suggestions', methods=['GET'])
def get_search_suggestions():
    """Get search suggestions"""
    try:
        query = request.args.get('q', '').lower()
        if len(query) < 2:
            return jsonify({'suggestions': []})
        
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        # Search in titles, instructors, and categories
        cursor.execute('''
            SELECT DISTINCT title as suggestion, 'course' as type FROM courses 
            WHERE LOWER(title) LIKE ? 
            UNION
            SELECT DISTINCT instructor as suggestion, 'instructor' as type FROM courses 
            WHERE LOWER(instructor) LIKE ?
            UNION  
            SELECT DISTINCT category as suggestion, 'category' as type FROM courses
            WHERE LOWER(category) LIKE ?
            LIMIT 10
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        suggestions = [{'text': row[0], 'type': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        return jsonify({'error': str(e)}), 500

def log_analytics(event_type: str, course_id: str, data: Dict):
    """Log analytics events"""
    try:
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        analytics_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO analytics (id, event_type, course_id, data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            analytics_id, event_type, course_id, 
            json.dumps(data), datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging analytics: {e}")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 Starting Iron Lady Advanced Course Management API")
    print("📊 Database initialized with sample data")
    print("🤖 AI Assistant", "enabled" if ai_assistant.api_key else "disabled (no API key)")
    print("🌐 Server running on http://localhost:5000")
    print("\n📋 Available Endpoints:")
    print("GET    /api/health - Health check")
    print("GET    /api/courses - List courses")
    print("POST   /api/courses - Create course") 
    print("PUT    /api/courses/<id> - Update course")
    print("DELETE /api/courses/<id> - Delete course")
    print("POST   /api/courses/<id>/enroll - Enroll student")
    print("POST   /api/courses/<id>/rate - Rate course")
    print("POST   /api/ai/generate-course - AI course generation")
    print("GET    /api/analytics/dashboard - Dashboard data")
    print("GET    /api/export/courses - Export courses")
    print("POST   /api/import/courses - Import courses")
    print("PUT    /api/bulk/update-status - Bulk status update")
    print("GET    /api/search/suggestions - Search suggestions")
    
    app.run(debug=True, host='0.0.0.0', port=5000)