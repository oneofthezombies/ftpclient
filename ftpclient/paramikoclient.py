# -*- coding: utf-8 -*-
# builtin packages
from pathlib import PurePosixPath
from typing import Optional, List
import stat
# site packages
import paramiko
# ootz.ftpclient packages
from ftpclient.interface import (IFTPClient, TIMEOUT, FTPFileNotExistError, FTPDirectoryNotExistError)


class SFTPClient(IFTPClient):
    def __init__(self, host: str, port: int = 22, username: Optional[str] = None, password: Optional[str] = None,
                 timeout: int = TIMEOUT):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.ssh = None
        self.client = None
        self._connect()

    def __del__(self):
        self._disconnect()

    def _connect(self):
        self._disconnect()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        ssh.connect(hostname=self.host, username=self.username, password=self.password, timeout=self.timeout)
        client = ssh.open_sftp()
        client.chdir('.')
        self.ssh = ssh
        self.client = client

    def _disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
        if self.ssh:
            self.ssh.close()
            self.ssh = None

    def is_exist(self, remote_path: str) -> bool:
        try:
            self.client.stat(remote_path)
            return True
        except FileNotFoundError:
            return False

    def is_directory(self, remote_path: str) -> bool:
        if self.is_exist(remote_path):
            return stat.S_ISDIR(self.client.stat(remote_path).st_mode)
        else:
            raise FTPDirectoryNotExistError(remote_path)

    def is_file(self, remote_path: str) -> bool:
        if self.is_exist(remote_path):
            return stat.S_ISREG(self.client.stat(remote_path).st_mode)
        else:
            raise FTPFileNotExistError(remote_path)

    def create_directory(self, remote_path: str, is_exist_ok: bool = True) -> None:
        split = PurePosixPath(remote_path).parts
        for i in range(len(split)):
            directory_object = PurePosixPath()
            for directory in split[:i + 1]:
                directory_object = directory_object / directory
            directory = str(directory_object)
            if self.is_exist(directory):
                if self.is_directory(directory):
                    if is_exist_ok:
                        continue
                    else:
                        error = FileExistsError(1, f'Directory already exists. ')
                        error.filename = directory
                        raise error
                else:
                    error = NotADirectoryError(1, f'This path is not a directory. ')
                    error.filename = directory
                    raise error
            else:
                self.client.mkdir(directory)

    def delete_directory(self, remote_path: str) -> None:
        if self.is_directory(remote_path):
            self.client.rmdir(remote_path)
        else:
            raise FTPDirectoryNotExistError(remote_path)

    def delete_file(self, remote_path: str) -> None:
        if self.is_file(remote_path):
            self.client.remove(remote_path)
        else:
            raise FTPFileNotExistError(remote_path)

    def delete(self, remote_path: str) -> None:
        if self.is_exist(remote_path):
            if self.is_file(remote_path):
                self.delete_file(remote_path)
            elif self.is_directory(remote_path):
                self.delete_directory(remote_path)
            else:
                error = OSError(1, f'This type is not supported. ')
                error.filename = remote_path
                raise error
        else:
            error = FileNotFoundError(1, f'This path does not exist. ')
            error.filename = remote_path
            raise error

    def delete_contents_in_directory(self, remote_path: str) -> None:
        pass

    def set_working_directory(self, remote_path: str, create_if_not_exist: bool = True) -> None:
        self.client.chdir(remote_path)

    def get_working_directory(self) -> str:
        return self.client.getcwd()

    def get_contents(self, remote_path: str, is_recursive: bool = False) -> [str]:
        contents = []
        self._get_files_and_directories(remote_path, '', contents, contents, is_recursive)
        return contents

    def get_files(self, remote_path: str, is_recursive: bool = False) -> [str]:
        files = []
        directories = [] if is_recursive else None
        self._get_files_and_directories(remote_path, '', files, directories, is_recursive)
        return files

    def get_directories(self, remote_path: str, is_recursive: bool = False) -> [str]:
        directories = []
        self._get_files_and_directories(remote_path, '', None, directories, is_recursive)
        return directories

    def get_files_and_directories(self, remote_path: str, is_recursive: bool = False) -> ([str], [str]):
        files = []
        directories = []
        self._get_files_and_directories(remote_path, '', files, directories, is_recursive)
        return files, directories

    def _get_files_and_directories(self, remote_path: str, traverse_directory: str,
                                   out_files: Optional[List[str]], out_directories: Optional[List[str]],
                                   is_recursive: bool = False) -> None:
        files = []
        directories = []
        traverse_path_object = PurePosixPath(remote_path) / traverse_directory
        traverse_directory_object = PurePosixPath(traverse_directory)
        for file in self.client.listdir_iter(str(traverse_path_object)):
            if file.longname.startswith('d'):
                if out_directories is not None:
                    directories.append(f'{str(traverse_directory_object / file.filename)}/')
            else:
                if out_files is not None:
                    files.append(str(traverse_directory_object / file.filename))
        total_sub_directories = []
        if is_recursive:
            for directory in directories:
                sub_files = [] if out_files is not None else None
                sub_directories = []
                self._get_files_and_directories(remote_path, directory, sub_files, sub_directories, is_recursive)
                if out_files is not None:
                    files.extend(sub_files)
                if out_directories is not None:
                    total_sub_directories.extend(sub_directories)
        if out_files is not None:
            out_files.extend(files)
        if out_directories is not None:
            out_directories.extend(directories)
            out_directories.extend(total_sub_directories)

    def upload_file(self, local_path: str, remote_path: str, create_directory: bool = True) -> None:
        pass

    def download_file(self, remote_path: str, local_path: str) -> None:
        pass

    def get_file_size(self, remote_path: str) -> int:
        return self.client.stat.st_size


