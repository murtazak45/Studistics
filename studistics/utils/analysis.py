"""
Analytics utilities for topic strength evaluation and dashboard metrics.
"""
from django.db.models import Sum, Avg

from studistics.models import Subject, Topic, RevisionLog


def calculate_topic_strength(topic):
    """
    Calculate a topic's strength score based on study session analytics.

    Scoring formula generates a normalized 0-100 score:
        Base = (Avg Confidence / 5.0) * 100
        If Marks exist: Base = (Base + Avg Marks) / 2
        Effort Bonus (max 20) = (Revisions * 3) + (Hours * 2)
        Final Score = min(Base + Bonus, 100)

    Classification:
        score < 40  → "weak"
        40 ≤ score < 75 → "moderate"
        score ≥ 75  → "strong"

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

    total_study_time = aggregates['total_study_time'] or 0.0
    average_confidence = aggregates['average_confidence'] or 0.0
    average_marks = aggregates['average_marks']
    total_revisions = aggregates['total_revisions'] or 0

    base_score = (average_confidence / 5.0) * 100.0

    if average_marks is not None:
        base_score = (base_score + average_marks) / 2.0

    effort_bonus = min((total_revisions * 3.0) + (total_study_time * 2.0), 20.0)

    score = min(base_score + effort_bonus, 100.0)

    if score < 40:
        strength = "weak"
    elif score < 75:
        strength = "moderate"
    else:
        strength = "strong"

    return {"score": round(score, 2), "strength": strength}


def analyze_user_topics(user):
    """
    Analyse all topics for a user and classify them by strength.
    Uses ORM annotations to prevent N+1 querying.
    """
    from django.db.models import Sum, Avg, Count
    
    topics = Topic.objects.filter(subject__user=user).select_related('subject').annotate(
        total_study_time=Sum('sessions__study_time'),
        average_confidence=Avg('sessions__confidence_level'),
        average_marks=Avg('sessions__practice_score'),
        total_revisions=Sum('sessions__revision_count'),
        session_count=Count('sessions')
    )

    weak_topics = []
    moderate_topics = []
    strong_topics = []

    for topic in topics:
        if topic.session_count == 0:
            result = {"score": 0, "strength": "weak"}
        else:
            total_study_time = topic.total_study_time or 0.0
            average_confidence = topic.average_confidence or 0.0
            average_marks = topic.average_marks
            total_revisions = topic.total_revisions or 0

            base_score = (average_confidence / 5.0) * 100.0
            if average_marks is not None:
                base_score = (base_score + average_marks) / 2.0

            effort_bonus = min((total_revisions * 3.0) + (total_study_time * 2.0), 20.0)
            score = min(base_score + effort_bonus, 100.0)

            if score < 40:
                strength = "weak"
            elif score < 75:
                strength = "moderate"
            else:
                strength = "strong"
                
            result = {"score": round(score, 2), "strength": strength}

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
