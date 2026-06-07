import sys
print("Starting debug_imports.py...", flush=True)

try:
    print("Importing os...", flush=True)
    import os
    print("Importing csv...", flush=True)
    import csv
    print("Importing random...", flush=True)
    import random
    print("Importing json...", flush=True)
    import json
    print("Importing flask...", flush=True)
    from flask import Flask, request, jsonify, send_from_directory, send_file
    print("Importing numpy...", flush=True)
    import numpy as np
    print("Importing joblib...", flush=True)
    import joblib
    print("Importing pandas...", flush=True)
    import pandas as pd
    print("Importing dotenv...", flush=True)
    from dotenv import load_dotenv
    print("Importing pymongo...", flush=True)
    from pymongo import MongoClient
    print("Importing google.generativeai...", flush=True)
    import google.generativeai as genai
    print("Importing certifi...", flush=True)
    import certifi
    print("Importing fpdf...", flush=True)
    from fpdf import FPDF
    print("Importing tempfile...", flush=True)
    import tempfile
    print("Importing auth...", flush=True)
    from auth import UserAuth
    print("Importing image_analysis.predict...", flush=True)
    from image_analysis.predict import XRayPredictor
    print("All imports successful!", flush=True)
except Exception as e:
    print(f"Exception during imports: {e}", flush=True)
