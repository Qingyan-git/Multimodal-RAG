import uuid
import os
import asyncio

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import PointStruct, Distance, VectorParams, models, SparseVector
from scripts.config import settings



# Creation functions

async def get_qdrant_client():
    """
    Returns a qdrant_client object
    """
    try:
        qdrant_cluster_endpoint = settings.qdrant_cluster_endpoint
        qdrant_api_key = settings.qdrant_api_key
        client = AsyncQdrantClient(
            url=qdrant_cluster_endpoint,
            api_key=qdrant_api_key.get_secret_value(),
            timeout=180
        )
        return client

    except Exception as e:
        print(f'Failed to create qdrant client, error {e}\n\n')
        raise


async def create_collection():

    try:
        client = await get_qdrant_client()
        name = settings.qdrant_collection_name

        if await client.collection_exists(name):
            print(f'Collection already exists. Deleting and recreating for clean schema switch...\n\n')
            await client.delete_collection(collection_name=name)

        await client.create_collection(
            collection_name=name,
            vectors_config={
                "coarse_embedding": models.VectorParams(
                    size=128,
                    distance=models.Distance.COSINE
                ),

                "page_embeddings": models.VectorParams(
                    size=128,
                    distance=models.Distance.DOT,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    ),
                    hnsw_config=models.HnswConfigDiff(m=0)
                ),
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
                filter=models.Filter()
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
        name = settings.qdrant_collection_name
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


async def similarity_search(splade_vector, coarse_vector, page_embeddings):

    try :
        client = await get_qdrant_client()
        name = settings.qdrant_collection_name

        qdrant_vector = SparseVector(
            indices=splade_vector['indices'],
            values=splade_vector['values']
        )

        response = await client.query_points(
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
            limit=20,

            # search_params=models.SearchParams(
            #     exact=True
            # )
        )
        
        retrieved = {}
        for point in response.points:
            page_id = point.payload.get("page_id")
            score = point.score
            retrieved[page_id] = score

        return retrieved

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

