# live_class/utils/jitsi_free.py
import hashlib
import secrets
from django.conf import settings

def generate_room_name(session_id, class_name):
    """Generate a unique room name for the session"""
    # Create a unique identifier
    unique_string = f"{session_id}_{class_name}_{secrets.token_hex(8)}"
    
    # Hash it to create a clean room name
    room_hash = hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    return f"LiveClass_{room_hash}"

def is_room_moderator(user):
    """Determine if user should be a moderator"""
    # You can customize this logic based on your requirements
    # For example: staff users, course instructors, etc.
    return user.is_staff or user.is_superuser

def get_jitsi_config(room_name, display_name, is_moderator, user_email):
    """Get Jitsi configuration for the room"""
    config = {
        'roomName': room_name,
        'displayName': display_name,
        'email': user_email,
        'startWithAudioMuted': not is_moderator,
        'startWithVideoMuted': not is_moderator,
        'enableWelcomePage': False,
        'prejoinPageEnabled': False,
        'requireDisplayName': True,
    }
    
    if is_moderator:
        config.update({
            'moderator': True,
            'startWithAudioMuted': False,
            'startWithVideoMuted': False,
        })
    
    return config
