"""
Management command to generate demo data for project demonstrations and testing.

Usage:
    python manage.py generate_demo_data

Creates a demo user with realistic academic data including subjects, topics,
study sessions (with varied strength profiles), exams, and revision logs.
"""
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker

from studistics.models import Subject, Topic, StudySession, Exam, RevisionLog

fake = Faker()

# ──────────────────────────────────────────────
# Structured Academic Dataset
# ──────────────────────────────────────────────
# Each subject maps to a list of (topic_name, strength_profile) tuples.
# strength_profile controls the analytics outcome:
#   "weak"     → low confidence, low score, short study time
#   "moderate" → mid confidence, mid score, medium study time
#   "strong"   → high confidence, high score, long study time, more revisions

CURRICULUM = {
    'Mathematics': {
        'description': 'Core mathematics including calculus, algebra, and probability.',
        'topics': [
            ('Calculus', 'strong'),
            ('Linear Algebra', 'moderate'),
            ('Probability', 'weak'),
            ('Differential Equations', 'moderate'),
        ],
    },
    'Physics': {
        'description': 'Classical mechanics, thermodynamics, and modern physics.',
        'topics': [
            ('Kinematics', 'strong'),
            ('Thermodynamics', 'weak'),
            ('Electromagnetism', 'moderate'),
            ('Optics', 'weak'),
        ],
    },
    'Database Systems': {
        'description': 'Relational databases, SQL, and database design principles.',
        'topics': [
            ('Normalization', 'weak'),
            ('Indexing', 'moderate'),
            ('Transactions', 'strong'),
            ('SQL Joins', 'moderate'),
            ('ER Diagrams', 'strong'),
        ],
    },
    'Machine Learning': {
        'description': 'Supervised and unsupervised learning algorithms.',
        'topics': [
            ('Regression', 'strong'),
            ('Classification', 'moderate'),
            ('Neural Networks', 'weak'),
            ('Clustering', 'moderate'),
            ('Decision Trees', 'strong'),
            ('Feature Engineering', 'weak'),
        ],
    },
    'Computer Networks': {
        'description': 'Network protocols, architecture, and security.',
        'topics': [
            ('TCP/IP Model', 'strong'),
            ('DNS', 'moderate'),
            ('Routing Algorithms', 'weak'),
            ('Network Security', 'moderate'),
        ],
    },
}

# Study session profiles per strength level
SESSION_PROFILES = {
    'weak': {
        'session_count': (1, 2),
        'study_time': (15, 30),
        'confidence': (1, 2),
        'practice_score': (1.0, 3.5),
        'revision_count': (0, 0),
    },
    'moderate': {
        'session_count': (2, 4),
        'study_time': (30, 55),
        'confidence': (2, 4),
        'practice_score': (4.0, 6.5),
        'revision_count': (0, 2),
    },
    'strong': {
        'session_count': (3, 6),
        'study_time': (45, 90),
        'confidence': (4, 5),
        'practice_score': (7.0, 10.0),
        'revision_count': (1, 3),
    },
}

# Exam definitions
EXAMS = [
    ('Database Systems', 'Database Systems Midterm', (10, 25)),
    ('Machine Learning', 'Machine Learning Quiz', (5, 15)),
    ('Mathematics', 'Mathematics Final', (30, 55)),
    ('Physics', 'Physics Lab Exam', (15, 35)),
    ('Computer Networks', 'Networks Practical', (20, 45)),
]


