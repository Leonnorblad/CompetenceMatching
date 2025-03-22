print("Launching CompetenceMatching tool...")
from scr.vdb.vdb import VDB
from scr.utils import load_from_file, write_to_file, paste_line, paste_double_line, clear_console
from scr.vdb.parser import parse_email_dir, pdf_parser, extract_olm, parse_csv
from scr.competence_matching.matching import CompetenceMatching, summarize_resume
from scr.config import *
import time
import os
import re
import sys
import json
import random
from ollama import chat

def wave_unfold_effect(text, delay=0.009, step_size=1):
    """
    Print text with a wave effect, smoothly revealing characters.
    
    :param text: The text to animate.
    :param delay: Time delay between steps.
    :param step_size: Number of characters to reveal at each step.
    """
    lines = text.splitlines()
    max_length = max(len(line) for line in lines)
    total_steps = max_length + len(lines)

    lines = [line.ljust(max_length) for line in lines]

    # Move cursor to top instead of clearing screen
    print("\033[H\033[J", end="")  # ANSI clear screen

    for step in range(0, total_steps, step_size):
        sys.stdout.write("\033[H")  # Move cursor to top
        for i, line in enumerate(lines):
            start_idx = max(0, step - i)
            end_idx = min(max_length, start_idx + step_size)
            sys.stdout.write(line[:end_idx].rstrip() + "\n")
        sys.stdout.flush()
        time.sleep(delay)

logo = f"""═══════════════════════════════════════════════════════════════════════════════
  _____  ____   __  __  _____   ______  _______  ______  _   _   _____  ______  
 / ____|/ __ \ |  \/  ||  __ \ |  ____||__   __||  ____|| \ | | / ____||  ____| 
| |    | |  | || \  / || |__) || |__      | |   | |__   |  \| || |     | |__    
| |    | |  | || |\/| ||  ___/ |  __|     | |   |  __|  | . ` || |     |  __|   
| |____| |__| || |  | || |     | |____    | |   | |____ | |\  || |____ | |____  
 \_____|\____/ |_|  |_||_|     |______|   |_|   |______||_| \_| \_____||______| 
          __  __         _______  _____  _    _  _____  _   _   _____           
         |  \/  |    /\ |__   __|/ ____|| |  | ||_   _|| \ | | / ____|          
         | \  / |   /  \   | |  | |     | |__| |  | |  |  \| || |  __          
         | |\/| |  / /\ \  | |  | |     |  __  |  | |  | . ` || | |_ |          
         | |  | | / ____ \ | |  | |____ | |  | | _| |_ | |\  || |__| |         
         |_|  |_|/_/    \_\|_|   \_____||_|  |_||_____||_| \_| \_____|         

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 By Leonard Norblad | github.com/ComptenceMatching | Version {VERSION} ({DATE})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

DATABASE_TRACKER_FILE = "./user_data/created_databases.json"

def input_with_check(input_text, last_step=False):
    user_input = input(input_text)
    stop_words = ["exit", "bye", "goodbye", "stop", "quit"]
    if user_input in stop_words:
        if last_step:
            outro()
        else:
            say_goodbye()
    return user_input

def load_database_tracker():
    """Load the database tracker from a file."""
    if os.path.exists(DATABASE_TRACKER_FILE):
        with open(DATABASE_TRACKER_FILE, "r") as f:
            return json.load(f)
    return []

def save_database_tracker(database_list):
    """Save the database tracker to a file."""
    with open(DATABASE_TRACKER_FILE, "w") as f:
        json.dump(database_list, f, indent=4)

def bad_input():
    print("Hmm, that does not seem to be a valid option 😅 Please try again!\n")

def check_path(path):
    return os.path.exists(path)

def ask_for_path(user_text):
    while True:
        path = input_with_check(user_text)
        
        if check_path(path):
            return path
        else:
            bad_input()

def first_interaction():
    welcome_message = """Welcome to CompetenceMatching! 🤖

        +------------------+        +----------+     +--------------+        
        | Email Collection |  <-->  |  Resume  |  +  | Requirements |        
        +------------------+        +----------+     +--------------+        

The system matches your resume with job listings.
You can also enter requirements to refine the match results.

