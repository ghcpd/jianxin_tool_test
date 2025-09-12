import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from pathlib import Path

# Optional Azure SDK imports with fallbacks for testing
try:
    from azure.identity import DefaultAzureCredential
    from azure.containerregistry import ContainerRegistryClient
except Exception:
    DefaultAzureCredential = object
    ContainerRegistryClient = object

# Optional Azure SDK async imports with fallbacks for testing
try:
    from azure.identity.aio import DefaultAzureCredential as AioDefaultAzureCredential
    from azure.containerregistry.aio import ContainerRegistryClient as AioContainerRegistryClient
except Exception:
    AioDefaultAzureCredential = object
    AioContainerRegistryClient = object

load_dotenv()

def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def list_acr_repositories(acr_name: str=None, save_path: str=None):
    try:
        # Load environment variables
        acr_name = acr_name or os.getenv("ACR_NAME", "acvdpwu2p001acr")
        acr_url = f"https://{acr_name}.azurecr.io"

        # Authenticate using DefaultAzureCredential
        credential = DefaultAzureCredential()

        # Create a ContainerRegistryClient
        client = ContainerRegistryClient(endpoint=acr_url, credential=credential, audience="https://management.azure.com")

        # List repositories in the ACR
        repositories = client.list_repository_names()
        properties = []
        for repo in repositories:
            # print(f"Repository: {repo}")
            properties.append([repo])
        properties = pd.DataFrame(properties, columns=["repository"])
        if save_path:
            save_to_csv(properties, save_path)
        return properties
    except Exception as e:
        print(f"An error occurred: {e}")

def get_acr_repository_properties(repository_name: str, acr_name: str=None, save_path: str=None, verbose: bool=True):
    try:
        # Load environment variables
        acr_name = acr_name or os.getenv("ACR_NAME", "acvdpwu2p001acr")
        acr_url = f"https://{acr_name}.azurecr.io"

        # Authenticate using DefaultAzureCredential
        credential = DefaultAzureCredential()

        # Create a ContainerRegistryClient
        client = ContainerRegistryClient(endpoint=acr_url, credential=credential, audience="https://management.azure.com")

        # Get tags of the specified repository
        tags = client.list_tag_properties(repository_name)
        if verbose:
            print(f"Tags in repository '{repository_name}':")
        _tags = []
        for tag in tags:
            if verbose:
                print(f"- {tag.name}")
            _tags.append([repository_name, tag.name, tag.created_on, tag.last_updated_on, tag.digest])
        _tags = pd.DataFrame(_tags, columns=["repository", "tag", "created_on", "last_updated_on", "digest"])
        if save_path:
            save_to_csv(_tags, save_path)
        return _tags
    except Exception as e:
        print(f"An error occurred: {e}")

# New: multithreaded retrieval of tags for multiple repositories
def get_tags_for_repositories(repo_names, acr_name: str=None, save_path: str=None, max_workers: int=5, verbose: bool=False):
    try:
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(get_acr_repository_properties, repo, acr_name, None, verbose): repo for repo in repo_names}
            for future in as_completed(futures):
                df = future.result()
                if isinstance(df, pd.DataFrame) and not df.empty:
                    results.append(df)
        combined = pd.concat(results, ignore_index=True) if results else pd.DataFrame(columns=["repository", "tag", "created_on", "last_updated_on", "digest"])
        if save_path:
            save_to_csv(combined, save_path)
        return combined
    except Exception as e:
        print(f"An error occurred: {e}")

# Async versions of helper functions
async def async_list_acr_repositories(acr_name: str=None, save_path: str=None):
    try:
        acr_name = acr_name or os.getenv("ACR_NAME", "acvdpwu2p001acr")
        acr_url = f"https://{acr_name}.azurecr.io"
        credential = AioDefaultAzureCredential()
        client = AioContainerRegistryClient(endpoint=acr_url, credential=credential, audience="https://management.azure.com")
        properties = []
        async for repo in client.list_repository_names():
            properties.append([repo])
        properties = pd.DataFrame(properties, columns=["repository"])
        if save_path:
            save_to_csv(properties, save_path)
        return properties
    except Exception as e:
        print(f"An error occurred: {e}")

async def async_get_acr_repository_properties(repository_name: str, acr_name: str=None, save_path: str=None, verbose: bool=True):
    try:
        acr_name = acr_name or os.getenv("ACR_NAME", "acvdpwu2p001acr")
        acr_url = f"https://{acr_name}.azurecr.io"
        credential = AioDefaultAzureCredential()
        client = AioContainerRegistryClient(endpoint=acr_url, credential=credential, audience="https://management.azure.com")
        if verbose:
            print(f"Tags in repository '{repository_name}':")
        _tags = []
        async for tag in client.list_tag_properties(repository_name):
            if verbose:
                print(f"- {tag.name}")
            _tags.append([repository_name, tag.name, tag.created_on, tag.last_updated_on, tag.digest])
        _tags = pd.DataFrame(_tags, columns=["repository", "tag", "created_on", "last_updated_on", "digest"])
        if save_path:
            save_to_csv(_tags, save_path)
        return _tags
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    list_acr_repositories(save_path="data/acr_repositories.csv")
    # get_acr_repository_properties("abanteai__apples-to-models-108")