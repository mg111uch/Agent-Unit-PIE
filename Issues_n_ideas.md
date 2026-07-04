# Problem statement

Suppose I have this project codebase structure:

```
project_dir/
├── subdir1/                         
│   ├── subsubdir1/
│   │   ├── file2.py         
│   │   └── file3.py          
│   └── file4.py  
├── subdir2/                         
│   ├── subsubdir2/
│   │   ├── file5.py         
│   │   └── file6.py          
│   └── file7.py
└── file1.py  
```

I want to render node graph of this project, but as there are so many files in node, rendering whole graph simultaneously and relocating nodes is not possible. What else i could do is render graph of subdirectories one by one, rearrange node as i want and save it. Finally rendering whole codebase becomes easy as it just load saved state of already arranged subdirectories nodes. How could this be achieved with respect to current graph served using `python/Agentic_Unit_PIE/codebase/modules/codebase_atlas/graph/backend/serve.py`. Also can we group files nodes in boxes as per the subdirectories are organised in the codebase.