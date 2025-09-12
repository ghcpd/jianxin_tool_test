import pytest
import os
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from acr_helper import save_to_csv, list_acr_repositories, get_acr_repository_properties


class TestSaveToCsv:
    """Test cases for save_to_csv function"""
    
    def test_save_to_csv_creates_directory(self, tmp_path):
        """Test that save_to_csv creates necessary directories"""
        data = [{'name': 'test', 'value': 123}]
        filename = tmp_path / "subdir" / "test.csv"
        
        save_to_csv(data, str(filename))
        
        assert filename.exists()
        assert filename.parent.exists()
    
    def test_save_to_csv_saves_data_correctly(self, tmp_path):
        """Test that save_to_csv saves data in correct CSV format"""
        data = [
            {'name': 'item1', 'value': 100},
            {'name': 'item2', 'value': 200}
        ]
        filename = tmp_path / "test.csv"
        
        save_to_csv(data, str(filename))
        
        # Read the saved CSV and verify content
        df = pd.read_csv(filename)
        assert len(df) == 2
        assert list(df.columns) == ['name', 'value']
        assert df.iloc[0]['name'] == 'item1'
        assert df.iloc[0]['value'] == 100
    
    def test_save_to_csv_with_empty_data(self, tmp_path):
        """Test save_to_csv with empty data"""
        data = []
        filename = tmp_path / "empty.csv"
        
        save_to_csv(data, str(filename))
        
        assert filename.exists()
        with pytest.raises(pd.errors.EmptyDataError):
            pd.read_csv(filename)


