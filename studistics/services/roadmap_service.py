"""
Roadmap Service — Generates learning roadmap recommendations.
"""
from studistics.utils.analysis import analyze_user_topics


def generate_learning_roadmap(user):
    """
    Generate simple learning roadmap recommendations based on topic analysis.

    Prioritises weak topics with study recommendations, then suggests
    revision for moderate topics.

    Args:
        user: The Django User instance.

    Returns:
        A list of recommendation strings.
    """
    analysis = analyze_user_topics(user)
    recommendations = []

    for entry in analysis['weak_topics']:
        recommendations.append(f"Review {entry['topic'].name} ({entry['topic'].subject.name})")

    for entry in analysis['moderate_topics']:
        recommendations.append(f"Practice {entry['topic'].name} ({entry['topic'].subject.name})")

    if not recommendations:
        recommendations.append("Great work! All topics are strong. Keep revising to stay sharp.")

    return recommendations