if __name__ == '__main__':
    def test():
        host = '127.0.0.1'
        username = password = 'hunhoekim'
        client = SFTPClient(host=host, username=username, password=password)

        assert client.get_working_directory() == '/'

        assert client.is_exist('') is True
        assert client.is_exist('.') is True
        assert client.is_exist('./') is True
        assert client.is_exist('/') is True

        assert client.is_exist('TDD') is True
        assert client.is_exist('./TDD') is True
        assert client.is_exist('./TDD/') is True
        assert client.is_exist('/TDD') is True
        assert client.is_exist('/TDD/') is True

        assert client.is_exist('non-exist-directory') is False
        assert client.is_exist('/non-exist-directory') is False
        assert client.is_exist('/non-exist-directory/') is False

        client.delete_directory('A/B/C')
        try:
            client.create_directory('A/B/C', is_exist_ok=False)
        except FileExistsError as e:
            pass
        client.create_directory('/A/B/C', is_exist_ok=False)

        client.set_working_directory('TDD', create_if_not_exist=False)
        assert client.get_working_directory() == '/TDD/'
        client.set_working_directory('/TDD', create_if_not_exist=False)
        assert client.get_working_directory() == '/TDD/'
        client.set_working_directory('/TDD/', create_if_not_exist=False)
        assert client.get_working_directory() == '/TDD/'

        result = (['1-1.txt', '1-2.txt'], ['1-1/', '1-2/'])
        assert client.get_files_and_directories('', is_recursive=False) == result
        assert client.get_files_and_directories('.', is_recursive=False) == result
        assert client.get_files_and_directories('./', is_recursive=False) == result
        assert client.get_files_and_directories('/TDD', is_recursive=False) == result
        assert client.get_files_and_directories('/TDD/', is_recursive=False) == result

        result = (['1-1.txt', '1-2.txt', '1-1/2-1.txt', '1-1/2-1/3-1.txt', '1-1/2-1/3-1/0-1.txt', '1-2/2-2.txt', '1-2/2-2/3-2.txt', '1-2/2-2/3-2/0-2.txt'], ['1-1/', '1-2/', '1-1/2-1/', '1-1/2-1/3-1/', '1-1/2-1/3-1/0-1/', '1-2/2-2/', '1-2/2-2/3-2/', '1-2/2-2/3-2/0-2/'])
        assert client.get_files_and_directories('', is_recursive=True) == result
        assert client.get_files_and_directories('.', is_recursive=True) == result
        assert client.get_files_and_directories('./', is_recursive=True) == result
        assert client.get_files_and_directories('/TDD', is_recursive=True) == result
        assert client.get_files_and_directories('/TDD/', is_recursive=True) == result

        result = (['2-1.txt'], ['2-1/'])
        assert client.get_files_and_directories('1-1', is_recursive=False) == result
        assert client.get_files_and_directories('./1-1', is_recursive=False) == result
        assert client.get_files_and_directories('./1-1/', is_recursive=False) == result
        assert client.get_files_and_directories('/TDD/1-1', is_recursive=False) == result
        assert client.get_files_and_directories('/TDD/1-1/', is_recursive=False) == result

        result = (['2-1.txt', '2-1/3-1.txt', '2-1/3-1/0-1.txt'], ['2-1/', '2-1/3-1/', '2-1/3-1/0-1/'])
        assert client.get_files_and_directories('1-1', is_recursive=True) == result
        assert client.get_files_and_directories('./1-1', is_recursive=True) == result
        assert client.get_files_and_directories('./1-1/', is_recursive=True) == result
        assert client.get_files_and_directories('/TDD/1-1', is_recursive=True) == result
        assert client.get_files_and_directories('/TDD/1-1/', is_recursive=True) == result

        result = ['1-1.txt', '1-2.txt', '1-1/', '1-2/']
        assert client.get_contents('', is_recursive=False) == result
        assert client.get_contents('.', is_recursive=False) == result
        assert client.get_contents('./', is_recursive=False) == result
        assert client.get_contents('/TDD', is_recursive=False) == result
        assert client.get_contents('/TDD/', is_recursive=False) == result

        result = ['1-1.txt', '1-2.txt', '1-1/2-1.txt', '1-1/2-1/3-1.txt', '1-1/2-1/3-1/0-1.txt', '1-2/2-2.txt', '1-2/2-2/3-2.txt', '1-2/2-2/3-2/0-2.txt', '1-1/', '1-2/', '1-1/2-1/', '1-1/2-1/3-1/', '1-1/2-1/3-1/0-1/', '1-2/2-2/', '1-2/2-2/3-2/', '1-2/2-2/3-2/0-2/']
        assert client.get_contents('', is_recursive=True) == result
        assert client.get_contents('.', is_recursive=True) == result
        assert client.get_contents('./', is_recursive=True) == result
        assert client.get_contents('/TDD', is_recursive=True) == result
        assert client.get_contents('/TDD/', is_recursive=True) == result

        result = ['2-1.txt', '2-1/']
        assert client.get_contents('1-1', is_recursive=False) == result
        assert client.get_contents('./1-1', is_recursive=False) == result
        assert client.get_contents('./1-1/', is_recursive=False) == result
        assert client.get_contents('/TDD/1-1', is_recursive=False) == result
        assert client.get_contents('/TDD/1-1/', is_recursive=False) == result

        result = ['2-1.txt', '2-1/3-1.txt', '2-1/3-1/0-1.txt', '2-1/', '2-1/3-1/', '2-1/3-1/0-1/']
        assert client.get_contents('1-1', is_recursive=True) == result
        assert client.get_contents('./1-1', is_recursive=True) == result
        assert client.get_contents('./1-1/', is_recursive=True) == result
        assert client.get_contents('/TDD/1-1', is_recursive=True) == result
        assert client.get_contents('/TDD/1-1/', is_recursive=True) == result

        result = ['1-1.txt', '1-2.txt']
        assert client.get_files('', is_recursive=False) == result
        assert client.get_files('.', is_recursive=False) == result
        assert client.get_files('./', is_recursive=False) == result
        assert client.get_files('/TDD', is_recursive=False) == result
        assert client.get_files('/TDD/', is_recursive=False) == result

        result = ['1-1.txt', '1-2.txt', '1-1/2-1.txt', '1-1/2-1/3-1.txt', '1-1/2-1/3-1/0-1.txt', '1-2/2-2.txt', '1-2/2-2/3-2.txt', '1-2/2-2/3-2/0-2.txt']
        assert client.get_files('', is_recursive=True) == result
        assert client.get_files('.', is_recursive=True) == result
        assert client.get_files('./', is_recursive=True) == result
        assert client.get_files('/TDD', is_recursive=True) == result
        assert client.get_files('/TDD/', is_recursive=True) == result

        result = ['2-1.txt']
        assert client.get_files('1-1', is_recursive=False) == result
        assert client.get_files('./1-1', is_recursive=False) == result
        assert client.get_files('./1-1/', is_recursive=False) == result
        assert client.get_files('/TDD/1-1', is_recursive=False) == result
        assert client.get_files('/TDD/1-1/', is_recursive=False) == result

        result = ['2-1.txt', '2-1/3-1.txt', '2-1/3-1/0-1.txt']
        assert client.get_files('1-1', is_recursive=True) == result
        assert client.get_files('./1-1', is_recursive=True) == result
        assert client.get_files('./1-1/', is_recursive=True) == result
        assert client.get_files('/TDD/1-1', is_recursive=True) == result
        assert client.get_files('/TDD/1-1/', is_recursive=True) == result

        result = ['1-1/', '1-2/']
        assert client.get_directories('', is_recursive=False) == result
        assert client.get_directories('.', is_recursive=False) == result
        assert client.get_directories('./', is_recursive=False) == result
        assert client.get_directories('/TDD', is_recursive=False) == result
        assert client.get_directories('/TDD/', is_recursive=False) == result

        result = ['1-1/', '1-2/', '1-1/2-1/', '1-1/2-1/3-1/', '1-1/2-1/3-1/0-1/', '1-2/2-2/', '1-2/2-2/3-2/', '1-2/2-2/3-2/0-2/']
        assert client.get_directories('', is_recursive=True) == result
        assert client.get_directories('.', is_recursive=True) == result
        assert client.get_directories('./', is_recursive=True) == result
        assert client.get_directories('/TDD', is_recursive=True) == result
        assert client.get_directories('/TDD/', is_recursive=True) == result

        result = ['2-1/']
        assert client.get_directories('1-1', is_recursive=False) == result
        assert client.get_directories('./1-1', is_recursive=False) == result
        assert client.get_directories('./1-1/', is_recursive=False) == result
        assert client.get_directories('/TDD/1-1', is_recursive=False) == result
        assert client.get_directories('/TDD/1-1/', is_recursive=False) == result

        result = ['2-1/', '2-1/3-1/', '2-1/3-1/0-1/']
        assert client.get_directories('1-1', is_recursive=True) == result
        assert client.get_directories('./1-1', is_recursive=True) == result
        assert client.get_directories('./1-1/', is_recursive=True) == result
        assert client.get_directories('/TDD/1-1', is_recursive=True) == result
        assert client.get_directories('/TDD/1-1/', is_recursive=True) == result
    test()
