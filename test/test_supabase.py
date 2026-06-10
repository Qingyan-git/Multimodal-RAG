import os
from pathlib import Path
import asyncio
from datetime import datetime, timezone, timedelta

from supabase import acreate_client, AsyncClient
from scripts.config import settings


# lfaPF9uigK7NFiLJ

async def get_connection():
    try:

        url = 'https://gfczuohhncdxboyfsmpi.supabase.co'
        key = ''
        client = await acreate_client(url, key)

        return client
    
    except Exception as e:
        print(f'Unable to get supabase connection, error {e}\n\n')
        raise


async def get_session(session_id):
    try:
        client = await get_connection()
        response = await (client
            .table('Sessions')
            .select('ExpiresAt, UserID')
            .eq('SessionID', session_id)
            .limit(1)
            .execute()
        )
        
        if response.data:
            return response.data
        return []

    except Exception as e:
        print(f'Unable to get session, error \n{e}\n')
        raise


async def create_session(session_id, user_id, delta=5):
    try:
        client = await get_connection()

        now = datetime.now(timezone.utc)
        created_at = now.isoformat()
        expires_at = (now + timedelta(minutes=delta)).isoformat()

        await (client
            .table('Sessions')
            .insert({
                'SessionID': session_id, 
                'UserID': user_id, 
                'CreatedAt': created_at, 
                'ExpiresAt': expires_at
            })
            .execute()
        )

    except Exception as e:
        print(f'Unable to create session, error \n{e}\n\n')
        raise


async def get_password(username):
    try:
        client = await get_connection()
        response = await (client
            .table('User')
            .select('Password')
            .eq('Username', username)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]['Password']
        return None

    except Exception as e:
        print(f'Unable to get password of user {username}, error \n{e}\n\n')
        raise


async def get_user(name):
    try:
        client = await get_connection()
        response = await (client
            .table('User')
            .select('UserID')
            .eq('Username', name)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]['UserID']
        return None

    except Exception as e:
        print(f'Unable to retrieve user {name} from supabase, error \n{e}\n')
        raise


async def create_user(name, password):
    try:
        client = await get_connection()
        await (client
            .table('User')
            .upsert({'Username': name, 'Password': password},
                on_conflict='Username',
                ignore_duplicates=True
            )
            .execute()
        )

    except Exception as e:
        print(f'Unable to create user {name} into supabase, error \n{e}\n\n')
        raise


async def get_chats(user_id):
    try:
        client = await get_connection()
        response = await (client
            .table('Chats')
            .select('Name, ChatID')
            .eq('UserID', user_id)
            .execute()
        )

        if response.data:
            return response.data
        return []

    except Exception as e:
        print(f'Unable to get chats for user {user_id}, error \n{e}\n')
        raise


async def create_chat(chat_name, user_id):
    try:
        client = await get_connection()
        response = await (client
            .table('Chats')
            .insert({
                'UserID': user_id,
                'Name': chat_name,
            })
            .execute()
        )

        if response.data:
            chat_id = response.data[0]['ChatID']
            return chat_id
        return None

    except Exception as e:
        print(f'Unable to create chat {chat_name}, error \n{e}\n\n')
        raise


async def get_chatitems(user_id, chat_id):
    try:
        client = await get_connection()
        response = await (client
            .table("ChatItem")
            .select("*, Chats!inner(UserID)")
            .eq("ChatID", chat_id)
            .eq("Chats.UserID", user_id)
            .order("ChatItemID", desc=False)
            .execute()
        )

        if response.data:
            return response.data
        return []

    except Exception as e:
        print(f'Unable to get chatitems for chat {chat_id}, error \n{e}\n')
        raise


async def create_chatitem(question, response, chat_id):
    try:
        client = await get_connection()
        await (client
            .table('ChatItem')
            .insert({'ChatID': chat_id, 'Question': question, 'Response': response})
            .execute()
        )

    except Exception as e:
        print(f'Unable to create chat item for question {question}, error \n{e}\n')
        raise


async def insert_pdf(name, path):
    try:
        client = await get_connection()
        await (client
            .table("pdfs")
            .upsert(
                {'name': name, 'path': str(path)},
                on_conflict="path",
                ignore_duplicates=False,
                returning='minimal'
            )
            .execute()
        )

    except Exception as e:
        print(f'Unable to insert pdf {name} into supabase, error {e}\n\n')
        raise


async def insert_page(filename, markdown, page_no):
    """
    Inserts or updates page text context, resolving the parent pdf reference 
    and outputting the relational sequential primary key id.
    """
    try:
        client = await get_connection()

        # Step 1: Look up parent mapping ID from the database catalog
        pdf_lookup = await (client
            .table('pdfs')
            .select('pdf_id')
            .eq('name', filename)
            .limit(1)
            .single()
            .execute()
        )
        pdf_id = pdf_lookup.data['pdf_id']

        response = await (client
            .table("pages")
            .upsert(
                {'pdf_id': pdf_id, 'markdown': markdown, 'num': page_no},
                ignore_duplicates=False,
            )
            .execute()
        )

        if response.data:
            page_id = response.data[0]['page_id']
            return page_id
            
        return None

    except Exception as e:
        print(f'Unable to insert page {page_no} from {filename} into supabase, error {e}\n\n')
        raise


async def retrieve_pdf_info(page_id):
    try:
        client = await get_connection()
        response = await (client
            .table("pages")
            .select("page_id, num, pdfs(name, path)")
            .eq("page_id", page_id)
            .limit(1)
            .single()
            .execute()
        )

        page_no = int(response.data['num'])
        pdf_name = response.data['pdfs']['name']
        pdf_path = response.data['pdfs']['path']

        return page_no, pdf_name, pdf_path

    except Exception as e:
        print(f'Unable to retrieve answer pdf for pages {page_id}, error \n{e}\n\n')
        raise


async def retrieve_markdowns(page_ids):
    try:
        client = await get_connection()
        response = await (client
            .table('pages')
            .select('page_id,markdown')
            .in_('page_id', page_ids)
            .execute()
        )

        markdowns = {}
        for row in response.data:
            page_id = int(row['page_id'])
            markdown = row['markdown']
            markdowns[page_id] = markdown

        return markdowns

    except Exception as e:
        print(f'Unable to retrieve answer files for pages {page_ids}, error \n{e}\n\n')
        raise


async def get_path_from_pdf_name(pdf_name):
    try:
        client = await get_connection()
        response = await (client
            .table('pdfs')
            .select('path')
            .eq('name', pdf_name)
            .limit(1)
            .single()
            .execute()
        )

        path = response.data['path']
        return path

    except Exception as e:
        print(f'Unable to retrieve path from pdf {pdf_name}, error : \n{e}\n\n')
        return None