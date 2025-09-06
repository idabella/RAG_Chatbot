__version__ = "1.0.0" 
__author__ = "Abdessamad L."
__description__ = "An intelligent FAQ chatbot using RAGs and langchain models. "
__title__ = "FAQ chatbot " 

__lisence__ = "MIT License"
__copyright__ = "Copyright (c) 2023 Abdessamad L."

def get_version() :   
    return __version__ 

def get_author() :
    return __author__ 

def app_info() : 
    return {
        "version" : __version__ ,
        "author" : __author__ ,
        "description" : __description__ ,
        "title" : __title__ 
    }

__all__ =[
    "__version__",
    "__author__",
    "__description__",
    "__title__",
    "__lisence__",
    "__copyright__",
    "get_version",
    "get_author",
    "app_info"
]