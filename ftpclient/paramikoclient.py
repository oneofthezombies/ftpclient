# -*- coding: utf-8 -*-

from typing import Optional, List
from pathlib import PurePosixPath
import paramiko

from ftpclient.interface import IFTPClient, TIMEOUT


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

    def set_working_directory(self, remote_path: str, create_directory: bool = True) -> None:
        self.client.chdir(remote_path)

    def get_working_directory(self) -> str:
        return self.client.getcwd()

    def create_directory(self, remote_path: str, is_exist_ok: bool = True) -> None:
        pass

    def get_contents(self, remote_path: str, create_directory: bool = True, is_recursive: bool = False) -> [str]:
        contents = []
        self._get_files_and_directories(remote_path, contents, contents, is_recursive)
        return contents

    def get_files(self, remote_path: str, is_recursive: bool = False) -> [str]:
        files = []
        directories = [] if is_recursive else None
        self._get_files_and_directories(remote_path, files, directories, is_recursive)
        return files

    def get_directories(self, remote_path: str, is_recursive: bool = False) -> [str]:
        directories = []
        self._get_files_and_directories(remote_path, None, directories, is_recursive)
        return directories

    def get_files_and_directories(self, remote_path: str, is_recursive: bool = False) -> ([str], [str]):
        files = []
        directories = []
        self._get_files_and_directories(remote_path, files, directories, is_recursive)
        return files, directories

    def _get_files_and_directories(self, remote_path: str, out_files: Optional[List[str]],
                                   out_directories: Optional[List[str]], is_recursive: bool = False) -> None:
        files = []
        directories = []
        remote_path_object = PurePosixPath(remote_path)
        for file in self.client.listdir_iter(remote_path):
            if file.longname.startswith('d'):
                if out_directories is not None:
                    directories.append(str(remote_path_object / f'{file.filename}/'))
            else:
                if out_files is not None:
                    files.append(str(remote_path_object / file.filename))
        total_sub_directories = []
        if is_recursive:
            for directory in directories:
                sub_files = [] if out_files is not None else None
                sub_directories = []
                self._get_files_and_directories(directory, sub_files, sub_directories, is_recursive)
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
        pass


if __name__ == '__main__':
    def test():
        host = '127.0.0.1'
        username = password = 'hunhoekim'
        client = SFTPClient(host=host, username=username, password=password)
        assert client.get_working_directory() == '/'
        client.set_working_directory('/TDD')
        assert client.get_working_directory() == '/TDD/'
        print(client.get_files_and_directories('.', is_recursive=True))
        print(client.get_contents('.', is_recursive=True))
        print(client.get_files('.', is_recursive=True))
        print(client.get_directories('.', is_recursive=True))

    test()
