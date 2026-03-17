"""
Study Planner Service — Generates daily study plans based on analytics.
"""
from studistics.utils.analysis import analyze_user_topics
from studistics.models import Exam
from datetime import date


def generate_daily_plan(user):
    """
    Generate a prioritised daily study plan for the user.

    Logic:
    1. Weak topics get "study" tasks (40 min each) — highest priority
    2. Moderate topics get "revision" tasks (20 min each)
    3. Topics linked to upcoming exams (next 7 days) get a "priority" boost

    Returns a list of task dicts:
        [{"topic": "...", "task_type": "study"|"revision", "duration_minutes": int}, ...]
    """
    analysis = analyze_user_topics(user)

    # Subjects with exams in the next 7 days
    upcoming_exam_subjects = set(
        Exam.objects.filter(
            user=user,
            exam_date__gte=date.today(),
            exam_date__lte=date.today(),
        )
        .values_list('subject_id', flat=True)
    )

    plan = []

    # --- Weak topics: study tasks (40 min) ---
    for entry in analysis['weak_topics']:
        topic = entry['topic']
        is_exam_soon = topic.subject_id in upcoming_exam_subjects
        plan.append({
            'topic': topic.name,
            'subject': topic.subject.name,
            'task_type': 'study',
            'duration_minutes': 40,
            'priority': 'high' if is_exam_soon else 'normal',
        })

    # --- Moderate topics: revision tasks (20 min) ---
    for entry in analysis['moderate_topics']:
        topic = entry['topic']
        is_exam_soon = topic.subject_id in upcoming_exam_subjects
        plan.append({
            'topic': topic.name,
            'subject': topic.subject.name,
            'task_type': 'revision',
            'duration_minutes': 20,
            'priority': 'high' if is_exam_soon else 'normal',
        })

    # Sort: high-priority items first
    plan.sort(key=lambda x: 0 if x['priority'] == 'high' else 1)

    return plan
