import os
from mutil_agents.agent import data_graph
from mutil_agents.memory.data_state import DataState
from utils.file_util import rewrite_json_file

def data_process(file_path):
    # Your processing code here
    data_state = DataState()
    data_state["file_path"] = file_path
    data = data_graph.invoke(data_state)
    return data
    
def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            print(f"{root}:{file_path}")
            data = data_process(file_path)
            if data is None or not data.get("final_chunks"):
                print(f"Error: {file_path}")
                continue
            final_data = {
                "file_path": file_path,
                "data": []
            }
            index = 0
            for ds in data["final_chunks"]:
                for d in ds:
                    ++index
                    d["chunk_id"] = index
                    final_data["data"].append(d)
            save_file_path = file_path.replace('raw_data', 'cleaned_data').split('.')[0] + '.json'
            save_dir = os.path.dirname(save_file_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            rewrite_json_file(save_file_path, final_data)
        for dir in dirs:
            process_directory(os.path.join(root, dir))

if __name__ == "__main__":
    directory = 'data/raw_data/'
    process_directory(directory)