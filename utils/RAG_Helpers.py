# ------------!
# Misc imports for helpers
from typing import List, Dict  # Dictionary constructor
from pydantic import BaseModel  # Data validator
import io  # For report file read/write
import os
from dotenv import load_dotenv
import re

#Global configs
load_dotenv()  # Load environment variables from .env file

# Global variables
# Taken from .env file otherwise default to local path
REPORTS_DIR = os.getenv("REPORTS_DIR", "<LOCAL PATH FOR REPORTS DIR >")  # Directory for reports
REPORTS_FILE_NAME = "accumulated_daily.txt"
# ------------------------------------------------------
# Utility func for dynamic s3 bucket location path


def get_dynamic_metadata_value(metadata: Dict, path: List[str]):
    value = metadata
    try:
        for key in path:
            value = value[key]
    except KeyError:
        value = None  # Handle the case where the key is not found
    return value


# ------------------------------------------------------
# Citation Report Creation


class Citation(BaseModel):
    page_content: str
    metadata: Dict


def extract_citations(context: List[Dict]) -> List[Citation]:
    return [Citation(page_content=doc.page_content, metadata=doc.metadata) for doc in context]


# ------------------------------------------------------
# Accumulated daily report function


def accumulated_daily(cb, dt):
    today_date_exists = False  # In case today date doesn't exists yet, create it with flag
    today_date = str(dt.date())
    fname = REPORTS_DIR + REPORTS_FILE_NAME  # Interchangeable to different path
    try:
        with io.open(fname, "r+", encoding="utf8") as f:
            lines = f.readlines()
            # Group 1 is prefix e.g, "on date 1901-01-01 total costs in USD: $"
            # Group 2 is the total costs, e.g, 0.0002313
            # Hence the line is "on date <dt.date()> total costs in USD: $0.0002313"
            pattern = rf"({today_date}.*?\$)([0-9.]+)"
            for idx, line in enumerate(lines):
                # print(today_date)
                match = re.search(pattern, line)
                # print(match)
                if match:
                    today_date_exists = True
                    prefix_group = match.group(1)
                    # print("if matched")
                    curr_value = float(match.group(2))
                    # print(curr_value)
                    new_val = cb + curr_value
                    # print(lines[idx])
                    lines[idx] = re.sub(pattern, f"{prefix_group}{new_val:.7f}", line)
                    # print(lines[idx])
                    f.seek(0)  # Pointer to start of file
                    f.truncate()  # Remove all content, e.g, '%d' in vim
                    f.writelines(lines)  # Write all data with update sum
                    break
            if not today_date_exists:
                with io.open(fname, "a", encoding="utf8") as f:
                    f.write(f"\non date {today_date} total costs in USD: ${cb:.7f}")
    except FileNotFoundError:
        with io.open(fname, "a", encoding="utf8") as f:
            f.write(f"on date {today_date} total costs in USD: ${cb:.7f}")
