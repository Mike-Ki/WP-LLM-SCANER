from abc import ABC, abstractmethod
from typing import Iterator
import os
import hashlib


class AbstractStaticAnalysisToolBase(ABC):

    @abstractmethod
    def run(self) -> Iterator[str]:
        """This function should return a prompt template for every round in the manner of using yield"""


class StaticAnalysisToolBase(AbstractStaticAnalysisToolBase):


    def __init__(self, directory):
        self.directory = os.path.relpath(directory)
        os.makedirs(os.path.join(self.directory, 'wp_scanner'), exist_ok=True)

        self.hash = self.hash_directory()

        self.cache_dir = os.path.join(self.directory, f'wp_scanner')


    def hash_directory(self):
        sha = hashlib.sha256()
        for root, dirs, files in os.walk(self.directory):
            if 'wp_scanner' in dirs:
                dirs.remove('wp_scanner')
            for file in sorted(files):
                filepath = os.path.join(root, file)
                with open(filepath, 'rb') as f:
                    while chunk := f.read(8192):
                        sha.update(chunk)
        return sha.hexdigest()