Type 'exit' anytime to leave. Ready to get started? 🚀"""
    print(welcome_message)

def olm_handler(olm_path):
    # Extact files and saved in user_data/olm_data
    extract_olm(olm_path)
    # if the olm olm_data data contains more than one folder, ask the user to select one
    olm_data = os.listdir("./user_data/olm_data/Accounts")
    if len(olm_data) > 1:
        print("\nSelect which email folder you would like to use:")
        for i, folder in enumerate(olm_data):
            print(f"{i+1}. {folder}")
        while True:
            folder_num = input_with_check("-> Selection: ")
            if folder_num in [str(i) for i in range(1, len(olm_data)+1)]:
                selected_folder = olm_data[int(folder_num)-1]
                break
            else:
                bad_input()
    else:
        selected_folder = olm_data[0]

    # Ask the user which outlok folder to use whithin the selected folder
    outlook_folders = os.listdir(f"./user_data/olm_data/Accounts/{selected_folder}/com.microsoft.__Messages")
    print("\nSelect which outlook folder you would like to use:")
    for i, folder in enumerate(outlook_folders):
        print(f"{i+1}. {folder}")
    while True:
        folder_num = input_with_check("-> Selection: ")
        if folder_num in [str(i) for i in range(1, len(outlook_folders)+1)]:
            selected_outlook_folder = outlook_folders[int(folder_num)-1]
            break
        else:
            bad_input()
    return f"./user_data/olm_data/Accounts/{selected_folder}/com.microsoft.__Messages/{selected_outlook_folder}"

def get_vdb_name(last_part_of_path):
    suggested_name = f"{last_part_of_path}_{time.strftime('%Y-%m-%d-%H-%M-%S')}_vdb"
    def sanitize_collection_name(name):
        # Truncate if the length exceeds 63 characters
        if len(name) > 63:
            # Ensure the last 63 characters are kept
            name = name[len(name) - 63:]

        # Remove invalid characters (anything other than alphanumeric, _, or -)
        name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

        # Replace multiple underscores or hyphens with a single underscore
        name = re.sub(r'[ _\-]+', '_', name)

        # Ensure it starts and ends with an alphanumeric character
        name = re.sub(r'^[_\-]+', '', name)  # Remove leading underscores or hyphens
        name = re.sub(r'[_\-]+$', '', name)  # Remove trailing underscores or hyphens

        return name
    return sanitize_collection_name(suggested_name)

def create_database(database_tracker):
    print("Lets import job listings from emails to create a collection! 📂")
    print("Enter the path to the folder containing emails (.eml, .txt, .xml, .pdf)")
    print("You can also input an .olm or .csv file.\n")
    while True:
        path = ask_for_path("-> Path: ")

        # First check if we got a folder or an .olm file, if it's an .olm file we need to extract it before parsing
        if os.path.basename(path).endswith(".olm"):
            path = olm_handler(path)
        
        last_part_of_path = os.path.basename(path)

        # Parse a csv file with emails
        if os.path.basename(path).lower().endswith(".csv"):
            dest_folder = f"./user_data/email_folders/{last_part_of_path[:-4]}_txts"
            parse_problems = parse_csv(path, dest_folder)
        # Parse a folder with emails
        else:
            dest_folder = f"./user_data/email_folders/{last_part_of_path}_txts"
            parse_problems = parse_email_dir(path, dest_folder)
        
        if parse_problems:
            print("The following emails can not be added to the collection (unsupported format):")
            for problem in parse_problems:
                print(f"- {problem}\n")
            _ = input_with_check("-> Press enter to continue or type 'exit' to exit: ")

        print("\nHang tight! Emails are being imported, and your new collection is being set up")
        
        vdb_name = get_vdb_name(last_part_of_path)
        db = VDB(vdb_name)
        db.add_docs(dest_folder)
        if len(db.db.get()['ids']) == 0:
            print("No documents were added to the collection. Please try again.")
            continue
        
        db.write_metadata()
        database_tracker.append(vdb_name)
        save_database_tracker(database_tracker)
        print(f"\n✅ Collection '{db.collection_name}' has been created!")
        _ = input_with_check("-> Press enter to continue: ")
        return db


def add_resume():
    print("\nPlease provide a path to the resume (.pdf)")
    while True:
        path = ask_for_path("-> PDF path: ")
        
        # check that the path is a pdf
        if not path.endswith(".pdf"):
            print("The file you uploaded is not a .pdf file. Please provide a path to a PDF.\n")
            continue

        print("(1/2) Parsing resume .pdf -> .txt")
        resume = pdf_parser(path)
        last_part_of_path = os.path.basename(path)[:-4]
        print("(2/2) Saving the resume in a dense format")
        sum_res = summarize_resume(resume)
        txt_path = f"./user_data/resumes/{last_part_of_path}.txt"
        write_to_file(txt_path, sum_res)
        print(f"\n✅ Resume '{last_part_of_path}' has been added!")
        _ = input_with_check("-> Press enter to continue:")
        return sum_res, txt_path


def import_emails_to_collection(database_tracker):
    print("\nSelect which collection you would like import emails to:")

    for i, db in enumerate(database_tracker):
        print(f"{i+1}. {db}")
    print("")
    while True:
        db_num = input_with_check("-> Selection: ")
        paste_line()
        
        if db_num in [str(i) for i in range(1, len(database_tracker)+1)]:
            db_name = database_tracker[int(db_num)-1]
            db = VDB(db_name)
            print("""
