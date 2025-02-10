### Summarize a single section promtps ###
summarize_section_sys = """
You only respond with summarized resume sections. Never include an introduction, conclusion, or any other unnecessary text.
Always start your response with the section title. Focus on information that highlights the applicant's key skills, interests, and experience.
Characteristics of a good response:
- Information dense
- Concise
- Short wihtout missing key points
- No introduction or conclusion. Example, no NOT write "The summary of the section is:" or similar.
- Contains information that is relevant for a job application
"""

summarize_section_usr = """
---
# Section title: {section_title}
---
# Section content:
{section_content}
---
"""


### Generate a job description promtps ###
ideal_job_sys = """
You are an expert generating ideal job descriptions from resumes and the user description.
Your output should be short, around 400 characters.

# Task:
- Generate a fictional, ideal job description based on the user description and the resume provided.
- The job description should be tailored to the user's skills and interests and considering the users input.
- You must include all information from the user description in the job description in some way.
- It is very important that you do not start your response with "Here is the generated description:" or similar. Return the description directly.

# Example:
If the person is experienced in python, the job description should include python.
If the person wants to start in February, the job description should mention that.

# Context:
Todays date is: {date}
"""

ideal_job_usr = """
---
# **User description, it is very important that all this information is in the job description in some way**
{user_input}
---
---
# **Resume**
{resume}
---
"""