import os
from pathlib import Path
import asyncio
from datetime import datetime, timezone, timedelta

from supabase import acreate_client, AsyncClient
from scripts.config import settings

_client = None
_lock = asyncio.Lock()

async def get_connection():
    
    try:
        global _client
        if _client is not None:
            return _client

        async with _lock:
            if _client is None:
                url = settings.supabase_url
                key = settings.supabase_key.get_secret_value()
                _client = await acreate_client(url, key)

        return _client
    
    except Exception as e:
        print(f'Unable to get supabase connection, error {e}\n\n')
        raise


async def create_session(session_id,user_id):

    try:
        client = await get_connection()

        created_at = datetime.now(timezone.utc).isoformat()
        expires_at = created_at + timedelta(minutes=5)

        await (client
            .table('Sessions')
            .insert({
                'SessionID' : session_id, 
                'UserID' : user_id, 
                'CreatedAt' : created_at, 
                'ExpiresAt' : expires_at
                })
            .execute()
        )

    except Exception as e:
        print(f'Unable to create session, error \n{e}\n\n')


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


async def get_user(name):

    try:
        client = await get_connection()

        response = await(client
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


async def create_user(name,password):
    
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


async def get_chats(user_id):

    try:
        client = await get_connection()

        response = await (client
            .table('Chats')
            .select('Name, ChatID')
            .eq('UserID',user_id)
            .execute()
        )

        if response.data:
            return response.data
        return []

    except Exception as e:
        print(f'Unable to get chats for user {user_id}, error \n{e}\n')


async def create_chat(chat_name,user_id):

    try:
        client = await get_connection()

        response = await (client
            .table('Chats')
            .insert(
                {
                    'UserID' : user_id,
                    'Name' : chat_name,
                }
            )
            .execute()
        )

        if response.data:
            chat_id = response.data[0]['ChatID']
            return chat_id
        return None

    except Exception as e:
        print(f'Unable to create chat {chat_name}, error \n{e}\n\n')
        raise


async def get_chatitems(chat_id):

    try:
        client = get_connection()

        response = await (client
            .table('ChatItem')
            .select('*')
            .eq('ChatID', chat_id)
            .order('ChatItemID', desc=False)
            .execute()
        )

        if response.data:
            return response.data
        return []

    except Exception as e:
        print(f'Unable to get chatitems for chat {chat_id}, error \n{e}\n')


async def create_chatitem(question,response,chat_id):

    try:
        client = await get_connection()

        await (client
            .table('ChatItem')
            .insert({'Question' : question, 'Response' : response})
            .execute()
        )

    except Exception as e:
        print(f'Unable to create chat item for question {question}, error \n{e}\n')


async def insert_pdf(name,path):

    try:
        client = await get_connection()

        await (client
            .table("pdfs")
            .upsert(
                {'name' : name, 'path' : str(path)},
                on_conflict="path",
                ignore_duplicates=False,
                returning='minimal'
            )
            .execute()
        )

    except Exception as e:
        print(f'Unable to insert pdf {name} into supabase, error {e}\n\n')
        raise


async def insert_page(filename,markdown,page_no):

    try:
        client = await get_connection()

        response = await (client
            .table('pdfs')
            .select('pdf_id')
            .eq('name',filename)
            .limit(1)
            .single()
            .execute()
        )

        pdf_id = response.data['pdf_id']

        response = await (client
            .table("pages")
            .upsert(
                {'pdf_id':pdf_id,'markdown':markdown,'num':page_no},
                ignore_duplicates=False,
            )
            .execute()
        )

        if response.data:
            page_id = response.data[0]['page_id']
            
            return page_id

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

        page_no = response.data['num']
        pdf_name = response.data['pdfs']['name']
        pdf_path = response.data['pdfs']['path']

        return page_no,pdf_name,pdf_path

    except Exception as e:
        print(f'Unable to retrieve answer pdf for pages {page_id}, error \n{e}\n\n')
        raise


async def retrieve_markdowns(page_ids):

    try:
        client = await get_connection()
        response = await (client
            .table('pages')
            .select('page_id,markdown')
            .in_('page_id',page_ids)
            .execute()
        )

        markdowns = {}
        for row in response.data:
            page_id = row['page_id']
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
            .eq('name',pdf_name)
            .limit(1)
            .single()
            .execute()
        )

        path = response.data['path']

        return path

    except Exception as e:
        print(f'Unable to retrieve path from pdf {pdf_name}, error : \n{e}\n\n')



if __name__ == "__main__":

    async def main():
        sure = input('Are you sure? Enter Y to continue : ')
        
        if sure == 'Y':
            await delete_rows()

        else:
            print('Aborted\n\n')

    asyncio.run(main())