Lets import job listings from emails to add to the collection! 📂
Enter the path to the folder containing emails (.eml, .txt, .xml, .pdf)
You can also input an .olm or .csv file.
Don't worry I'll make sure to not overwrite or create any duplicates 😉
            """)
            while True:
                path = ask_for_path("-> Path: ")
                # First check if we got a folder or an .olm file, if it's an .olm file we need to extract it before parsing
                if os.path.basename(path).endswith(".olm"):
                    path = olm_handler(path)
                
                last_part_of_path = os.path.basename(path)
                if os.path.basename(path).lower().endswith(".csv"):
                    dest_folder = f"./user_data/email_folders/{last_part_of_path[:-4]}_txts"
                    parsing_problems = parse_csv(path, dest_folder)
                else:
                    dest_folder = f"./user_data/email_folders/{last_part_of_path}_txts"
                    parsing_problems = parse_email_dir(path, dest_folder)
                
                if parsing_problems:
                    print("The following emails can not be added to the collection (unsupported format):")
                    for problem in parsing_problems:
                        print(f"- {problem}\n")
                    _ = input_with_check("-> Press enter to continue or type 'exit' to exit: ")

                print("Importing emails to the collection! This takes about 10 seconds per email.")
                db.add_docs(dest_folder)
                db.write_metadata()
                print(f"\nCollection '{db.collection_name}' updated! 📂")
                _ = input_with_check("-> Press enter to continue: ")
                return db
            break
        else:
            bad_input()

def ask_for_db(database_tracker):
    print("\nYour email collections:")
    for i, db in enumerate(database_tracker):
        print(f"{i+1}. {db}")
    print("""
* Select a number from above load an existing collection.
* Type 'create' to create a new collection.
* Type 'import' to import more emails to an existing collection.
""")
    while True:
        db_num = input_with_check("-> Selection: ")

        if db_num in [str(i) for i in range(1, len(database_tracker)+1)]:
            db_name = database_tracker[int(db_num)-1]
            print(f"Loading collection '{db_name}'...")
            db = VDB(db_name)
            return db

        if db_num=="create":
            header()
            update_progress(0)
            paste_double_line()
            db = create_database(database_tracker)
            return db

        if db_num=="import":
            header()
            update_progress(0)
            paste_double_line()
            db = import_emails_to_collection(database_tracker)
            return db

        else:
            bad_input()

def ask_for_resume():
    resume_files = os.listdir("./user_data/resumes")
    resume_files = [file[:-4] for file in resume_files]
    print("\nImported resumes:")
    for i, res in enumerate(resume_files):
        print(f"{i+1}. {res}")
    print("\nSelect a number from above or type 'import' to import a new resume")
    while True:
        user_response = input_with_check("-> Selection: ")
        if user_response=="import":
            sum_res = add_resume()
            return sum_res
        if user_response in [str(i) for i in range(1, len(resume_files)+1)]:
            resume_name = resume_files[int(user_response)-1]
            txt_path = f"./user_data/resumes/{resume_name}.txt"
            sum_res = load_from_file(txt_path)
            return sum_res, txt_path
        else:
            bad_input()


def get_requirements():
    print("""
Are there any specific requirements you want to match against? 🎯

