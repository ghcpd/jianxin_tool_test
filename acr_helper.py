import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.containerregistry import ContainerRegistryClient
import pandas as pd
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from azure.containerregistry.aio import ContainerRegistryClient as ACRAsync
from azure.identity.aio import DefaultAzureCredential as DefaultAzureCredentialAsync

import inspect


# Expose a single aio namespace for easier testing/mocking
class _Aio:
    pass

aio = _Aio()
from azure.containerregistry.aio import ContainerRegistryClient as _ACR
from azure.identity.aio import DefaultAzureCredential as _DefaultAio
aio.ContainerRegistryClient = _ACR
aio.DefaultAzureCredential = _DefaultAio

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



def get_acr_tags_for_repositories(repositories, acr_name: str=None, save_path: str=None, max_workers: int=4, verbose: bool=False):
    cols = ["repository", "tag", "created_on", "last_updated_on", "digest"]
    results = []
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(get_acr_repository_properties, repo, acr_name, None, verbose) for repo in repositories]
            for fut in as_completed(futures):
                try:
                    df = fut.result()
                    if df is not None and not df.empty:
                        results.append(df)
                except Exception as e:
                    print(f"An error occurred: {e}")
        final = pd.concat(results, ignore_index=True) if results else pd.DataFrame(columns=cols)
        if save_path:
            save_to_csv(final, save_path)
        return final
    except Exception as e:
        print(f"An error occurred: {e}")


async def list_acr_repositories_async(acr_name: str=None, save_path: str=None):
    try:
        acr_name = acr_name or os.getenv("ACR_NAME", "acvdpwu2p001acr")
        acr_url = f"https://{acr_name}.azurecr.io"
        credential = aio.DefaultAzureCredential()
        client = aio.ContainerRegistryClient(endpoint=acr_url, credential=credential, audience="https://management.azure.com")
        try:
            repos = []
            iterable = client.list_repository_names()
            if inspect.isawaitable(iterable):
                iterable = await iterable
            async for repo in iterable:
                repos.append([repo])
            df = pd.DataFrame(repos, columns=["repository"]) 
            if save_path:
                save_to_csv(df, save_path)
            return df
        finally:
            closer = getattr(client, "close", None)
            if closer:
                res = closer()
                if inspect.isawaitable(res):
                    await res
    except Exception as e:
        print(f"An error occurred: {e}")


async def get_acr_repository_properties_async(repository_name: str, acr_name: str=None, save_path: str=None, verbose: bool=True):
    try:
        acr_name = acr_name or os.getenv("ACR_NAME", "acvdpwu2p001acr")
        acr_url = f"https://{acr_name}.azurecr.io"
        credential = aio.DefaultAzureCredential()
        client = aio.ContainerRegistryClient(endpoint=acr_url, credential=credential, audience="https://management.azure.com")
        try:
            rows = []
            iterable = client.list_tag_properties(repository_name)
            if inspect.isawaitable(iterable):
                iterable = await iterable
            async for tag in iterable:
                if verbose:
                    print(f"- {tag.name}")
                rows.append([repository_name, tag.name, tag.created_on, tag.last_updated_on, tag.digest])
            df = pd.DataFrame(rows, columns=["repository", "tag", "created_on", "last_updated_on", "digest"]) 
            if save_path:
                save_to_csv(df, save_path)
            return df
        finally:
            closer = getattr(client, "close", None)
            if closer:
                res = closer()
                if inspect.isawaitable(res):
                    await res
    except Exception as e:
        print(f"An error occurred: {e}")


async def get_acr_tags_for_repositories_async(repositories, acr_name: str=None, save_path: str=None, verbose: bool=False):
    cols = ["repository", "tag", "created_on", "last_updated_on", "digest"]
    try:
        tasks = [get_acr_repository_properties_async(repo, acr_name, None, verbose) for repo in repositories]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        dfs = [r for r in results if isinstance(r, pd.DataFrame) and not r.empty]
        final = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame(columns=cols)
        if save_path:
            save_to_csv(final, save_path)
        return final
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    list_acr_repositories(save_path="data/acr_repositories.csv")
    # get_acr_repository_properties("abanteai__apples-to-models-108")