from ollama import chat
import json
from pydantic import BaseModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
import sys
import os

from .prompts import *
from .response_models import *
from scr.vdb.tags import requirements2query
from scr.utils import paste_line
from scr.config import *

def split_resume_into_sections(resume):
    """
    Splits the resume text into sections based on Markdown headers (#).
    """
    sections = {}
    current_section = "General"
    sections[current_section] = []
    
    for line in resume.splitlines():
        if line.startswith("#"):
            current_section = line.strip()
            sections[current_section] = []
        else:
            sections[current_section].append(line.strip())
    
    # Merge lines into single strings for each section
    for section in sections:
        sections[section] = "\n".join(sections[section])
    
    return sections

def summarize_section(section_title, section_content):
    """
    Summarizes a single section of the resume using the LLM.
    """
    user_prompt = summarize_section_usr.format(section_title=section_title, section_content=section_content)
    response = chat(
        model=model_config["summary"],
        messages=[
            {"role": "system", "content": summarize_section_sys},
            {"role": "user", "content": user_prompt}
        ],
        format=None
    )
    return response.message.content

def summarize_resume(resume):
    """
    Splits the resume into sections, summarizes each section, and merges the results.
    """
    # Step 1: Split the resume into sections
    sections = split_resume_into_sections(resume)
    
    # Step 2: Summarize each section
    summarized_sections = []
    for section_title, section_content in sections.items():
        if section_content.strip():
            summary = summarize_section(section_title, section_content)
            summarized_sections.append(f"\n{summary}")
    
    # Step 3: Merge the summaries into one text
    return "\n\n".join(summarized_sections)

def generate_ideal_job_description(user_input, resume):
    """
    Generates an ideal job description based on the user's input and resume.
    """
    response = chat(
        model=model_config["ideal_job_description"],
        messages=[
            {"role": "system", "content": ideal_job_sys.format(date=datetime.now().strftime("%Y-%m-%d"))},
            {"role": "user", "content": ideal_job_usr.format(user_input=user_input, resume=resume)}
        ],
        format=None
    )
    return response.message.content

def get_ad_name(ad_path):
    """Extarct the name of the ad from the path"""
    return ad_path.split("/")[-1].split(".txt")[0]

def ad_paths_from_names(ad_names, ad_dir):
    ad_paths = []
    for ad_name in ad_names:
        ad_path = os.path.join(ad_dir, ad_name + ".txt")
        ad_paths.append(ad_path)
    return ad_paths

def fetch_ads(ad_paths):
    def create_centered_header(name, width=80):
        # Create the separator line
        separator = "━" * width
        
        # Calculate padding for centering the name
        # Subtract 2 to account for spaces on either side of the name
        padding = (width - len(name) - 2) // 2
        
        # Create the centered name line
        # Handle odd-length names by adding extra space on the right if needed
        left_padding = " " * padding
        right_padding = " " * (width - padding - len(name) - 2)
        centered_name = f"{left_padding} {name} {right_padding}"
        
        return f"{separator}\n{centered_name}\n{separator}"

    # Load the ads
    res_lst = []
    ad_names = []
    
    for path in ad_paths:
        with open(path, "r") as f:
            res_str = ""
            # Get the name of the ad
            name = get_ad_name(path)
            ad_names.append(name)
            
            # Create the formatted header
            res_str += create_centered_header(name) + "\n"
            res_str += f.read()
            res_lst.append(res_str)
            
    return res_lst, ad_names

def split_ideal_job(ideal_job):
    text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=600,
                chunk_overlap=100,
                separators=["\n\n", "\n", " ", ""],
            )
    ideal_job_chunks = text_splitter.split_text(ideal_job)
    return ideal_job_chunks


def get_top_results(all_search_results_sorted, n):
    """
    Fast method to get the top n results from the sorted search results.
    Ads will be sorted based on first mention in the search results.
    """
    top_ads = []
    
    for res in all_search_results_sorted:
        metadata = res[0].metadata
        ad_name = get_ad_name(metadata["source"])
        if ad_name not in [list(ad.keys())[0] for ad in top_ads]:
            top_ads.append({ad_name:metadata})
        if len(top_ads) == n:
            break
    return top_ads

def paste_results(top_results, ad_lst):
    remote_dict = {
        "fully_remote": "Remote",
        "partly_remote": "Hybrid",
        "on_site": "On-site"
    }

    def truncate_text(text, width):
        if len(str(text)) > width:
            return str(text)[:width-3] + "..."
        return str(text)

    # Create header for the table
    top_lst = "\nHere are some ads you might find interesting, sorted by relevance:\n"
    
    # Add table header with proper spacing
    headers = [" ", "Email / Job Listing", "Location", "Start date", "Remote"]
    col_widths = [2, 32, 16, 10, 7]  # Adjust column widths as needed
    
    # Create the header row with only inner borders
    header_row = " | ".join(f"{header:<{width}}" for header, width in zip(headers, col_widths))
    separator = "-+-".join("-" * width for width in col_widths)
    
    top_lst += f"\n{header_row}\n{separator}"
    
    # Add each job to the table
    for i, res in enumerate(top_results):
        job_name = truncate_text(list(res.keys())[0], col_widths[1])
        details = list(res.values())[0]
        try:
            location = truncate_text(details['location'], col_widths[2])
        except:
            location = "N/A"

        try:
            start_date = truncate_text(details['start_date_str'], col_widths[3])
        except:
            start_date = "N/A"

        try:
            remote = truncate_text(remote_dict[details['remote']], col_widths[4])
        except:
            remote = "N/A"
        
        row = [
            str(i + 1),
            job_name,
            location,
            start_date,
            remote
        ]
        
        formatted_row = " | ".join(f"{str(val):<{width}}" for val, width in zip(row, col_widths))
        top_lst += f"\n{formatted_row}"
    
    top_lst += "\n\n"
    
    res_str = ""
    for ad in ad_lst:
        res_str += ad
        res_str += "\n\n"
    
    return top_lst, res_str

def CompetenceMatching(user_prompt, sum_res, db):
    # Ideal job description
    print("[IDEAL JOB GENERATOR] Generating ideal job description")
    ideal_job = generate_ideal_job_description(user_prompt, sum_res)
    ideal_job_chunks = split_ideal_job(ideal_job)

    # Get filters for the search
    if user_prompt:
        print(f"[FILTER] Generating search filters")
    filters_from_llm = requirements2query(user_prompt)

    # Use each chunk ideal ad to search for ad chunk in vdb
    #print(f"[SEARCH] Starting extensive search")
    all_search_results = []
    for ideal_job_chunk in ideal_job_chunks:
        #print(f"[FILTER]: Got filters: {filters_from_llm}" if filters_from_llm else "[FILTER]: No filters")
        search_results = db.search(ideal_job_chunk, filters_from_llm, num_results=NUM_RES_PER_CHUNK)
        all_search_results.extend(search_results)
    print(f"[SEARCH] Extensive search completed! {len(all_search_results)} results found")

    # Sort the search results by similarity score
    all_search_results_sorted = sorted(all_search_results, key=lambda x: x[1])

    top_results = get_top_results(all_search_results_sorted, MAX_RES_USER)
    ad_paths_from_names_lst = [list(ad.values())[0]['source'] for ad in top_results]
    # Collect a list of the ad contents
    ad_lst, _ = fetch_ads(ad_paths_from_names_lst)
    print("Done! 🎉")
    for res in top_results:
        print(res)
    top_lst, res_str = paste_results(top_results, ad_lst)
    return top_lst, res_str
    