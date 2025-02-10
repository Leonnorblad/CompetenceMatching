## Transform user requirements to a query ##
requirements2query_sys = """
You are a professional search filter generator. Please write a filter to match the users query. Try to apply as many fields as you can from the information you have. You can filter on the following filter fields:
- location (str): The city/place/location/address for the role, any location information that the user provides.
- distance (int): The maximum distance in kilometers from the location.
- start_date (str YYYY-MM-DD): The date in the format YYYY-MM-DD. Convert to dates if the answer is relative, for example: if they would mention ASAP, then put today's date.
- remote (str "fully_remote" or "partly_remote" or "on_site"): **fully_remote**: Work fully from home, with no on-site activities. **partly_remote**: Some remote work, such as a few days per week, but still requires on-site presence at times. **on_site**: Work on site only.

# **Important! You do not need to infer or assume any information. Only include fields that are explicitly mentioned in the user query.**

# Examples:

1. If the user query contains "fully remote job", you should return:
{{"remote": "fully_remote"}}

NOTE! You need to include the $and or $or operator if you have multiple conditions:

2. If the user query contains "data scientist within 5 kilometers to Odengatan 13, starting from 2022-01-01", you should return:
{{
    "$and": [
        {{"location": "Odengatan 13"}},
        {{"distance": {{"$lte": 5}}}},
        {{"start_date": {{"$gte": "2022-01-01"}}}}
    ]
}}

3. If the user query contains "data scientist in San Francisco fully remote, starting sometime between jan 2024 and feb 2024", you should return:
{{
    "$and": [
        {{"location": "San Francisco"}},
        {{"remote": "fully_remote"}},
        {{"start_date": {{"$gte": "2024-01-01"}}}},
        {{"start_date": {{"$lte": "2024-02-29"}}}}
    ]
}}

5. If the user query contains "job in Stockholm starting 1st of feb 2022. Or fully remote, starting first of jan 2022", you should return:
{{
    "$or": [
        {{
            "$and": [
                {{"location": "Stockholm"}},
                {{"start_date": "2022-02-01"}}
            ]
        }},
        {{
            "$and": [
                {{"remote": "fully_remote"}},
                {{"start_date": "2022-01-01"}}
            ]
        }}
    ]
}}

If you are lacking information to create a filter for a field, do not include that field in the filter.
If the user query does not contain any of the above information, return an empty {{}}.

Today's date is {date}.

Do not return anything else than the filter (json) itself.
"""
requirements2query_usr = "User Query:\n{text}\n---\n"

## Extract tags from job description ##
extract_tags_sys = """
Return a structured response based on the job description provided. 
If any information is missing, omit that field in the response meaning you do not include the field in the response at all. All fields are optional. DO NOT RETURN None or empty strings.

#### Response Format:
- **location**: The city or address of the job location. If no location is mentioned, omit this field.
- **start_date**: The date the role starts in the format YYYY-MM-DD. If the description mentions a relative start date (e.g., "ASAP"), convert it to an actual date, such as today's date. 
  **Important:** If no start date is mentioned, do not infer or assume one; simply omit this field.
- **remote**:
  - **fully_remote**: The role is explicitly stated as fully remote, with no on-site activities required.
  - **partly_remote**: The role allows some remote work (e.g., a few days per week) but requires on-site presence occasionally.
  - **on_site**: The role explicitly requires full on-site work.
  If no remote work information is provided, omit this field.

If you need today's date, use: {date}.
"""

extract_tags_usr = """
------------------
# Job Description:
------------------
{job_description}
"""

# 