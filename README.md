# University Course Schedule Generator

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)

A web-based system for **automatically generating conflict-free weekly course schedules** at universities. It replaces error-prone manual scheduling with an algorithmic approach, saving time and eliminating resource conflicts.

---

## Features

- **Automated schedule generation** using a backtracking algorithm with constraint satisfaction
- Define and manage departments, classrooms, instructors, and courses
- **Bulk data import/export** via Excel and CSV (powered by pandas and openpyxl)
- Automatic instructor assignment to courses
- View generated schedules through a web interface or export them to Excel
- Instructor and classroom availability constraint management
- Support for shared courses across departments with cross-department conflict detection
- Separate handling of lab sessions, lectures, and online (evening) time slots
- Django Admin panel for full data management

---

## Tech Stack

| Layer        | Technology                              |
|--------------|----------------------------------------|
| **Backend**  | Python 3.9+, Django 5.2                |
| **Database** | PostgreSQL                             |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap     |
| **Data I/O** | pandas, openpyxl, XlsxWriter          |
| **Admin UI** | Django Admin with django-admin-interface |
| **Containerization** | Docker                        |

---

## Algorithm: Backtracking with Constraint Satisfaction

The core scheduling engine (`schedule/scheduler.py`) implements a **backtracking search** algorithm — a well-established approach for solving constraint satisfaction problems (CSPs), which are NP-hard in the general case.

### How It Works

1. **Data Loading & Prioritization** — Courses are fetched from the database. University-wide compulsory courses are prioritized first, followed by lab sessions, then sorted by year and enrollment capacity.
2. **Candidate Generation** — For each unscheduled course, the algorithm generates all possible (day, time slot, classroom, instructor) assignments.
3. **Constraint Checking** — Each candidate is validated against:
   - Instructor availability (no double-booking, respects personal time-off constraints)
   - Classroom availability (no double-booking, capacity and type matching)
   - Student group conflicts (same department + year cannot have overlapping slots)
   - Global constraints (institution-wide blocked time slots)
4. **Assignment or Backtrack** — If a valid slot is found, the course is assigned and the algorithm moves to the next course. If no valid slot exists, it **backtracks** — undoing the last assignment and trying alternative placements.
5. **Completion** — The process repeats until every course is placed or all possibilities are exhausted. Unplaceable courses are reported separately.

> This approach guarantees a conflict-free schedule whenever one exists within the given constraints.

---

## Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 13+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yavuzhankursun/Ders-Programi.git
cd Ders-Programi/Ders_Programi

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure the database
# Edit dersprogrami_project/settings.py with your PostgreSQL credentials

# Apply migrations
python manage.py migrate

# Create an admin user
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

### Docker

```bash
cd Ders-Programi/Ders_Programi
docker build -t course-scheduler .
docker run -p 5000:5000 course-scheduler
```

---

## Usage

1. **Log in** to the Django Admin panel at `http://localhost:8000/admin/`.
2. **Add data** — Create departments, classrooms, instructors, and courses (or import them in bulk from Excel/CSV).
3. **Set constraints** — Define instructor availability and global time-slot restrictions.
4. **Generate the schedule** — Trigger the backtracking scheduler from the admin interface.
5. **Review & export** — View the generated schedule on the web interface or download it as an Excel file.

### Management Commands

```bash
# Import courses from an Excel file
python manage.py import_courses

# Auto-assign instructors to courses
python manage.py assign_all_instructors

# Generate the course schedule
python manage.py generate_schedule
```

---

## Testing

| Type             | Scope                                                   |
|------------------|---------------------------------------------------------|
| **Unit Tests**   | CRUD operations, management command outputs              |
| **System Tests** | End-to-end schedule generation, Excel export validation  |
| **User Tests**   | Interactive admin panel workflows                        |
| **Performance**  | Generates schedules for 200+ courses in under 5 seconds  |

---

## Future Improvements

- Genetic algorithm or constraint-programming solver as alternative scheduling backends
- AJAX-powered interactive calendar view
- Role-based access control with a student/instructor-facing frontend
- REST API for integration with external systems (SIS, LMS)
- Mobile-responsive interface or standalone mobile application

---

## License

This project is licensed under the terms of the license included in the repository.

---

> This project demonstrates the digitization of university course scheduling. Its modular architecture makes it straightforward to adapt to the needs of different institutions.
