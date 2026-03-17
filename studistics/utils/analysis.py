"""
Analytics utilities for topic strength evaluation and dashboard metrics.
"""
from django.db.models import Sum, Avg

from studistics.models import Subject, Topic, RevisionLog


def calculate_topic_strength(topic):
    """
    Calculate a topic's strength score based on study session analytics.

    Scoring formula:
        score = (avg_confidence * 20) + (avg_marks * 10)
              + (total_revisions * 5) + (total_study_time * 0.1)

    Classification:
        score < 40  → "weak"
        40 ≤ score < 70 → "moderate"
        score ≥ 70  → "strong"

    Returns a dict with 'score' and 'strength' keys.
    """
    sessions = topic.sessions.all()

    if not sessions.exists():
        return {"score": 0, "strength": "weak"}

    aggregates = sessions.aggregate(
        total_study_time=Sum('study_time'),
        average_confidence=Avg('confidence_level'),
        average_marks=Avg('practice_score'),
        total_revisions=Sum('revision_count'),
    )

    total_study_time = aggregates['total_study_time'] or 0
    average_confidence = aggregates['average_confidence'] or 0
    average_marks = aggregates['average_marks'] or 0
    total_revisions = aggregates['total_revisions'] or 0

    score = (
        (average_confidence * 20)
        + (average_marks * 10)
        + (total_revisions * 5)
        + (total_study_time * 0.1)
    )

    if score < 40:
        strength = "weak"
    elif score < 70:
        strength = "moderate"
    else:
        strength = "strong"

    return {"score": round(score, 2), "strength": strength}


def analyze_user_topics(user):
    """
    Analyse all topics for a user and classify them by strength.

    Returns a dict with 'weak_topics', 'moderate_topics', 'strong_topics' lists.
    Each item is a dict containing the topic object and its analysis result.
    """
    subjects = Subject.objects.filter(user=user)
    topics = Topic.objects.filter(subject__in=subjects)

    weak_topics = []
    moderate_topics = []
    strong_topics = []

    for topic in topics:
        result = calculate_topic_strength(topic)
        entry = {"topic": topic, **result}

        if result["strength"] == "weak":
            weak_topics.append(entry)
        elif result["strength"] == "moderate":
            moderate_topics.append(entry)
        else:
            strong_topics.append(entry)

    return {
        "weak_topics": weak_topics,
        "moderate_topics": moderate_topics,
        "strong_topics": strong_topics,
    }
