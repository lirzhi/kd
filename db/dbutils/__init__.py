#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import logging
import os
import re
import tiktoken
from utils.file_util import get_project_base_directory

def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        key = str(cls) + str(os.getpid())
        if key not in instances:
            instances[key] = cls(*args, **kw)
        return instances[key]

    return _singleton


def rmSpace(txt):
    txt = re.sub(r"([^a-z0-9.,\)>]) +([^ ])", r"\1\2", txt, flags=re.IGNORECASE)
    return re.sub(r"([^ ]) +([^a-z0-9.,\(<])", r"\1\2", txt, flags=re.IGNORECASE)


def findMaxDt(fnm):
    m = "1970-01-01 00:00:00"
    try:
        with open(fnm, "r") as f:
            while True:
                l = f.readline()
                if not l:
                    break
                l = l.strip("\n")
                if l == 'nan':
                    continue
                if l > m:
                    m = l
    except Exception as e:
        pass
    return m

  
def findMaxTm(fnm):
    m = 0
    try:
        with open(fnm, "r") as f:
            while True:
                l = f.readline()
                if not l:
                    break
                l = l.strip("\n")
                if l == 'nan':
                    continue
                if int(l) > m:
                    m = int(l)
    except Exception as e:
        pass
    return m

tiktoken_cache_dir = get_project_base_directory()
os.environ["TIKTOKEN_CACHE_DIR"] = tiktoken_cache_dir
# encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
encoder = tiktoken.get_encoding("cl100k_base")


def truncate(string: str, max_len: int) -> str:
    """Returns truncated text if the length of text exceed max_len."""
    return encoder.decode(encoder.encode(string)[:max_len])