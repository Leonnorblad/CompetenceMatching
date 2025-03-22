import os
from email import policy
from email.parser import BytesParser
from docling.document_converter import DocumentConverter
import xml.etree.ElementTree as ET
import re
import pandas as pd
from bs4 import BeautifulSoup
import zipfile
from scr.utils import write_to_file, detect_encoding

def parse_mail_body_eml(eml_file_path):
    try:
        body = ""
        with open(eml_file_path, "rb") as file:
            email_message = BytesParser(policy=policy.default).parse(file)
            if email_message.is_multipart():
                for part in email_message.iter_parts():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_content()
                        break
            else:
                body = email_message.get_body(preferencelist=("plain")).get_content()
        return body
    except Exception as e:
        print(f"Error parsing email {eml_file_path}: {e}")
        return None

def parse_mail_body_xml(xml_file_path):
    try:
        body = ""
        with open(xml_file_path, "r", encoding="utf-8") as file:
            xml_data = file.read()
            # Parse the XML data
            root = ET.fromstring(xml_data)

            # Extract the body
            body_html = root.find(".//OPFMessageCopyBody").text if root.find(".//OPFMessageCopyBody") is not None else None
            
            # Clean HTML tags if body exists
            body = None
            if body_html:
                soup = BeautifulSoup(body_html, "html.parser")
                body = soup.get_text(separator="\n")

            # Extract the subject
            subject = root.find(".//OPFMessageCopySubject").text if root.find(".//OPFMessageCopySubject") is not None else None

            # Extract the sender's email
            sender_email_element = root.find(".//OPFMessageCopySenderAddress/emailAddress")
            sender_email = sender_email_element.attrib.get("OPFContactEmailAddressAddress") if sender_email_element is not None else None

            mail_body = f"Subject: {subject}\n" if subject else ""
            mail_body += f"From: {sender_email}\n" if sender_email else ""
            mail_body += f"{body}\n" if body else ""

            return mail_body

    except ET.ParseError as e:
        return None

def extract_olm(file_path, extract_to="./user_data/olm_data"):
    # Extract the .olm file
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


def parse_email_dir(source_dir, target_dir):
    failed_emails = []
    any_error = False
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)

    for root, _, files in os.walk(source_dir):
        for file in files:
            try:
                if file.endswith(".eml"):
                    email_body = parse_mail_body_eml(os.path.join(root, file))
                    if len(email_body) > 0:
                        write_to_file(os.path.join(target_dir, file.replace(".eml", "") + ".txt"), email_body)
                    else:
                        failed_emails.append(file)
                        any_error = True

                if file.endswith(".xml"):
                    email_body = parse_mail_body_xml(os.path.join(root, file))
                    if len(email_body) > 0:
                        write_to_file(os.path.join(target_dir, file.replace(".xml", "") + ".txt"), email_body)
                    else:
                        failed_emails.append(file)
                        any_error = True

                if file.endswith(".pdf"):
                    email_body = pdf_parser(os.path.join(root, file))
                    if len(email_body) > 0:
                        write_to_file(os.path.join(target_dir, file.replace(".pdf", "") + ".txt"), email_body)
                    else:
                        failed_emails.append(file)
                        any_error = True
                
                if file.endswith(".txt"):
                    with open(os.path.join(root, file), "r") as f:
                        email_body = f.read()
                        if len(email_body) > 0:
                            write_to_file(os.path.join(target_dir, file), email_body)
                        else:
                            failed_emails.append(file)
                            any_error = True

            except Exception as e:
                failed_emails.append(file)
                any_error = True
    if any_error:
        return failed_emails
    else:
        return False

def parse_csv(csv_path, dest_folder):
    """
    # input: one csv with all emails
    # Outout: a folder with txt files with the emails
    """
    encoding = detect_encoding(csv_path)
    df = pd.read_csv(csv_path, encoding=encoding)
    # Get the 0'th index column
    headers_lst = list(df.keys())
    body_col_name, sender_col_name, subject_col_name = headers_lst[1], headers_lst[3], headers_lst[0]

    # Create the destination folder if it doesn't exist
    os.makedirs(dest_folder, exist_ok=True)
    # Iterate df and create txt files
    parsring_problem_lst = []
    for idx, row in df.iterrows():
        try:
            body, sender_email, subject = row[body_col_name], row[sender_col_name], row[subject_col_name]
            mail_body = f"Subject: {subject}\n"
            mail_body += f"From: {sender_email}\n"
            mail_body += f"{body}\n"
            # Create a txt file for each email
            write_to_file(f"{dest_folder}/{idx}.txt", mail_body)
        except Exception as e:
            parsring_problem_lst.append(idx)
            continue
    if len(parsring_problem_lst) > 0:
        return parsring_problem_lst
    else:
        return False

def pdf_parser(file_path):
    converter = DocumentConverter()
    result = converter.convert(file_path)
    markdown_result = result.document.export_to_markdown()
    return markdown_result