"""
Management command to generate demo data for project demonstrations and testing.

Usage:
    python manage.py generate_demo_data           # additive (safe to re-run)
    python manage.py generate_demo_data --clear    # wipe demo user data first

Creates a demo user with realistic academic data including subjects, topics,
study sessions (with varied strength profiles), exams, and revision logs.

The generated data produces meaningful analytics output that is compatible
with the dashboard, weakness detection, and study planner features.

Requires: pip install faker
"""
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker

from studistics.models import Subject, Topic, StudySession, Exam, RevisionLog

fake = Faker()

# --------------------------------------------------
# Structured Academic Dataset
# --------------------------------------------------
# Each subject maps to a list of (topic_name, strength_profile) tuples.
# strength_profile controls the analytics outcome:
#   "weak"     -> low confidence, low score, short study time
#   "moderate" -> mid confidence, mid score, medium study time
#   "strong"   -> high confidence, high score, long study time, more revisions

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

# --------------------------------------------------
# Study session profiles per strength level
# --------------------------------------------------
# Tuned to produce reliable analytics scores using the formula:
#   score = (avg_confidence * 20) + (avg_practice_score * 10)
#         + (total_revisions * 5) + (total_study_time * 0.1)
#
# Target score bands:
#   weak     -> score < 40
#   moderate -> 40 <= score < 70
#   strong   -> score >= 70

SESSION_PROFILES = {
    'weak': {
        'session_count': (5, 8),        # 5-8 sessions
        'study_time': (15, 30),         # short study time
        'confidence': (1, 2),           # very low / low
        'practice_score': (1.0, 3.0),   # low score
        'revision_count': (0, 0),       # no revisions
    },
    'moderate': {
        'session_count': (7, 12),       # 7-12 sessions
        'study_time': (30, 60),         # medium study time
        'confidence': (2, 4),           # low - high
        'practice_score': (4.0, 6.5),   # mid score
        'revision_count': (0, 2),       # some revisions
    },
    'strong': {
        'session_count': (10, 15),      # 10-15 sessions
        'study_time': (60, 120),        # long study time
        'confidence': (4, 5),           # high / very high
        'practice_score': (7.0, 10.0),  # high score
        'revision_count': (1, 3),       # frequent revisions
    },
}

# --------------------------------------------------
# Exam definitions
# --------------------------------------------------
# (subject_name, exam_name, (min_days_ahead, max_days_ahead))
EXAMS = [
    ('Database Systems', 'DBMS Midterm', (10, 25)),
    ('Machine Learning', 'ML Quiz', (5, 15)),
    ('Mathematics', 'Math Final', (30, 55)),
    ('Physics', 'Physics Lab Exam', (15, 35)),
    ('Computer Networks', 'Networks Practical', (20, 45)),
]


