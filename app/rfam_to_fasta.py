"""
Download seed alignment from Rfam, remove pseudoknots, and save as FASTA.
"""

from Bio import AlignIO
import datetime
from io import StringIO
import requests
import os
import sys

def download_rfam_alignment(rfam_id):
    """
    Download a Stockholm alignment from Rfam given an Rfam ID.
    Returns the filename of the downloaded file.
    """
    stockholm_filename = f"{rfam_id}.sto"

    print("%s Looking for %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),stockholm_filename))

    if os.path.exists(stockholm_filename):
        with open(stockholm_filename, "r") as file:
            stockholm_text = file.read()
        return stockholm_text
    else:
        url = f"https://rfam.org/family/{rfam_id}/alignment/stockholm"

        print("%s Trying to open %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),url))

        response = requests.get(url)

        print("%s Considering the response from %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),url))

        if response.status_code == 200:
            stockholm_text = response.text
            # with open(stockholm_filename, "w") as file:
            #     file.write(response.text)
            # dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # print(f"{dt} Downloaded Rfam alignment for {rfam_id} and saved to {stockholm_filename}")
            return stockholm_text
        else:
            print(f"Unable to download alignment for {rfam_id}. Status code: {response.status_code}")
            return ""
            return f"Unable to download alignment for {rfam_id}. Status code: {response.status_code}"
            raise Exception(f"Failed to download alignment for {rfam_id}. Status code: {response.status_code}")

# def remove_pseudoknots(stockholm_alignment):
#     """
#     Remove pseudoknots from the consensus structure annotation in a Stockholm alignment.
#     Any pseudoknot characters in SS_cons (e.g., '{', '}', '[', ']') will be replaced with '.'.
#     """
#     if "SS_cons" in stockholm_alignment.column_annotations:
#         ss_cons = stockholm_alignment.column_annotations["SS_cons"]
#         cleaned_ss_cons = ss_cons.replace('{', '.').replace('}', '.').replace('[', '.').replace(']', '.')
#         stockholm_alignment.column_annotations["SS_cons"] = cleaned_ss_cons
#     return stockholm_alignment

def convert_to_fasta(stockholm_text, rfam_id):
    """
    Convert the modified Stockholm alignment to FASTA format and save it.
    """

    title = rfam_id

    # loop over lines in the Stockholm text and get the DE line as the title
    lines = stockholm_text.split("\n")
    for line in lines:
        if line.startswith("#=GF DE "):
            title += " " + line[8:].strip()
            break

    # Use StringIO to convert the string to a file-like object
    stockholm_handle = StringIO(stockholm_text)

    # Read the alignment from the StringIO object
    alignment = AlignIO.read(stockholm_handle, "stockholm")

    # print(alignment)

    # for record in alignment:
    #     # Access the "DE" field from the "dbxref" annotation
    #     de_field = record.annotations.get("dbxref", [])
    #     print(f"Sequence ID: {record.id}, DE field: {de_field}")

    # print(dir(alignment))
    # print(dir(alignment.annotations))
    # print(dir(alignment._annotations))
    # print(alignment.annotations.get("ID"))
    # print(alignment.annotations.get("AC"))

    # Remove pseudoknots
    # print("%s Removing pseudoknots" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    # alignment = remove_pseudoknots(alignment)

    # Write the secondary structure
    if "secondary_structure" in alignment.column_annotations:
        ss = alignment.column_annotations["secondary_structure"]
        # print('Initial secondary structure:')
        # print(ss)
        ss = ss.replace('{', '.').replace('}', '.').replace('[', '.').replace(']', '.')
        ss = ss.replace('a', '.').replace('A', '.')
        ss = ss.replace('b', '.').replace('B', '.')
        ss = ss.replace('c', '.').replace('C', '.')
        ss = ss.replace('d', '.').replace('D', '.')
        ss = ss.replace('e', '.').replace('E', '.')
        # print('Pseudoknots removed:')
        # print(ss)
        ss = ss.replace('<', '(').replace('>', ')')
        # print('Parentheses instead of brackets:')
        # print(ss)
        ss = ss.replace(':', '.').replace('-', '.').replace('_', '.').replace(',', '.')
        # print('Dots for gaps:')
        print(ss)

    else:
        # we can't get anywhere without the secondary structure
        print("%s Did not find an SS_cons line" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        return None

    # Define output FASTA filename based on Rfam ID
    # fasta_filename = f"{rfam_id}.fasta"
    # print("%s Writing secondary structure" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    # with open(fasta_filename, "w") as fasta_output:
    #     fasta_output.write(f"{ss}\n")
    # print("%s Writing alignment in fasta format" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    # with open(fasta_filename, "a") as fasta_output:
    #     AlignIO.write(alignment, fasta_output, "fasta-2line")

    output_handle = StringIO()
    AlignIO.write(alignment, output_handle, "fasta-2line")

    # Retrieve the alignment as a string
    fasta_text = ss + "\n" + output_handle.getvalue()

    # print(f"Converted alignment to FASTA format and saved to {fasta_filename}")

    return fasta_text, title

def process_rfam_alignment(rfam_id):
    """
    Main function to download the alignment, process it, save it as FASTA, and delete the Stockholm file.
    """
    print("%s Downloading Stockholm file" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    stockholm_text = download_rfam_alignment(rfam_id)

    if not stockholm_text:
        return "", ""

    print("%s Converting to fasta" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    fasta_text, title = convert_to_fasta(stockholm_text, rfam_id)

    # Remove the Stockholm file after conversion
    # os.remove(stockholm_filename)
    # print(f"Deleted temporary Stockholm file: {stockholm_filename}")

    if not fasta_text:
        return "", ""

    # with open(fasta_filename, "r") as file:
    #     fasta_data = file.read()

    # Remove the fasta file now that we read it
    # os.remove(fasta_filename)

    # print(f"Process complete. FASTA alignment saved as {fasta_filename}")

    return fasta_text, title

if __name__ == "__main__":

    # Parse command line arguments
    argv = sys.argv

    if len(argv) != 2:
        rfam_id = "RF00005"  # Example Rfam ID for 5S ribosomal RNA
    else:
        rfam_id = argv[1]

    # print timestamp and message
    print("%s Processing Rfam alignment for %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rfam_id))
    fasta_data,title = process_rfam_alignment(rfam_id)
    print(" ")
    print(fasta_data[0:1000])
    print(title)
