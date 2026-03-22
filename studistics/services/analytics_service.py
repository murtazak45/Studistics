"""
Analytics Service -- Provides chart-ready data for the dashboard.

All functions return dicts with 'labels' and 'values' lists suitable
for direct consumption by Chart.js on the frontend.

Requires: pip install pandas numpy
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta

from studistics.models import StudySession
from studistics.utils.analysis import analyze_user_topics


def get_study_time_trend(user):
    """
    Daily total study time over the last 7 days.

    Returns:
        {"labels": ["Mar 15", ...], "values": [120, 45, ...]}
    """
    seven_days_ago = date.today() - timedelta(days=6)

    qs = StudySession.objects.filter(
        topic__subject__user=user,
        date__gte=seven_days_ago,
    ).values('date', 'study_time')

    # Build a complete 7-day range so the chart always has 7 points
    date_range = pd.date_range(end=date.today(), periods=7, freq='D')
    result = pd.Series(0.0, index=date_range, dtype=float)

    if qs.exists():
        df = pd.DataFrame(list(qs))
        df['date'] = pd.to_datetime(df['date'])
        grouped = df.groupby('date')['study_time'].sum()
        for d, val in grouped.items():
            if d in result.index:
                result[d] = round(float(val), 1)

    return {
        "labels": [d.strftime('%b %d') for d in result.index],
        "values": result.tolist(),
    }


def get_confidence_trend(user):
    """
    Daily average confidence level over the last 7 days.

    Returns:
        {"labels": ["Mar 15", ...], "values": [3.2, 4.0, ...]}
    """
    seven_days_ago = date.today() - timedelta(days=6)

    qs = StudySession.objects.filter(
        topic__subject__user=user,
        date__gte=seven_days_ago,
    ).values('date', 'confidence_level')

    date_range = pd.date_range(end=date.today(), periods=7, freq='D')
    result = pd.Series(0.0, index=date_range, dtype=float)

    if qs.exists():
        df = pd.DataFrame(list(qs))
        df['date'] = pd.to_datetime(df['date'])
        grouped = df.groupby('date')['confidence_level'].mean()
        for d, val in grouped.items():
            if d in result.index:
                result[d] = round(float(val), 1)

    return {
        "labels": [d.strftime('%b %d') for d in result.index],
        "values": result.tolist(),
    }


def get_topic_strength_distribution(user):
    """
    Count of weak / moderate / strong topics.

    Reuses the existing analyse_user_topics() utility so scoring
    logic is never duplicated.

    Returns:
        {"labels": ["Weak", "Moderate", "Strong"], "values": [6, 8, 9]}
    """
    analysis = analyze_user_topics(user)

    return {
        "labels": ["Weak", "Moderate", "Strong"],
        "values": [
            len(analysis['weak_topics']),
            len(analysis['moderate_topics']),
            len(analysis['strong_topics']),
        ],
    }
