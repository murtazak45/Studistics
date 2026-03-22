"""
Study Planner Service — Generates daily study plans based on analytics.
"""
from studistics.utils.analysis import analyze_user_topics
from studistics.models import Exam
from datetime import date


def generate_daily_plan(user):
    """
    Generate a prioritised daily study plan for the user, capped at 6 hours.

    Logic:
    1. Weak topics get "study" tasks (1 hr each)
    2. Moderate topics get "revision" tasks (0.5 hr each)
    3. Exams in the next 7 days give a massive priority boost
    4. Capped at 6 hours daily to prevent student burnout
    """
    from datetime import timedelta
    analysis = analyze_user_topics(user)

    # Subjects with exams in the next 7 days
    upcoming_exam_subjects = set(
        Exam.objects.filter(
            user=user,
            exam_date__gte=date.today(),
            exam_date__lte=date.today() + timedelta(days=7),
        )
        .values_list('subject_id', flat=True)
    )

    all_tasks = []

    # --- Weak topics: study tasks (1 hr) ---
    for entry in analysis['weak_topics']:
        topic = entry['topic']
        is_exam_soon = topic.subject_id in upcoming_exam_subjects
        all_tasks.append({
            'topic': topic.name,
            'subject': topic.subject.name,
            'task_type': 'study',
            'duration_hours': 1.0,
            'priority': 'high' if is_exam_soon else 'normal',
        })

    # --- Moderate topics: revision tasks (0.5 hr) ---
    for entry in analysis['moderate_topics']:
        topic = entry['topic']
        is_exam_soon = topic.subject_id in upcoming_exam_subjects
        all_tasks.append({
            'topic': topic.name,
            'subject': topic.subject.name,
            'task_type': 'revision',
            'duration_hours': 0.5,
            'priority': 'high' if is_exam_soon else 'normal',
        })

    # Sort logic: High priority first, then study tasks over revision tasks
    def task_sort_key(task):
        score = 0
        if task['priority'] == 'high':
            score += 10
        if task['task_type'] == 'study':
            score += 5
        return -score

    all_tasks.sort(key=task_sort_key)

    # --- Cap Plan to prevent Burnout (Max 6 hours) ---
    MAX_DAILY_HOURS = 6.0
    current_hours = 0.0
    plan = []

    for task in all_tasks:
        if current_hours + task['duration_hours'] <= MAX_DAILY_HOURS:
            plan.append(task)
            current_hours += task['duration_hours']
        
        if current_hours >= MAX_DAILY_HOURS:
            break

    return plan
