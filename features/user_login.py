
import asyncio
from uuid import uuid4 
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from scripts.supabase_setup import create_user, get_user, get_password
from scripts.config import settings


async def sign_up(username,password):

    try:
        ph = PasswordHasher()
        hashed_password = ph.hash(password)
        await create_user(username, hashed_password)
        print(f'User {username} created\n')

    except Exception as e:
        print(f'Unexpected error occured : \n{e}\n') 


async def login(username,password):
    
    try:
        user_id = await get_user(username)

        if user_id is not None:
            hashed_password = await get_password(username)

            if hashed_password is not None:
                try:
                    ph = PasswordHasher()
                    ph.verify(hashed_password, password)
                    
                except VerifyMismatchError:
                    raise ValueError(f'Authentication failed: Invalid username or password.\n')

                session_id = str(uuid4())
                await create_session(session_id,user_id)

                cookie = {
                    'session_id' : session_id,
                    'user_id' : user_id,
                    'username' : username
                }

            else:
                raise ValueError(f'User does not have password\n')            
        else:
            raise ValueError(f'User does not exist\n')


    except Exception as e:
        print(f'Unable to login user, error \n{e}\n\n')