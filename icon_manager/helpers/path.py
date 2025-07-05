import os
from typing import List, Optional


def is_file(path: str, name: str, extension: Optional[str] = None) -> bool:
    """
    Check if a file with the given name exists at the specified path and optionally matches a file extension.
    
    Parameters:
        path (str): Directory path to search in.
        name (str): Name of the file to check.
        extension (Optional[str]): File extension to match (with or without leading dot).
    
    Returns:
        bool: True if the file exists at the path and matches the extension (if provided), otherwise False.
    """
    if not os.path.isfile(os.path.join(path, name)):
        return False
    if extension is None:
        return True
    if not extension.startswith('.'):
        extension = f'.{extension}'
    return name.endswith(extension)


def get_files(path: str, extension: Optional[str] = None) -> List[str]:
    """
    Return a list of filenames in the specified directory, optionally filtered by file extension.
    
    Parameters:
        path (str): The directory to search for files.
        extension (Optional[str]): If provided, only files with this extension are included.
    
    Returns:
        List[str]: Filenames in the directory that match the extension criteria.
    """
    return [name for name in os.listdir(path) if is_file(path, name, extension)]