class Command(BaseCommand):
    help = 'Generate realistic demo data for project demonstrations and testing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete ALL existing demo-user data before regenerating (full reset).',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n=== Studistics Demo Data Generator ===\n'
        ))

        user = self._create_demo_user()

        if options['clear']:
            self._clear_demo_data(user)

        subjects = self._create_subjects(user)
        topics, topic_count = self._create_topics(subjects)
        session_count = self._create_study_sessions(topics)
        revision_count = self._create_revision_logs(topics)
        exam_count = self._create_exams(user, subjects)

        # -- Summary --
        self.stdout.write(self.style.MIGRATE_HEADING('\n-- Summary --'))
        self.stdout.write(f'  Subjects created : {len(subjects)}')
        self.stdout.write(f'  Topics created   : {topic_count}')
        self.stdout.write(f'  Study sessions   : {session_count}')
        self.stdout.write(f'  Revision logs    : {revision_count}')
        self.stdout.write(f'  Exams created    : {exam_count}')
        self.stdout.write(self.style.SUCCESS(
            '\n[OK] Demo Data Created Successfully\n'
        ))

    # -- Clear ------------------------------------
    def _clear_demo_data(self, user):
        """Delete all data owned by the demo user for a clean slate."""
        subjects = Subject.objects.filter(user=user)
        # Cascading deletes handle Topics -> StudySessions / RevisionLogs
        session_count = StudySession.objects.filter(
            topic__subject__user=user
        ).count()
        revision_count = RevisionLog.objects.filter(
            topic__subject__user=user
        ).count()
        exam_count = Exam.objects.filter(user=user).count()
        topic_count = Topic.objects.filter(subject__user=user).count()
        subject_count = subjects.count()

        # Delete in order (children first avoids integrity issues on some DBs)
        RevisionLog.objects.filter(topic__subject__user=user).delete()
        StudySession.objects.filter(topic__subject__user=user).delete()
        Exam.objects.filter(user=user).delete()
        Topic.objects.filter(subject__user=user).delete()
        subjects.delete()

        self.stdout.write(self.style.WARNING(
            f'  [!] Cleared: {subject_count} subjects, {topic_count} topics, '
            f'{session_count} sessions, {revision_count} revisions, '
            f'{exam_count} exams'
        ))

    # -- Demo User ---------------------------------
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
            self.stdout.write(self.style.SUCCESS(
                '  [+] Demo user created (demo_student / demo1234)'
            ))
        else:
            self.stdout.write('  [=] Demo user already exists -- reusing')
        return user

    # -- Subjects ----------------------------------
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
            tag = '[+]' if created else '[=]'
            self.stdout.write(f'  {tag} Subject: {name} ({status})')
        return subjects

    # -- Topics ------------------------------------
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
                        'last_studied_date': date.today() - timedelta(
                            days=random.randint(0, 14)
                        ),
                    },
                )
                if created:
                    count += 1
                topics.append((topic, strength))
        self.stdout.write(f'  [+] Topics processed: {len(topics)} ({count} new)')
        return topics, count

    # -- Study Sessions -----------------------------
    def _create_study_sessions(self, topics):
        total = 0
        for topic, strength in topics:
            profile = SESSION_PROFILES[strength]
            num_sessions = random.randint(*profile['session_count'])

            for _ in range(num_sessions):
                session = StudySession.objects.create(
                    topic=topic,
                    study_time=random.randint(*profile['study_time']),
                    confidence_level=random.randint(*profile['confidence']),
                    practice_score=round(
                        random.uniform(*profile['practice_score']), 1
                    ),
                    revision_count=random.randint(*profile['revision_count']),
                )
                # Backdate the auto_now_add date to spread sessions
                # over the last 30 days
                past_date = date.today() - timedelta(
                    days=random.randint(0, 30)
                )
                StudySession.objects.filter(pk=session.pk).update(
                    date=past_date
                )
                total += 1

        self.stdout.write(f'  [+] Study sessions created: {total}')
        return total

    # -- Revision Logs -----------------------------
    def _create_revision_logs(self, topics):
        total = 0
        for topic, strength in topics:
            # Strong topics get recent revisions, weak topics have none
            if strength == 'strong':
                num_revisions = random.randint(1, 3)
            elif strength == 'moderate':
                num_revisions = random.choice([0, 0, 1])
            else:
                num_revisions = 0  # Weak topics: no revisions -> triggers reminders

            for _ in range(num_revisions):
                log = RevisionLog.objects.create(topic=topic)
                past_date = date.today() - timedelta(
                    days=random.randint(0, 7)
                )
                RevisionLog.objects.filter(pk=log.pk).update(
                    revision_date=past_date
                )
                total += 1

        self.stdout.write(f'  [+] Revision logs created: {total}')
        return total

    # -- Exams -------------------------------------
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
                    'exam_date': date.today() + timedelta(
                        days=random.randint(*day_range)
                    ),
                },
            )
            if created:
                total += 1
            status = 'created' if created else 'exists'
            tag = '[+]' if created else '[=]'
            self.stdout.write(f'  {tag} Exam: {exam_name} ({status})')
        return total
