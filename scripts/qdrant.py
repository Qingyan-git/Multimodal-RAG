from qdrant_client import QdrantClient, models
from qdrant_client.models import PointStruct, Distance, VectorParams, models

import os



# Creation functions

def get_qdrant_client():
    """
    Returns a qdrant_client object
    """
    try: 

        qdrant_cluster_endpoint = os.getenv('qdrant_cluster_endpoint')
        qdrant_api_key = os.getenv('qdrant_api_key')

        qdrant_client = QdrantClient(
            url=qdrant_cluster_endpoint,
            api_key=qdrant_api_key,
            timeout=120
        )

        return qdrant_client

    except Exception as e:
        print(f'Failed to connect to qdrant using parameters, error {e}\n\n')


def create_text_collection():

    try:
        client = get_qdrant_client()
        name = os.getenv('text_collection_name')

        if client.collection_exists(name):
            print(f'Text collection already exists, clearing points from it now\n\n')
            clear_points(name)

        else:
            client.create_collection(
                collection_name=name,
                vectors_config={
                    'colqwen_coarse' : models.VectorParams(
                        size = 123456789,
                        distance = models.Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    'splade_text' : models.SparseVectorParams(
                        index_value_type=models.SparseIndexValueType.FLOAT32,
                        modifier=models.Modifier.IDF
                    )
                },
                hnsw_config=models.HnswConfigDiff(on_disk=True)
            )

            print(f'Text collection created\n\n')

    except Exception as e:
        print(f'Unable to create text collection in qdrant, error {e}\n\n')


def create_patch_collection():

    try:
        client = get_qdrant_client()
        name = os.getenv('patch_collection_name')

        if client.collection_exists(name):
            print(f'Text collection already exists, clearing points from it now\n\n')
            clear_points(name)

        else:
            client.create_collection(
                collection_name=name,
                vectors_config={
                    'patch' : models.VectorParams(
                        size = 123456789,
                        distance = models.distance.COSINE
                    )
                }
            )

            print(f'Patch collection created\n\n')

    except Exception as e:
        print(f'Unable to create text collection in qdrant, error {e}\n\n')


def clear_points(name):

    try:
        client = get_qdrant_client()
        client.delete(
                collection_name=name,
                points_selector=models.Filter() 
            )

        print(f'All points deleted from collection {name}\n\n')

    except Exception as e:
        print(f'Unable to delete all points from collection {name} in qdrant, error {e}\n\n')



# Execution functions


















def upload_to_qdrant(chunks, dense, sparse, late):

    try : 
        qdrant_client = get_qdrant_client()
        collection_name = os.getenv('qdrant_collection_name')
        
        points=[
            models.PointStruct(
                id=chunk.id,
                vector={
                    # 1. Dense (OpenAI)
                    "dense": dense[i], 
                    
                    # 2. Sparse (BM25/SPLADE) - Using the dict from your SparseEmbedder
                    "sparse": models.SparseVector(
                        indices=sparse[i]["indices"],
                        values=sparse[i]["values"]
                    ),
                    
                    # 3. Multi (ColBERT) - Ensure this is a list of lists (float)
                    "multi": late[i]
                },
                payload=asdict(chunk)
            ) for i, chunk in enumerate(chunks)]

        # 3. Perform the upload
        qdrant_client.upload_points(
            collection_name=collection_name,
            points=points,
            parallel=4,
            batch_size=32,
            wait=True
        )

    except Exception as e:
        print(f'Unable to upload embeddings to qdrant cloud, error {e}\n\n')


def get_similar_chunks(dense,sparse,late,limit1=20,limit2=4,filters=None):

    try:
        collection_name = os.getenv('qdrant_collection_name')
        client = get_qdrant_client()

        prefetch = [
            models.Prefetch(
                query=dense,
                using="dense",
                limit=limit1,
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse["indices"], 
                    values=sparse["values"]
                ),
                using="sparse",
                limit=limit1,
            ),
        ]

        results = client.query_points(
            collection_name=collection_name,
            prefetch=prefetch,
            query=late, 
            using="multi",
            with_payload=True,
            limit=limit2,
            query_filter=filters
        )

        if results:
            similar_chunks = []
            for result in results.points:

                item = {
                    'id' : result.id,
                    'score' : result.score, 
                    'document_name' : result.payload['document_name'], 
                    'context' : result.payload['context'],
                    'content' : result.payload['content'], 
                    'metadata' : result.payload['metadata']
                }

                similar_chunks.append(item)

            similar_chunks.sort(key=lambda item: item['score'], reverse=True)

            return similar_chunks

        else:
            print('No results found for this query.\n\n')
            return []

    except Exception as e:
        print(f'Unable to get similar chunks, error {e}\n\n')
        raise



if __name__ == '__main__':

    recreate = 1
    sure = input('Are you sure? Enter Y to continue : ')
    
    if recreate == 1 and sure == 'Y':
        create_text_collection()
        create_patch_collection()

    else:
        print('Aborted\n\n')

