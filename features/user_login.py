
import asyncio
from uuid import uuid4 
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timezone

from scripts.supabase_setup import create_user, get_user, get_password, get_session
from scripts.config import settings


async def verify_session(session_id):

    try:

        session = await get_session(session_id)

        if not session:
            raise ValueError(f'Session does not exist')

        expiry = session['ExpiresAt']

        if datetime.now(timezone.utc) > expiry:
            return None
        else:
            return session['UserID']

    except Exception as e:
        print(f'Unable to verify session_id, error \n{e}\n')
        raise


async def sign_up(username,password):
    try:

        user_id = await get_user(username)

        if user_id:
            raise ValueError(f'User already exists, please log in instead\n')

        ph = PasswordHasher()
        hashed_password = ph.hash(password)
        await create_user(username, hashed_password)
        print(f'User {username} created\n')

    except Exception as e:
        print(f'Unexpected error occured : \n{e}\n') 
        raise


async def login(username,password):
    try:
        user_id = await get_user(username)
        if user_id is None:
            raise ValueError(f'User does not exist\n')

        hashed_password = await get_password(username)
        if hashed_password is None:
            raise ValueError(f'User does not have password\n')      

        try:
            ph = PasswordHasher()
            ph.verify(hashed_password, password)
        except VerifyMismatchError:
            raise ValueError(f'Authentication failed: Invalid username or password.\n')

        session_id = str(uuid4())
        await create_session(session_id,user_id)

        return session_id

    except Exception as e:
        print(f'Unable to login user, error \n{e}\n\n')
        raise