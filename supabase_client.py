# supabase_client.py

from supabase import create_client, Client
import os

class SupabaseConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            urL: str = os.environ.get("SUPABASE_URL")
            key: str = os.environ.get("SUPABASE_KEY")
            cls._instance = create_client(urL, key)
        return cls._instance