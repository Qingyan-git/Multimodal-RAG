import os
from pathlib import Path
import asyncio
from datetime import datetime, timezone, timedelta

from supabase import acreate_client, AsyncClient
from scripts.config import settings



async def get_connection():
    try:
        url = settings.supabase_url
        key = settings.supabase_key.get_secret_value()
        client = await acreate_client(url, key)
        return client
    except Exception as e:
        print(f'Unable to get supabase connection, error {e}\n\n')
        raise


async def get_session(session_id):
    try:
        client = await get_connection()
        response = await (client
            .table('sessions')
            .select('expiresat, userid')
            .eq('sessionid', session_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
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
            .table('sessions')
            .insert({
                'sessionid': session_id,
                'userid': user_id, 
                'createdat': created_at, 
                'expiresat': expires_at
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
            .select('password')
            .eq('username', username)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]['password']
        return ""
    except Exception as e:
        print(f'Unable to get password of user {username}, error \n{e}\n\n')
        raise


async def get_user(name):
    try:
        client = await get_connection()
        response = await (client
            .table('User')
            .select('userid')
            .eq('username', name)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]['userid']
        return None
    except Exception as e:
        print(f'Unable to retrieve user {name} from supabase, error \n{e}\n')
        raise


async def create_user(name, password):
    try:
        client = await get_connection()
        await (client
            .table('User')
            .upsert({'username': name, 'password': password},
                on_conflict='username',
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
            .table('chats')
            .select('name, chatid')
            .eq('userid', user_id)
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
            .table('chats')
            .insert({
                'userid': user_id,
                'name': chat_name,
            })
            .execute()
        )
        if response.data:
            chat_id = response.data[0]['chatid']
            return chat_id
        return None
    except Exception as e:
        print(f'Unable to create chat {chat_name}, error \n{e}\n\n')
        raise


async def append_summary(user_id, chat_id, summary):
    try:
        client = await get_connection()
        response = await (client
            .table("chats")
            .select("chatsummary")
            .eq("chatid", chat_id)
            .eq("userid", user_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            print(f"Error: Chat {chat_id} for User {user_id} does not exist.\n")
            return False

        old_summary = response.data[0]['chatsummary']
        new_summary = f"{old_summary}\n{summary}" if old_summary else summary

        await (client
            .table("chats")
            .update({"chatsummary": new_summary})
            .eq("chatid", chat_id)
            .eq("userid", user_id)
            .execute()
        )
        return True
    except Exception as e:
        print(f'Unable to append summary to chat, error \n{e}\n')
        raise


async def get_non_cached(user_id, chat_id):
    try:
        client = await get_connection()
        response = await (client
            .table("chatitem")
            .select("*, chats!inner(userid)")
            .eq("chatid", chat_id)
            .eq("chats.userid", user_id)
            .eq("cached", False)
            .order("chatitemid", desc=False)
            .execute()
        )
        if response.data:
            return response.data
        return []
    except Exception as e:
        print(f'Unable to get non cached chats, error \n{e}\n')
        return []


async def convert_cached(chatitem_ids):
    try:
        client = await get_connection()
        await (client
            .table('chatitem')
            .update({'cached': True})
            .in_('chatitemid', chatitem_ids)
            .execute()
        )
    except Exception as e:
        print(f'Unable to convert chats to cache, error \n{e}\n')
        raise


async def get_chat_history(user_id, chat_id):
    try:
        client = await get_connection()
        response = await (client
            .table("chats")
            .select("chatsummary")
            .eq("chatid", chat_id)
            .eq("userid", user_id)
            .limit(1)
            .execute()
        )

        chat_summary = response.data[0]['chatsummary'] if response.data else None

        response = await (client
            .table('chatitem')
            .select('question', 'response', 'chats!inner(userid)')
            .eq('chatid', chat_id)
            .eq('cached', False)
            .eq("chats.userid", user_id)
            .order('createdat', desc=False)
            .execute()
        )

        if response.data:
            uncached_chats = [{'question': item['question'], 'response': item['response']} for item in response.data]
        else:
            uncached_chats = None

        return chat_summary, uncached_chats
    except Exception as e:
        print(f'Unable to get chat history, error \n{e}\n')
        raise


async def get_chatitems(user_id, chat_id):
    try:
        client = await get_connection()
        response = await (client
            .table("chatitem")
            .select("*, chats!inner(userid)")
            .eq("chatid", chat_id)
            .eq("chats.userid", user_id)
            .order("chatitemid", desc=False)
            .execute()
        )
        if response.data:
            return response.data
        return []
    except Exception as e:
        print(f'Unable to get chatitems for chat {chat_id}, error \n{e}\n')
        raise


async def create_chatitem(question, response, user_id, chat_id):
    try:
        client = await get_connection()
        chat_verification = await (client
            .table("chats")
            .select("userid")
            .eq("chatid", chat_id)
            .eq("userid", user_id)
            .limit(1)
            .execute()
        )

        if not chat_verification.data:
            print(f"Unauthorized attempt by User {user_id} to access Chat {chat_id}")
            return

        await (client
            .table('chatitem')
            .insert({'chatid': chat_id, 'question': question, 'response': response})
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
            )
            .execute()
        )
    except Exception as e:
        print(f'Unable to insert pdf {name} into supabase, error {e}\n\n')
        raise


async def insert_page(filename, markdown, page_no, page_image):
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

        bucket_name = settings.supabase_bucket_name
        storage_path = f"{filename}/page_{page_no}.jpeg"

        await (client
            .storage
            .from_(bucket_name)
            .upload(
                file=page_image,
                path=storage_path,
                file_options={"cache-control": "3600", "upsert": "true"}
            )
        )

        response = await (client
            .table("pages")
            .upsert(
                {'pdf_id': pdf_id, 'markdown': markdown, 'num': page_no, 'bucket_path' : storage_path},
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


async def retrieve_source_from_pageid(page_id):
    try:
        client = await get_connection()

        response = await (client
        .table("pages")
        .select(
            "num",
            "bucket_path",
            "pdfs(name)"
        )
        .eq("page_id", page_id)
        .limit(1)
        .execute())

        if response.data:
            info = response.data[0]
            pdf_name = info['pdfs']['name']
            page_no = info['num']
            bucket_path = info['bucket_path']

            bucket_name = settings.supabase_bucket_name
            page_image = await (client
                .storage
                .from_(bucket_name)
                .download(bucket_path)
            )

            return pdf_name, page_no, page_image
        else:
            return None

    except Exception as e:
        print(f'Unable to retrieve page data, error \n{e}\n')


async def retrieve_source_from_pdf_name(pdf_name, page_no):
    try:
        client = await get_connection()

        response = await (client
            .table("pages")
            .select("bucket_path, pdfs!inner(name)")
            .eq("num", page_no)
            .eq("pdfs.name", pdf_name)
            .limit(1)
            .execute()
        )

        if response.data:
            info = response.data[0]
            bucket_path = info['bucket_path']
            bucket_name = settings.supabase_bucket_name
            page_image = await (client
                .storage
                .from_(bucket_name)
                .download(bucket_path)
            )

            return page_image
        else:
            return None

    except Exception as e:
        print(f'Unable to retrieve page data, error \n{e}\n')
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