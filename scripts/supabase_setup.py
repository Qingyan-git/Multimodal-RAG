import os
from pathlib import Path
import asyncio

from supabase import acreate_client, AsyncClient


_client = None
_lock = asyncio.Lock()

async def get_connection():
    
    try:
        global _client
        if _client is not None:
            return _client

        async with _lock:
            if _client is None:
                url = os.getenv('supabase_url')
                key = os.getenv('supabase_api_key')
                _client = await acreate_client(url, key)

        return _client
    
    except Exception as e:
        print(f'Unable to get supabase connection, error {e}\n\n')
        raise


async def delete_rows():

    try:
        client = await get_connection()

        print("Initiating database purge...\n")

        # 1. Define both tasks as concurrent coroutines
        # Changed filter to .gte() which plays better with primary key index scanning
        task_pages = client.table('pages').delete(count="exact").gte('page_id', 0).execute()
        task_pdfs = client.table('pdfs').delete(count="exact").gte('pdf_id', 0).execute()

        # 2. Fire both requests simultaneously over the network
        result_pages, result_pdfs = await asyncio.gather(task_pages, task_pdfs)

        # 3. Extract the counts safely from the concurrent results
        print(f'{result_pages.count} pages deleted\n')
        print(f'{result_pdfs.count} pdfs deleted\n\n')

    except Exception as e:
        print(f'Unable to delete rows in supabase db, error {e}\n\n')
        raise


async def insert_pdf(name,path):

    try:
        client = await get_connection()

        response = await (client
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


async def retrieve_pdf_path(filename):

    try:
        client = await get_connection()

        response = await (client
            .table('pdfs')
            .select('path')
            .eq('name',filename)
            .limit(1)
            .single()
            .execute()
        )

        path = response.data['path']

        return path

    except Exception as e:
        print(f'Unable to retrieve answer pages for files {file in filenames}, error \n{e}\n\n')
        raise


async def retrieve_files(page_ids):

    try:
        client = await get_connection()

        response = await (client
            .table('pages')
            .select('pdfs(name),num')
            .in_('page_id',page_ids)
            .execute()
        )

        sources = []
        for row in response.data:
            item = {
                'name' : row['pdfs']['name'],
                'page_no' : row['num']
            }
            sources.append(item)

        return sources

    except Exception as e:
        print(f'Unable to retrieve answer files for pages {page_id in page_ids}, error \n{e}\n\n')
        raise




if __name__ == "__main__":

    async def main():
        sure = input('Are you sure? Enter Y to continue : ')
        
        if sure == 'Y':
            await delete_rows()

        else:
            print('Aborted\n\n')

    asyncio.run(main())