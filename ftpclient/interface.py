# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

TIMEOUT = 600


class FTPFileNotExistError(FileNotFoundError):
    def __init__(self, remote_path: str):
        super().__init__(1, f'File does not exist. ')
        self.filename = remote_path


class FTPDirectoryNotExistError(FileNotFoundError):
    def __init__(self, remote_path: str):
        super().__init__(1, f'Directory does not exist. ')
        self.filename = remote_path


class IFTPClient(metaclass=ABCMeta):
    @abstractmethod
    def set_working_directory(self, remote_path: str, create_directory: bool = True) -> None:
        pass

    @abstractmethod
    def get_working_directory(self) -> str:
        pass

    @abstractmethod
    def create_directory(self, remote_path: str, is_exist_ok: bool = True) -> None:
        pass

    @abstractmethod
    def get_contents(self, remote_path: str, is_recursive: bool = False) -> [str]:
        pass

    @abstractmethod
    def get_files(self, remote_path: str, is_recursive: bool = False) -> [str]:
        pass

    @abstractmethod
    def get_directories(self, remote_path: str, is_recursive: bool = False) -> [str]:
        pass

    @abstractmethod
    def get_files_and_directories(self, remote_path: str, is_recursive: bool = False) -> ([str], [str]):
        pass

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str, create_directory: bool = True) -> None:
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> None:
        pass

    @abstractmethod
    def get_file_size(self, remote_path: str) -> int:
        pass
