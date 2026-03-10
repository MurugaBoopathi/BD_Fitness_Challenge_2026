# utils/auth_utils.py
"""
Authentication utilities for BD Fitness Challenge App
Provides secure user authentication using Firebase Authentication
"""

import hashlib
import secrets
import streamlit as st
from datetime import datetime, timedelta
from firebase_admin import auth
from firebase_config import db


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


def hash_password(password: str, salt: str = None) -> tuple:
    """
    Hash a password using SHA256 with salt
    Returns: (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(32)
    
    # Combine password and salt
    pwd_salt = f"{password}{salt}".encode('utf-8')
    hashed = hashlib.sha256(pwd_salt).hexdigest()
    
    return hashed, salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify a password against its hash
    """
    test_hash, _ = hash_password(password, salt)
    return test_hash == hashed_password


def validate_email(email: str) -> bool:
    """
    Basic email validation
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, ""


def create_user_account(email: str, password: str, full_name: str, department: str = None, strava_id: str = None) -> dict:
    """
    Create a new user account with email and password
    Returns: user_data dict or raises AuthenticationError
    """
    try:
        # Validate inputs
        if not validate_email(email):
            raise AuthenticationError("Invalid email format")
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            raise AuthenticationError(error_msg)
        
        if not full_name or len(full_name.strip()) < 2:
            raise AuthenticationError("Please provide a valid full name")
        
        # Check if email already exists
        users_ref = db.collection("users")
        existing = users_ref.where("email", "==", email.lower()).limit(1).stream()
        if any(existing):
            raise AuthenticationError("An account with this email already exists")
        
        # Check if this is the first user (auto-grant admin)
        all_users = list(users_ref.limit(1).stream())
        is_first_user = len(all_users) == 0
        
        # Hash the password
        hashed_pwd, salt = hash_password(password)
        
        # Create user document in Firestore
        user_data = {
            "email": email.lower(),
            "full_name": full_name.strip(),
            "password_hash": hashed_pwd,
            "password_salt": salt,
            "height": 0,
            "weight": 0,
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
            "is_active": True,
            "is_admin": is_first_user  # First user gets admin automatically
        }
        
        # Add department if provided
        if department:
            user_data["department"] = department
        
        # Add Strava ID if provided
        if strava_id and strava_id.strip():
            user_data["strava_id"] = strava_id.strip()
        
        # Add to Firestore
        new_user_ref = users_ref.document()
        new_user_ref.set(user_data)
        
        user_data['uid'] = new_user_ref.id
        return user_data
        
    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(f"Error creating account: {str(e)}")


def authenticate_user(email: str, password: str) -> dict:
    """
    Authenticate a user with email and password
    Returns: user_data dict or raises AuthenticationError
    """
    try:
        # Validate email format
        if not validate_email(email):
            raise AuthenticationError("Invalid email format")
        
        # Find user by email
        users_ref = db.collection("users")
        query = users_ref.where("email", "==", email.lower()).limit(1).stream()
        
        user_doc = next(iter(query), None)
        if user_doc is None:
            raise AuthenticationError("Invalid email or password")
        
        user_data = user_doc.to_dict()
        user_data['uid'] = user_doc.id
        
        # Check if account is active
        if not user_data.get('is_active', True):
            raise AuthenticationError("Account is disabled. Please contact support.")
        
        # Verify password
        password_hash = user_data.get('password_hash')
        password_salt = user_data.get('password_salt')
        
        if not password_hash or not password_salt:
            raise AuthenticationError("Account configuration error. Please contact support.")
        
        if not verify_password(password, password_hash, password_salt):
            raise AuthenticationError("Invalid email or password")
        
        # Update last login time
        users_ref.document(user_doc.id).update({
            "last_login": datetime.now().isoformat()
        })
        
        return user_data
        
    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(f"Authentication error: {str(e)}")


def initialize_session(user_data: dict):
    """
    Initialize user session in Streamlit
    """
    st.session_state['authenticated'] = True
    st.session_state['user_email'] = user_data['email']
    st.session_state['user_name'] = user_data['full_name']
    st.session_state['uid'] = user_data['uid']
    st.session_state['is_admin'] = user_data.get('is_admin', False)
    st.session_state['login_time'] = datetime.now().isoformat()


def clear_session():
    """
    Clear user session (logout)
    """
    # Clear all session state keys
    keys_to_clear = ['authenticated', 'user_email', 'user_name', 'uid', 'login_time', 'is_admin']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def is_authenticated() -> bool:
    """
    Check if user is authenticated
    """
    return st.session_state.get('authenticated', False)


def require_authentication():
    """
    Decorator-like function to require authentication
    Call this at the start of protected pages
    """
    if not is_authenticated():
        return False
    return True


def get_current_user() -> dict:
    """
    Get current authenticated user data
    Returns: dict with uid, email, full_name, is_admin
    """
    if not is_authenticated():
        return None
    
    return {
        'uid': st.session_state.get('uid'),
        'email': st.session_state.get('user_email'),
        'full_name': st.session_state.get('user_name'),
        'is_admin': st.session_state.get('is_admin', False)
    }


def is_admin() -> bool:
    """
    Check if current user has admin privileges
    """
    return st.session_state.get('is_admin', False)


def admin_reset_password(uid: str, new_password: str) -> bool:
    """
    Admin function to reset any user's password
    Does NOT require current password - for admin use only
    Returns: True if successful, raises AuthenticationError otherwise
    """
    try:
        # Validate new password
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            raise AuthenticationError(error_msg)
        
        # Get user document
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise AuthenticationError("User not found")
        
        # Hash new password
        new_hash, new_salt = hash_password(new_password)
        
        # Update password in database
        user_ref.update({
            "password_hash": new_hash,
            "password_salt": new_salt,
            "password_updated_at": datetime.now().isoformat(),
            "password_reset_by_admin": True
        })
        
        return True
        
    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(f"Error resetting password: {str(e)}")


def change_password(uid: str, current_password: str, new_password: str) -> bool:
    """
    Change user password
    Returns: True if successful, raises AuthenticationError otherwise
    """
    try:
        # Validate new password
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            raise AuthenticationError(error_msg)
        
        # Get user document
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise AuthenticationError("User not found")
        
        user_data = user_doc.to_dict()
        
        # Verify current password
        if not verify_password(current_password, user_data['password_hash'], user_data['password_salt']):
            raise AuthenticationError("Current password is incorrect")
        
        # Hash new password
        new_hash, new_salt = hash_password(new_password)
        
        # Update password in database
        user_ref.update({
            "password_hash": new_hash,
            "password_salt": new_salt,
            "password_updated_at": datetime.now().isoformat()
        })
        
        return True
        
    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(f"Error changing password: {str(e)}")


def request_password_reset(email: str) -> str:
    """
    Generate a password reset token for a user
    Returns: reset_token
    """
    try:
        # Find user by email
        users_ref = db.collection("users")
        query = users_ref.where("email", "==", email.lower()).limit(1).stream()
        
        user_doc = next(iter(query), None)
        if user_doc is None:
            # Don't reveal if email exists or not for security
            return "If the email exists, a reset link will be sent"
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        
        # Store token with expiration (24 hours)
        expiration = (datetime.now() + timedelta(hours=24)).isoformat()
        
        users_ref.document(user_doc.id).update({
            "reset_token": reset_token,
            "reset_token_expiration": expiration
        })
        
        # In production, send this token via email
        # For now, return it (in production you wouldn't return it directly)
        return f"Password reset token: {reset_token}"
        
    except Exception as e:
        # Don't reveal errors for security
        return "If the email exists, a reset link will be sent"


def reset_password_with_token(email: str, token: str, new_password: str) -> bool:
    """
    Reset password using a valid token
    """
    try:
        # Validate new password
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            raise AuthenticationError(error_msg)
        
        # Find user
        users_ref = db.collection("users")
        query = users_ref.where("email", "==", email.lower()).limit(1).stream()
        
        user_doc = next(iter(query), None)
        if user_doc is None:
            raise AuthenticationError("Invalid reset token")
        
        user_data = user_doc.to_dict()
        
        # Verify token
        stored_token = user_data.get('reset_token')
        token_expiration = user_data.get('reset_token_expiration')
        
        if not stored_token or stored_token != token:
            raise AuthenticationError("Invalid reset token")
        
        # Check expiration
        if datetime.fromisoformat(token_expiration) < datetime.now():
            raise AuthenticationError("Reset token has expired")
        
        # Hash new password
        new_hash, new_salt = hash_password(new_password)
        
        # Update password and clear reset token
        users_ref.document(user_doc.id).update({
            "password_hash": new_hash,
            "password_salt": new_salt,
            "reset_token": None,
            "reset_token_expiration": None,
            "password_updated_at": datetime.now().isoformat()
        })
        
        return True
        
    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(f"Error resetting password: {str(e)}")


def migrate_existing_user_to_auth(uid: str, full_name: str, default_email: str = None) -> str:
    """
    Helper function to migrate existing users without authentication to the new system
    Generates a temporary password that should be changed on first login
    """
    try:
        # Generate a temporary password
        temp_password = secrets.token_urlsafe(12)
        
        # If no email provided, create one based on name
        if not default_email:
            # Create email from name (replace spaces with dots, make lowercase)
            email_base = full_name.lower().replace(" ", ".").replace("(", "").replace(")", "")
            default_email = f"{email_base}@bdchallenge.temp"
        
        # Hash password
        hashed_pwd, salt = hash_password(temp_password)
        
        # Update existing user document
        user_ref = db.collection("users").document(uid)
        user_ref.update({
            "email": default_email.lower(),
            "password_hash": hashed_pwd,
            "password_salt": salt,
            "is_active": True,
            "requires_password_change": True,
            "migrated_at": datetime.now().isoformat()
        })
        
        return temp_password
        
    except Exception as e:
        raise AuthenticationError(f"Error migrating user: {str(e)}")


def set_admin_status(uid: str, is_admin: bool) -> bool:
    """
    Set or remove admin privileges for a user
    Returns: True if successful
    """
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise AuthenticationError("User not found")
        
        user_ref.update({
            "is_admin": is_admin,
            "admin_updated_at": datetime.now().isoformat()
        })
        
        return True
        
    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(f"Error updating admin status: {str(e)}")


def get_all_users() -> list:
    """
    Get all users (admin only)
    Returns: list of user dictionaries
    """
    try:
        users_ref = db.collection("users")
        all_users = list(users_ref.stream())
        
        users_list = []
        for user_doc in all_users:
            user_data = user_doc.to_dict()
            user_data['uid'] = user_doc.id
            users_list.append(user_data)
        
        return users_list
        
    except Exception as e:
        raise AuthenticationError(f"Error fetching users: {str(e)}")
