from pinterest_dl.exceptions import ExecutableNotFoundError


def ensure_executable(executable: str) -> str:
    """
    Ensure the given binary is available in the system PATH.

    Args:
        executable (str): The name of the executable to check.

    Returns:
        str: The path to the executable if found.

    Raises:
        ExecutableNotFoundError: If the executable is not found in the system PATH.
    """
    import shutil

    path = shutil.which(executable)
    if path is None:
        raise ExecutableNotFoundError(f"{executable} not found in system PATH.")
    return path
