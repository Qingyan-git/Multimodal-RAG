from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import PointStruct, Distance, VectorParams, models
import uuid
import os
import asyncio



_client = None
_lock = asyncio.Lock()

# Creation functions

async def get_qdrant_client():
    """
    Returns a qdrant_client object
    """
    try:
        global _client
        if _client is not None:
            return _client

        async with _lock:
            if _client is None:
                qdrant_cluster_endpoint = os.getenv('qdrant_cluster_endpoint')
                qdrant_api_key = os.getenv('qdrant_api_key')
                _client = AsyncQdrantClient(
                    url=qdrant_cluster_endpoint,
                    api_key=qdrant_api_key,
                    timeout=180
                )

        return _client

    except Exception as e:
        print(f'Failed to create qdrant client, error {e}\n\n')
        raise


async def create_collection():

    try:
        client = await get_qdrant_client()
        name = os.getenv('qdrant_collection_name')

        if await client.collection_exists(name):
            print(f'Collection already exists, clearing points from it now\n\n')
            await clear_points(name)

        else:
            await client.create_collection(
                collection_name=name,
                vectors_config={
                    "coarse_embedding": models.VectorParams(
                        size=128,
                        distance=models.Distance.COSINE
                    ),

                    "page_embeddings": models.VectorParams(
                        size=128,
                        distance=models.Distance.COSINE,
                        multivector_config=models.MultiVectorConfig(
                            comparator=models.MultiVectorComparator.MAX_SIM
                        )
                    )
                },

                sparse_vectors_config={
                    "splade_vector": models.SparseVectorParams(
                        modifier=models.Modifier.IDF
                    )
                },
                
                hnsw_config=models.HnswConfigDiff(on_disk=True)
            )

            print(f'Collection created\n\n')

    except Exception as e:
        print(f'Unable to create collection in qdrant, error \n{e}\n\n')
        raise


async def clear_points(name):

    try:
        client = await get_qdrant_client()
        await client.delete(
            collection_name=name,
            points_selector=models.FilterSelector(
                filter=models.Filter() # Explicit structural wildcard filter match
            )
        )

        print(f'All points deleted from collection {name}\n\n')

    except Exception as e:
        print(f'Unable to delete all points from collection {name} in qdrant, error \n{e}\n\n')
        raise



# Execution functions


def format_point(embedding):

    vector = models.PointStruct(
        id=str(uuid.uuid4()),
        vector={
            "coarse_embedding": embedding['coarse'],
            "page_embeddings": embedding['multi'],

            "splade_vector": models.SparseVector(
                indices=embedding['sparse']['indices'],
                values=embedding['sparse']['values']
            )
        },
        payload={
            "page_id" : embedding['page_id']
        }
    )

    return vector


async def upload_points(points, batch_size=16):

    try:
        name = os.getenv('qdrant_collection_name')
        client = await get_qdrant_client()
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            await client.upsert(
                collection_name=name,
                points=batch
            )

    except Exception as e:
        print(f'Unable to upload points to collection {name} to qdrant, error \n{e}\n\n')
        raise


async def similarity_search(splade_vector, coarse_vector, query_embeddings):

    try :
        client = await get_qdrant_client()
        name = os.getenv('qdrant_collection_name')

        response = client.query_points(
            collection_name=name,

            prefetch=[
                models.Prefetch(
                    query=coarse_vector,
                    using="coarse_embedding",
                    limit=50
                ),
                models.Prefetch(
                    query=qdrant_vector,
                    using="splade_vector",
                    limit=50
                ),
            ],
            query=page_embeddings,
            using="page_embeddings",
            limit=20
        )

        pages = {}
        for point in response.points:
            score = point.score
            page_id = point.payload.get('page_id')
            pages[page_id] = {'image_score' : score}

        return pages

    except Exception as e:
        print(f'Unable to perform similarity search on qdrant, error \n{e}\n\n')
        raise



if __name__ == '__main__':

    async def main():
        sure = input('Are you sure? Enter Y to continue : ')
        
        if sure == 'Y':
            await create_collection()
        else:
            print('Aborted\n\n')

    asyncio.run(main())

