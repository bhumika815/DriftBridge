"""
Reputation Service
Manages user reputation and trust levels
"""

from app import db
from app.models.user import User


# Reputation points for different actions
POINTS = {
    'bottle_thrown': 5,
    'bottle_kept': 10,
    'message_sent': 2,
    'journal_created': 15,
    'story_created': 10,
    'profile_completed': 25,
    'daily_login': 5,
    'chat_initiated': 8
}

# Trust levels based on points
TRUST_LEVELS = {
    'newcomer': {'min': 0, 'max': 50, 'badge': '🌱', 'name': 'Newcomer'},
    'explorer': {'min': 51, 'max': 150, 'badge': '🔍', 'name': 'Explorer'},
    'connector': {'min': 151, 'max': 300, 'badge': '🤝', 'name': 'Connector'},
    'trusted': {'min': 301, 'max': 500, 'badge': '⭐', 'name': 'Trusted'},
    'veteran': {'min': 501, 'max': 1000, 'badge': '👑', 'name': 'Veteran'},
    'legend': {'min': 1001, 'max': float('inf'), 'badge': '💎', 'name': 'Legend'}
}


def award_points(user_id: int, action: str, amount: int = None) -> int:
    """
    Award reputation points to a user for an action
    
    Args:
        user_id: ID of the user to award points to
        action: The action that earned points
        amount: Optional custom amount (overrides default)
        
    Returns:
        New total points
    """
    user = db.session.get(User, user_id)
    
    if not user:
        return 0
    
    # Use custom amount or default for action
    points_to_add = amount if amount is not None else POINTS.get(action, 0)
    
    user.points += points_to_add
    db.session.commit()
    
    return user.points


def deduct_points(user_id: int, amount: int) -> int:
    """
    Deduct reputation points from a user (for violations)
    
    Args:
        user_id: ID of the user
        amount: Points to deduct
        
    Returns:
        New total points
    """
    user = db.session.get(User, user_id)
    
    if not user:
        return 0
    
    user.points = max(0, user.points - amount)
    db.session.commit()
    
    return user.points


def get_trust_level(points: int) -> dict:
    """
    Get trust level information based on points
    
    Args:
        points: User's reputation points
        
    Returns:
        Dictionary with trust level info
    """
    for level_key, level_info in TRUST_LEVELS.items():
        if level_info['min'] <= points <= level_info['max']:
            return {
                'key': level_key,
                'badge': level_info['badge'],
                'name': level_info['name'],
                'min': level_info['min'],
                'max': level_info['max'],
                'progress': calculate_progress(points, level_info['min'], level_info['max'])
            }
    
    return TRUST_LEVELS['newcomer']


def calculate_progress(points: int, min_points: int, max_points: int) -> float:
    """
    Calculate progress percentage within current level
    
    Args:
        points: Current points
        min_points: Minimum points for level
        max_points: Maximum points for level
        
    Returns:
        Progress percentage (0-100)
    """
    if max_points == float('inf'):
        return 100.0
    
    range_size = max_points - min_points
    if range_size <= 0:
        return 100.0
    
    progress = ((points - min_points) / range_size) * 100
    return min(100.0, max(0.0, progress))


def get_user_trust_info(user_id: int) -> dict:
    """
    Get complete trust information for a user
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with all trust information
    """
    user = db.session.get(User, user_id)
    
    if not user:
        return None
    
    trust_level = get_trust_level(user.points)
    
    return {
        'points': user.points,
        'level': trust_level,
        'can_share_media': user.points >= 100,  # Unlock at 100 points
        'can_create_public_journals': user.points >= 50,  # Unlock at 50 points
        'can_send_voice_messages': user.points >= 150,  # Unlock at 150 points
        'max_daily_bottles': get_max_daily_bottles(user.points),
        'max_active_stories': get_max_active_stories(user.points)
    }


def get_max_daily_bottles(points: int) -> int:
    """
    Get maximum bottles user can throw per day based on points
    
    Args:
        points: User's reputation points
        
    Returns:
        Maximum daily bottles
    """
    if points < 50:
        return 3
    elif points < 150:
        return 5
    elif points < 300:
        return 10
    else:
        return 20


def get_max_active_stories(points: int) -> int:
    """
    Get maximum active stories user can have based on points
    
    Args:
        points: User's reputation points
        
    Returns:
        Maximum active stories
    """
    if points < 50:
        return 2
    elif points < 150:
        return 5
    elif points < 300:
        return 10
    else:
        return 20


def check_feature_unlock(user_id: int, feature: str) -> bool:
    """
    Check if a user has unlocked a specific feature
    
    Args:
        user_id: User ID
        feature: Feature to check ('media_sharing', 'voice_messages', etc.)
        
    Returns:
        Boolean indicating if feature is unlocked
    """
    trust_info = get_user_trust_info(user_id)
    
    if not trust_info:
        return False
    
    feature_map = {
        'media_sharing': trust_info['can_share_media'],
        'voice_messages': trust_info['can_send_voice_messages'],
        'public_journals': trust_info['can_create_public_journals']
    }
    
    return feature_map.get(feature, False)