This could be things like:
- Location (adress, city or place)
- Start date of the new role
- Do you want to work from home? Remote / Hybrid / On-site?

Type 'no' if you have no specific requirements:""")
    while True:
        requirements = input_with_check("-> Requirements: ").strip().lower()

        if requirements == "no":
            print("Got it! We'll proceed without any specific requirements. 🚀")
            return None
        else:
            return requirements

def say_goodbye():
    exit_phrases = [
        "Goodbye! 👋",
        "See you later! 👋",
        "Bye! 👋",
        "Have a good one! 👋",
        "👋👋👋"
        ]
    exit_phrase = random.choice(exit_phrases)
    print(exit_phrase)
    print("\n")
    sys.exit()

def outro():
    print("\nThank you for using the CompetenceMatching tool! 🚀\n")
    sys.exit()

def update_progress(step):
    steps = ["Email collection", "Select resume", "Specify requirements"]
    current_step = f"({step+1}/3) {steps[step]}"
    len_current_step = len(current_step)
    right_padding = 79 - len_current_step
    print(f"{current_step}")

def header():
    clear_console()
    print(logo)
    #paste_double_line()

def save_metadata(db, resume_path, requirements, results):
    result_metadata ="\n".join([f"Collection: {db.collection_name}", f"Resume (txt path): {resume_path}", f"Requirements: {requirements}"])
    # create parent folder if it does not exist
    if not os.path.exists("./user_data/results"):
        os.makedirs("./user_data/results")
    write_to_file(f"./user_data/results/{time.strftime('%Y-%m-%d-%H-%M-%S')}_result.txt", result_metadata + "\n" + "-"*79 + "\n\n" + results)
    
def test_ollama():
    try:
        response = chat(
            model=model_config["test"],
            messages=[
                {"role": "user", "content": "say hi"}
            ],
            format=None
        )
        return True
    except Exception as e:
        print(f"\nError: {e}")
        print(f"Please make sure you are running ollama on your local machine!\n")
       
        return False
def check_create_userdata_dirs():
    """Check if the user_data directories exist, if not create them."""
    directories = [
        "./user_data",
        "./user_data/email_folders",
        "./user_data/resumes",
        "./user_data/results",
        "./user_data/vdbs"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

def run_TUI():
    if not test_ollama():
        sys.exit()
    check_create_userdata_dirs()
    database_tracker = load_database_tracker()
    
    # Start the program
    clear_console()
    wave_unfold_effect(logo)
    time.sleep(0.2)

    # Add database
    update_progress(0)
    paste_double_line()

    # Check if the user has a database
    # All databases are saved in the user_data/vdbs folder
    # If the folder is empty, the user does not have a database
    # If the folder is not empty, the user has at least one database
    if not database_tracker:
        first_interaction()
        paste_line()
        db = create_database(database_tracker)
    else:
        print("\nWelcome back! 👋")
        db = ask_for_db(database_tracker)

    # Add resume
    header()
    update_progress(1)
    paste_double_line()
    # Check if "./user_data/resumes" is empty
    # If it is empty, the user has not uploaded a resume
    # If it is not empty, the user has uploaded a resume
    if not os.listdir("./user_data/resumes"):
        sum_res, resume_path = add_resume()
    else:
        sum_res, resume_path = ask_for_resume()
    
    # Get the requirements
    header()
    update_progress(2)
    paste_double_line()
    requirements = get_requirements()
    
    # Run the tool
    header()
    print("Running the tool! 🚀")
    paste_double_line()
    top_lst, full_res = CompetenceMatching(requirements, sum_res, db)
    
    # Save result in the results folder
    if len(full_res) > 0:
        save_metadata(db, resume_path, requirements, top_lst+full_res)
    else:
        save_metadata(db, resume_path, requirements, "No results found")

    # Print the results
    header()
    print("Results! 🎉")
    paste_double_line()
    if full_res:
        print(top_lst)
        _ = input_with_check("--> Press enter to read the full emails or exit to exit: ", last_step=True)
        print(full_res)
    else:
        print("\nNo results found, please try one of the following: \n- Reduce your requirements\n- Expand your email collection\n")
        results = ""

    # Exit the program
    while True:
        paste_line()
        outro()
        break


if __name__ == '__main__':
    run_TUI()