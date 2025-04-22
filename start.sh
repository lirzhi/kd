#!/bin/bash
cd llm/
python llm_server.py &
cd ..
python app.py 
echo "Both llm_server.py and app.py processes start successfully."