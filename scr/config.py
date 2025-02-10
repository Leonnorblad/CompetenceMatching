VERSION =  "0.1.0"
DATE = "2025-02-09"

# Number of ads for each chunk of ideal job ad
NUM_RES_PER_CHUNK = 10

# Showing the top 10 results to the user.
MAX_RES_USER = 10 
# For example:
# If MAX_RES_USER is set to 3 and the result is:
# 1. Chunk 1 - job listing A
# 2. Chunk 1 - job listing B
# 3. Chunk 2 - job listing B
# 4. Chunk 1 - job listing C
# 5. Chunk 1 - job listing D

# We return:
# 1. A
# 2. B
# 3. C

# Ollama models to use
model_config = {
    # Test to see if the model is working - runs when the program starts
    "test": "llama3.1:8b",
    
    # Summarizes resumes
    "summary": "llama3.1:8b",

    # Writes the HyDe job description
    "ideal_job_description": "llama3.1:8b",

    # Extract the location / start date / remote tags from each job listing
    "extact_tags": "llama3.1:8b",

    # Writer of the db query
    "requirements2query": "llama3.1:8b"
    }