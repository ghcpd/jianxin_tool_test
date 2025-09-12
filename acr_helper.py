import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.containerregistry import ContainerRegistryClient
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
import asyncio

load_dotenv()


def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")


def list_acr_repositories(acr_name: str = None, save_path: str = None):
    try:
        # Load environment variables
        acr_name = acr_name or os.getenv("ACR_NAME", "acvdpwu2p001acr")
        acr_url = f"https://{acr_name}.azurecr.io"

        # Authenticate using DefaultAzureCredential
        credential = DefaultAzureCredential()

        # Create a ContainerRegistryClient
        client = ContainerRegistryClient(
            endpoint=acr_url, credential=credential, audience="https://management.azure.com"
        )

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


def get_acr_repository_properties(
    repository_name: str, acr_name: str = None, save_path: str = None, verbose: bool = True
):
    try:
        # Load environment variables
        acr_name = acr_name or os.getenv("ACR_NAME", "acvdpwu2p001acr")
        acr_url = f"https://{acr_name}.azurecr.io"

        # Authenticate using DefaultAzureCredential
        credential = DefaultAzureCredential()

        # Create a ContainerRegistryClient
        client = ContainerRegistryClient(
            endpoint=acr_url, credential=credential, audience="https://management.azure.com"
        )

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


def get_tags_from_repositories_multithreaded(
    repository_names: List[str], acr_name: str = None, save_path: str = None, max_workers: int = 5, verbose: bool = True
):
    """
    Get tags from multiple ACR repositories using multithreading.

    Args:
        repository_names: List of repository names to get tags from
        acr_name: ACR name (optional, uses environment variable if not provided)
        save_path: Path to save results as CSV (optional)
        max_workers: Maximum number of concurrent threads
        verbose: Whether to print verbose output

    Returns:
        pandas.DataFrame with all tags from all repositories
    """
    if not repository_names:
        print("No repository names provided")
        return pd.DataFrame()

    all_tags = []
    failed_repos = []

    def fetch_repo_tags(repo_name):
        try:
            return get_acr_repository_properties(repo_name, acr_name=acr_name, verbose=False)
        except Exception as e:
            failed_repos.append((repo_name, str(e)))
            if verbose:
                print(f"Failed to get tags for {repo_name}: {e}")
            return pd.DataFrame()

    if verbose:
        print(f"Fetching tags from {len(repository_names)} repositories using {max_workers} threads...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_repo = {executor.submit(fetch_repo_tags, repo): repo for repo in repository_names}

        # Collect results as they complete
        for future in as_completed(future_to_repo):
            repo_name = future_to_repo[future]
            try:
                result = future.result()
                if not result.empty:
                    all_tags.append(result)
                    if verbose:
                        print(f"✓ Completed {repo_name}: {len(result)} tags")
                else:
                    if verbose:
                        print(f"✗ No tags found for {repo_name}")
            except Exception as e:
                failed_repos.append((repo_name, str(e)))
                if verbose:
                    print(f"✗ Failed {repo_name}: {e}")

    # Combine all results
    if all_tags:
        combined_df = pd.concat(all_tags, ignore_index=True)
    else:
        combined_df = pd.DataFrame(columns=["repository", "tag", "created_on", "last_updated_on", "digest"])

    if verbose:
        print(f"\nSummary: {len(combined_df)} total tags from {len(repository_names)} repositories")
        if failed_repos:
            print(f"Failed repositories: {len(failed_repos)}")
            for repo, error in failed_repos:
                print(f"  - {repo}: {error}")

    # Save to CSV if requested
    if save_path:
        save_to_csv(combined_df, save_path)

    return combined_df


if __name__ == "__main__":
    list_acr_repositories(save_path="data/acr_repositories.csv")
    # get_acr_repository_properties("abanteai__apples-to-models-108")


# Async versions of the functions


async def async_list_acr_repositories(acr_name: str = None, save_path: str = None):
    """
    Async version of list_acr_repositories.

    Note: Since Azure Container Registry client doesn't have native async support,
    this function runs the synchronous version in an executor to avoid blocking.
    """
    loop = asyncio.get_event_loop()

    def _sync_list_repos():
        return list_acr_repositories(acr_name=acr_name, save_path=save_path)

    return await loop.run_in_executor(None, _sync_list_repos)


async def async_get_acr_repository_properties(
    repository_name: str, acr_name: str = None, save_path: str = None, verbose: bool = True
):
    """
    Async version of get_acr_repository_properties.

    Note: Since Azure Container Registry client doesn't have native async support,
    this function runs the synchronous version in an executor to avoid blocking.
    """
    loop = asyncio.get_event_loop()

    def _sync_get_props():
        return get_acr_repository_properties(repository_name, acr_name=acr_name, save_path=save_path, verbose=verbose)

    return await loop.run_in_executor(None, _sync_get_props)


async def async_get_tags_from_repositories(
    repository_names: List[str],
    acr_name: str = None,
    save_path: str = None,
    max_concurrent: int = 5,
    verbose: bool = True,
):
    """
    Async version to get tags from multiple ACR repositories using asyncio.

    Args:
        repository_names: List of repository names to get tags from
        acr_name: ACR name (optional, uses environment variable if not provided)
        save_path: Path to save results as CSV (optional)
        max_concurrent: Maximum number of concurrent async operations
        verbose: Whether to print verbose output

    Returns:
        pandas.DataFrame with all tags from all repositories
    """
    if not repository_names:
        if verbose:
            print("No repository names provided")
        return pd.DataFrame()

    if verbose:
        print(
            f"Fetching tags from {len(repository_names)} repositories with "
            f"max {max_concurrent} concurrent operations..."
        )

    # Create a semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_repo_tags_async(repo_name: str):
        async with semaphore:
            try:
                result = await async_get_acr_repository_properties(repo_name, acr_name=acr_name, verbose=False)
                if verbose and result is not None and not result.empty:
                    print(f"✓ Completed {repo_name}: {len(result)} tags")
                elif verbose:
                    print(f"✗ No tags found for {repo_name}")
                return result
            except Exception as e:
                if verbose:
                    print(f"✗ Failed {repo_name}: {e}")
                return pd.DataFrame()

    # Run all tasks concurrently
    tasks = [fetch_repo_tags_async(repo) for repo in repository_names]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    all_tags = []
    failed_repos = []

    for i, result in enumerate(results):
        repo_name = repository_names[i]
        if isinstance(result, Exception):
            failed_repos.append((repo_name, str(result)))
        elif result is not None and not result.empty:
            all_tags.append(result)

    # Combine all results
    if all_tags:
        combined_df = pd.concat(all_tags, ignore_index=True)
    else:
        combined_df = pd.DataFrame(columns=["repository", "tag", "created_on", "last_updated_on", "digest"])

    if verbose:
        print(f"\nAsync Summary: {len(combined_df)} total tags from {len(repository_names)} repositories")
        if failed_repos:
            print(f"Failed repositories: {len(failed_repos)}")
            for repo, error in failed_repos:
                print(f"  - {repo}: {error}")

    # Save to CSV if requested
    if save_path:
        save_to_csv(combined_df, save_path)

    return combined_df
