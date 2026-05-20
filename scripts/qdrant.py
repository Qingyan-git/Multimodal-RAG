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


def create_collection():

    try:
        client = get_qdrant_client()
        name = os.getenv('collection_name')

        if client.collection_exists(name):
            print(f'Collection already exists, clearing points from it now\n\n')
            clear_points(name)

        else:
            client.create_collection(
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
        print(f'Unable to create collection in qdrant, error {e}\n\n')


def clear_points(name):

    try:
        client.delete(
            collection_name=name,
            points_selector=models.FilterSelector(
                filter=models.Filter() # Explicit structural wildcard filter match
            )
        )

        print(f'All points deleted from collection {name}\n\n')

    except Exception as e:
        print(f'Unable to delete all points from collection {name} in qdrant, error {e}\n\n')



# Execution functions



if __name__ == '__main__':

    recreate = 1
    sure = input('Are you sure? Enter Y to continue : ')
    
    if recreate == 1 and sure == 'Y':
        create_collection()

    else:
        print('Aborted\n\n')

