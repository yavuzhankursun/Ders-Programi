from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, UniqueConstraint, func, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
import json
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# Kullanıcılar tablosu
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    user_type = Column(String(20), nullable=False)  # 'ogrenci', 'ogretim_uyesi', 'yonetici'
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __init__(self, name, surname, email, password, user_type):
        self.name = name
        self.surname = surname
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.user_type = user_type
        logger.info(f"Yeni kullanıcı oluşturuldu: {email} ({user_type})")
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.name} {self.surname}"

# Öğretim üyeleri tablosu
class Faculty(Base):
    __tablename__ = 'faculty'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    title = Column(String(50), nullable=True)  # Unvan (Prof. Dr., Doç. Dr., Dr. Öğr. Üyesi, vb.), opsiyonel
    availability = Column(Text)  # JSON formatında uygunluk durumu
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user = relationship('User', backref='faculty_profile')
    
    def set_availability(self, availability_dict):
        self.availability = json.dumps(availability_dict)
        logger.info(f"Öğretim üyesi müsaitlik bilgileri güncellendi")
    
    def get_availability(self):
        if self.availability:
            return json.loads(self.availability)
        return {}

# Öğrenciler tablosu
class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    student_number = Column(String(20), unique=True, index=True)
    department_id = Column(Integer, ForeignKey('departments.id'))
    year = Column(Integer)  # 1, 2, 3, 4
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user = relationship('User', backref='student_profile')
    department = relationship('Department', backref='students')

# Bölümler tablosu
class Department(Base):
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, nullable=False, index=True)  # BLM, YZM, vb.
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Department {self.code}>"

# Dersler tablosu
class Course(Base):
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    weekly_hours = Column(Integer, nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    semester = Column(Integer)  # 1-8
    is_mandatory = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    fixed_time = Column(Text)  # JSON formatında zorunlu zaman bilgisi
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    instructor_id = Column(Integer, ForeignKey('faculty.id'))
    instructor = relationship('Faculty', backref='teaching_courses')
    department = relationship('Department', backref='courses')
    
    def set_fixed_time(self, fixed_time_dict):
        if fixed_time_dict:
            self.fixed_time = json.dumps(fixed_time_dict)
            logger.info(f"Ders sabit zamanı ayarlandı: {self.code}")
        else:
            self.fixed_time = None
    
    def get_fixed_time(self):
        if self.fixed_time:
            return json.loads(self.fixed_time)
        return None
    
    def __repr__(self):
        return f"<Course {self.code}>"

# Ortak dersler için eşleştirme tablosu
class SharedCourse(Base):
    __tablename__ = 'shared_courses'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    shared_with_department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    course = relationship('Course')
    shared_with_department = relationship('Department')
    
    __table_args__ = (
        UniqueConstraint('course_id', 'shared_with_department_id', name='uq_shared_course'),
    )

# Derslikler tablosu
class Classroom(Base):
    __tablename__ = 'classrooms'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False, unique=True, index=True)
    capacity = Column(Integer, nullable=False)
    type = Column(String(10), nullable=False)  # NORMAL, LAB
    location = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Classroom {self.name}>"

# Ders programı tablosu
class Schedule(Base):
    __tablename__ = 'schedule'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    day = Column(String(10), nullable=False)  # Pazartesi, Salı, vb.
    start_time = Column(String(5), nullable=False)  # "09:00"
    end_time = Column(String(5), nullable=False)  # "10:00"
    classroom_id = Column(Integer, ForeignKey('classrooms.id', ondelete='SET NULL'))
    is_online = Column(Boolean, default=False)
    academic_year = Column(String(20), nullable=False)  # "2024-2025"
    semester = Column(String(10), nullable=False)  # "Güz", "Bahar"
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    course = relationship('Course', backref='schedules')
    classroom = relationship('Classroom', backref='schedules')
    
    __table_args__ = (
        Index('idx_schedule_search', 'course_id', 'academic_year', 'semester'),
    )
    
    def __repr__(self):
        return f"<Schedule {self.course_id} on {self.day} at {self.start_time}-{self.end_time}>"