class Command(BaseCommand):
    help = 'Generate realistic demo data for project demonstrations and testing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n═══ Studistics Demo Data Generator ═══\n'))

        user = self._create_demo_user()
        subjects = self._create_subjects(user)
        topics, topic_count = self._create_topics(subjects)
        session_count = self._create_study_sessions(topics)
        revision_count = self._create_revision_logs(topics)
        exam_count = self._create_exams(user, subjects)

        # Summary
        self.stdout.write(self.style.MIGRATE_HEADING('\n── Summary ──'))
        self.stdout.write(f'  Subjects created : {len(subjects)}')
        self.stdout.write(f'  Topics created   : {topic_count}')
        self.stdout.write(f'  Study sessions   : {session_count}')
        self.stdout.write(f'  Revision logs    : {revision_count}')
        self.stdout.write(f'  Exams created    : {exam_count}')
        self.stdout.write(self.style.SUCCESS('\n✓ Demo dataset created successfully.\n'))

    # ── Demo User ───────────────────────────
    def _create_demo_user(self):
        user, created = User.objects.get_or_create(
            username='demo_student',
            defaults={
                'email': 'demo@student.com',
                'first_name': 'Demo',
                'last_name': 'Student',
            },
        )
        if created:
            user.set_password('demo1234')
            user.save()
            self.stdout.write(self.style.SUCCESS('  ✓ Demo user created (demo_student / demo1234)'))
        else:
            self.stdout.write('  • Demo user already exists — skipping')
        return user

    # ── Subjects ────────────────────────────
    def _create_subjects(self, user):
        subjects = {}
        for name, data in CURRICULUM.items():
            subject, created = Subject.objects.get_or_create(
                user=user,
                name=name,
                defaults={'description': data['description']},
            )
            subjects[name] = subject
            status = 'created' if created else 'exists'
            self.stdout.write(f'  {"✓" if created else "•"} Subject: {name} ({status})')
        return subjects

    # ── Topics ──────────────────────────────
    def _create_topics(self, subjects):
        topics = []
        count = 0
        for subject_name, data in CURRICULUM.items():
            subject = subjects[subject_name]
            for topic_name, strength in data['topics']:
                topic, created = Topic.objects.get_or_create(
                    subject=subject,
                    name=topic_name,
                    defaults={
                        'confidence_level': {
                            'weak': 'Weak',
                            'moderate': 'Moderate',
                            'strong': 'Strong',
                        }[strength],
                        'last_studied_date': date.today() - timedelta(days=random.randint(0, 14)),
                    },
                )
                if created:
                    count += 1
                topics.append((topic, strength))
        self.stdout.write(f'  ✓ Topics processed: {len(topics)} ({count} new)')
        return topics, count

    # ── Study Sessions ──────────────────────
    def _create_study_sessions(self, topics):
        total = 0
        for topic, strength in topics:
            profile = SESSION_PROFILES[strength]
            num_sessions = random.randint(*profile['session_count'])

            for i in range(num_sessions):
                session = StudySession.objects.create(
                    topic=topic,
                    study_time=random.randint(*profile['study_time']),
                    confidence_level=random.randint(*profile['confidence']),
                    practice_score=round(random.uniform(*profile['practice_score']), 1),
                    revision_count=random.randint(*profile['revision_count']),
                )
                # Backdate the auto_now_add date to spread sessions over the last 30 days
                past_date = date.today() - timedelta(days=random.randint(0, 30))
                StudySession.objects.filter(pk=session.pk).update(date=past_date)
                total += 1

        self.stdout.write(f'  ✓ Study sessions created: {total}')
        return total

    # ── Revision Logs ───────────────────────
    def _create_revision_logs(self, topics):
        total = 0
        for topic, strength in topics:
            # Strong topics get recent revisions, weak topics may have none
            if strength == 'strong':
                num_revisions = random.randint(1, 3)
            elif strength == 'moderate':
                num_revisions = random.choice([0, 0, 1])
            else:
                num_revisions = 0  # Weak topics: no revisions (triggers reminders)

            for _ in range(num_revisions):
                log = RevisionLog.objects.create(topic=topic)
                past_date = date.today() - timedelta(days=random.randint(0, 7))
                RevisionLog.objects.filter(pk=log.pk).update(revision_date=past_date)
                total += 1

        self.stdout.write(f'  ✓ Revision logs created: {total}')
        return total

    # ── Exams ───────────────────────────────
    def _create_exams(self, user, subjects):
        total = 0
        for subject_name, exam_name, day_range in EXAMS:
            if subject_name not in subjects:
                continue
            exam, created = Exam.objects.get_or_create(
                user=user,
                subject=subjects[subject_name],
                exam_name=exam_name,
                defaults={
                    'exam_date': date.today() + timedelta(days=random.randint(*day_range)),
                },
            )
            if created:
                total += 1
            status = 'created' if created else 'exists'
            self.stdout.write(f'  {"✓" if created else "•"} Exam: {exam_name} ({status})')
        return total
