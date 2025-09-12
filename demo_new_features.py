#!/usr/bin/env python3
"""
Demo script showing the new ACR helper features
"""

# Example usage of new features:

# 1. Multithreaded tag retrieval from multiple repositories
from acr_helper import get_tags_from_repositories_multithreaded

repository_list = ["repo1", "repo2", "repo3"]
# Get tags from multiple repositories using threading
# result = get_tags_from_repositories_multithreaded(
#     repository_names=repository_list,
#     acr_name="your-acr-name",
#     save_path="output/tags.csv",  # Save results to CSV
#     max_workers=3,                # Use 3 concurrent threads
#     verbose=True
# )

# 2. Async version for better performance in async applications
import asyncio
from acr_helper import async_get_tags_from_repositories

async def main():
    # result = await async_get_tags_from_repositories(
    #     repository_names=repository_list,
    #     acr_name="your-acr-name", 
    #     save_path="output/async_tags.csv",  # Save results to CSV
    #     max_concurrent=3,                   # Max concurrent operations
    #     verbose=True
    # )
    pass

# Run async function
# asyncio.run(main())

print("Demo script ready - uncomment lines to test with real ACR credentials")