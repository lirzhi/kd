from typing import TypedDict


class DataState(TypedDict):
    status: bool
    file_path: str
    origin_chunks: list
    cleaned_chunks: list
    split_chunks: list[list]
    final_chunks: list
    