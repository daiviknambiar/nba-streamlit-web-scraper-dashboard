import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from dotenv import load_dotenv
from supabase import create_client, Client
import os


def get_client() -> Client:
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    return create_client(url, key)

def main():
    supabase = get_client()
    response = supabase.table("nba_news_data").select("*").execute()
    