class TestListAcrRepositories:
    """Test cases for list_acr_repositories function"""
    
    @patch('acr_helper.DefaultAzureCredential')
    @patch('acr_helper.ContainerRegistryClient')
    @patch('acr_helper.save_to_csv')
    @patch.dict(os.environ, {'ACR_NAME': 'test_acr'})
    def test_list_acr_repositories_success(self, mock_save_csv, mock_client_class, mock_credential):
        """Test successful listing of ACR repositories"""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_repository_names.return_value = ['repo1', 'repo2', 'repo3']
        
        # Call the function
        list_acr_repositories(save_path="test.csv")
        
        # Verify interactions
        mock_credential.assert_called_once()
        mock_client_class.assert_called_once_with(
            endpoint="https://test_acr.azurecr.io",
            credential=mock_credential.return_value,
            audience="https://management.azure.com"
        )
        mock_client.list_repository_names.assert_called_once()
        
        # Verify save_to_csv was called with correct data
        mock_save_csv.assert_called_once()
        call_args = mock_save_csv.call_args
        saved_data = call_args[0][0]  # First argument to save_to_csv
        assert len(saved_data) == 3
        assert saved_data.columns.tolist() == ['repository']
        assert saved_data['repository'].tolist() == ['repo1', 'repo2', 'repo3']
    
    @patch('acr_helper.DefaultAzureCredential')
    @patch('acr_helper.ContainerRegistryClient')
    def test_list_acr_repositories_with_custom_acr_name(self, mock_client_class, mock_credential):
        """Test list_acr_repositories with custom ACR name"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_repository_names.return_value = []
        
        list_acr_repositories(acr_name="custom_acr")
        
        mock_client_class.assert_called_once_with(
            endpoint="https://custom_acr.azurecr.io",
            credential=mock_credential.return_value,
            audience="https://management.azure.com"
        )
    
    @patch('acr_helper.DefaultAzureCredential')
    @patch('acr_helper.ContainerRegistryClient')
    @patch('builtins.print')
    def test_list_acr_repositories_exception_handling(self, mock_print, mock_client_class, mock_credential):
        """Test exception handling in list_acr_repositories"""
        mock_client_class.side_effect = Exception("Connection failed")
        
        list_acr_repositories()
        
        mock_print.assert_called_with("An error occurred: Connection failed")


class TestGetAcrRepositoryProperties:
    """Test cases for get_acr_repository_properties function"""
    
    @patch('acr_helper.DefaultAzureCredential')
    @patch('acr_helper.ContainerRegistryClient')
    @patch('acr_helper.save_to_csv')
    def test_get_acr_repository_properties_success(self, mock_save_csv, mock_client_class, mock_credential):
        """Test successful retrieval of repository properties"""
        # Setup mock tag objects
        mock_tag1 = MagicMock()
        mock_tag1.name = "v1.0"
        mock_tag1.created_on = "2023-01-01"
        mock_tag1.last_updated_on = "2023-01-02"
        mock_tag1.digest = "sha256:abc123"
        
        mock_tag2 = MagicMock()
        mock_tag2.name = "latest"
        mock_tag2.created_on = "2023-01-03"
        mock_tag2.last_updated_on = "2023-01-04"
        mock_tag2.digest = "sha256:def456"
        
        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_tag_properties.return_value = [mock_tag1, mock_tag2]
        
        # Call the function
        result = get_acr_repository_properties("test_repo", save_path="test.csv", verbose=False)
        
        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["repository", "tag", "created_on", "last_updated_on", "digest"]
        assert result.iloc[0]['repository'] == 'test_repo'
        assert result.iloc[0]['tag'] == 'v1.0'
        assert result.iloc[1]['tag'] == 'latest'
        
        # Verify save_to_csv was called
        mock_save_csv.assert_called_once_with(result, "test.csv")
    
    @patch('acr_helper.DefaultAzureCredential')
    @patch('acr_helper.ContainerRegistryClient')
    @patch('builtins.print')
    def test_get_acr_repository_properties_verbose_output(self, mock_print, mock_client_class, mock_credential):
        """Test verbose output in get_acr_repository_properties"""
        mock_tag = MagicMock()
        mock_tag.name = "v1.0"
        mock_tag.created_on = "2023-01-01"
        mock_tag.last_updated_on = "2023-01-02"
        mock_tag.digest = "sha256:abc123"
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_tag_properties.return_value = [mock_tag]
        
        get_acr_repository_properties("test_repo", verbose=True)
        
        # Check that print was called with expected messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert "Tags in repository 'test_repo':" in print_calls
        assert "- v1.0" in print_calls
    
    @patch('acr_helper.DefaultAzureCredential')
    @patch('acr_helper.ContainerRegistryClient')
    @patch('builtins.print')
    def test_get_acr_repository_properties_exception_handling(self, mock_print, mock_client_class, mock_credential):
        """Test exception handling in get_acr_repository_properties"""
        mock_client_class.side_effect = Exception("Authentication failed")
        
        result = get_acr_repository_properties("test_repo")
        
        mock_print.assert_called_with("An error occurred: Authentication failed")
        assert result is None
    
    @patch('acr_helper.DefaultAzureCredential')
    @patch('acr_helper.ContainerRegistryClient')
    @patch.dict(os.environ, {'ACR_NAME': 'env_acr'})
    def test_get_acr_repository_properties_uses_env_acr_name(self, mock_client_class, mock_credential):
        """Test that function uses ACR name from environment variable"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_tag_properties.return_value = []
        
        get_acr_repository_properties("test_repo")
        
        mock_client_class.assert_called_once_with(
            endpoint="https://env_acr.azurecr.io",
            credential=mock_credential.return_value,
            audience="https://management.azure.com"
        )


class TestIntegration:
    """Integration tests"""
    
    def test_csv_save_and_load_integration(self, tmp_path):
        """Test integration between data processing and CSV saving"""
        # Create sample data similar to what the functions would generate
        repo_data = [['repo1'], ['repo2']]
        filename = tmp_path / "integration_test.csv"
        
        # Save data
        save_to_csv(repo_data, str(filename))
        
        # Load and verify
        df = pd.read_csv(filename)
        assert len(df) == 2
        assert df.iloc[0, 0] == 'repo1'
        assert df.iloc[1, 0] == 'repo2'


# Fixtures for common test data
@pytest.fixture
def sample_repository_data():
    """Fixture providing sample repository data"""
    return [
        ['repo1'],
        ['repo2'],
        ['repo3']
    ]


@pytest.fixture
def sample_tag_data():
    """Fixture providing sample tag data"""
    return [
        ['test_repo', 'v1.0', '2023-01-01', '2023-01-02', 'sha256:abc123'],
        ['test_repo', 'latest', '2023-01-03', '2023-01-04', 'sha256:def456']
    ]


if __name__ == "__main__":
    pytest.main([__file__])