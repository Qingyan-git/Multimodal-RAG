import uuid
import os
import asyncio

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import PointStruct, Distance, VectorParams, models, SparseVector
from scripts.config import settings



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
            print(f'Collection already exists. Deleting and recreating collection...\n\n')
            await client.delete_collection(collection_name=name)

        # Re-create collection without coarse_embedding
        await client.create_collection(
            collection_name=name,
            vectors_config={
                "page_embeddings": models.VectorParams(
                    size=128,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM
                    )
                ),
            },
            sparse_vectors_config={
                "splade_vector": models.SparseVectorParams(
                    modifier=models.Modifier.IDF
                )
            },
            # On-disk HNSW ensures your multi-vector index doesn't explode your RAM usage
            hnsw_config=models.HnswConfigDiff(on_disk=True)
        )

        print(f'Collection {name} successfully created.\n\n')

    except Exception as e:
        print(f'Unable to create collection in qdrant, error \n{e}\n\n')
        raise


def format_point(embedding):
    """
    Expects embedding dict containing: 'page_id', 'sparse', and 'multi'
    """

    vector = models.PointStruct(
        id=str(uuid.uuid4()),
        vector={
            "page_embeddings": embedding['multi'],
            "splade_vector": models.SparseVector(
                indices=embedding['sparse']['indices'],
                values=embedding['sparse']['values']
            )
        },
        payload={
            "page_id": embedding['page_id']
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


async def similarity_search(splade_vector, page_embeddings):
    try:
        client = await get_qdrant_client()
        name = settings.qdrant_collection_name

        qdrant_sparse = models.SparseVector(
            indices=splade_vector['indices'],
            values=splade_vector['values']
        )

        # response = await client.query_points(
        #     collection_name=name,
        #     prefetch=[
        #         models.Prefetch(query=qdrant_sparse, using="splade_vector", limit=50),
        #         models.Prefetch(query=page_embeddings, using="page_embeddings", limit=50),
        #     ],
        #     query=models.FusionQuery(fusion=models.Fusion.RRF),
        #     limit=20,
        # )

        response = await client.query_points(
            collection_name=name,
            prefetch=[
                models.Prefetch(
                    query=qdrant_sparse,     # The sparse vector
                    using="splade_vector",   # The sparse vector namespace
                    limit=200
                )
            ],
            query=page_embeddings,           # The dense vector re-ranks the top 50
            using="page_embeddings",         # The dense vector namespace
            limit=20,                        # Returns final top 20
        )

        # response = await client.query_points(
        #     collection_name=name,
        #     query=page_embeddings,
        #     using="page_embeddings",
        #     limit=20,
        # )
        
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
        sure = input('Are you sure? Enter Y to rebuild the collection : ')
        if sure == 'Y':
            await create_collection()
        else:
            print('Aborted\n\n')

    asyncio.run(main())