
import asyncio
from uuid import uuid4 
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timezone

from scripts.supabase_setup import create_user, get_user, get_password, get_session, create_session, get_chatitems, append_summary
from scripts.config import settings


async def verify_session(session_id):
    try:
        response = await get_session(session_id)
        if not response:
            raise ValueError('Session does not exist')

        expiry_str = response['expiresat'] 
        expiry = datetime.fromisoformat(expiry_str)

        if datetime.now(timezone.utc) > expiry:
            raise ValuerError(f"Session has expired, please log in again")
            return None
        else:
            return response['userid']

    except Exception as e:
        print(f'Unable to verify session_id, error \n{e}\n')
        return None


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
        if not hashed_password:
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


if __name__ == "__main__":

    async def main():

        user1 = 'admin'
        pass1 = 'admin'

        await sign_up(user1,pass1)

        session_id = await login(user1,pass1)
        print(f'session_id : {session_id}\n')

        session_verification = await verify_session(session_id)
        print(f'session_verification : {session_verification}\n')

    asyncio.run(main())