from typing import Any, Dict, Optional
import requests
import re
from pygitrefer.const import SKIPWORDS
import string
from pykakasi import kakasi
kks = kakasi()


def get_reference_data(doi: str, agency: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve reference data from the appropriate API based on the agency.

    Args:
        doi (str): DOI of the reference.
        agency (str): Agency responsible for the DOI.

    Returns:
        Optional[Dict[str, Any]]: Reference data if found, otherwise None.
    """
    if agency == "crossref":
        return _get_reference_data_from_crossref(doi)
    elif agency == "datacite":
        return _get_reference_data_from_datacite(doi)
    else:
        print(f"Agency not supported: {agency}")
        return None


def _get_reference_data_from_crossref(doi: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve reference data from CrossRef API.

    Args:
        doi (str): DOI of the reference.

    Returns:
        Optional[Dict[str, Any]]: Reference data if found, otherwise None.
    """
    url = f"https://api.crossref.org/works/{doi}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()["message"]
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from CrossRef for DOI {doi}: {e}")
    except Exception as e:
        print(f"Failed to retrieve data from CrossRef for DOI {doi}: {e}")
    return None


def _get_reference_data_from_datacite(doi: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve reference data from DataCite API.

    Args:
        doi (str): DOI of the reference.

    Returns:
        Optional[Dict[str, Any]]: Reference data if found, otherwise None.
    """
    url = f"https://api.datacite.org/dois/{doi}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()["data"]["attributes"]
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from DataCite for DOI {doi}: {e}")
    except Exception as e:
        print(f"Failed to retrieve data from DataCite for DOI {doi}: {e}")
    return None


def validate_doi(doi: str) -> bool:
    """
    Validate the DOI format.

    Args:
        doi (str): DOI to validate.

    Returns:
        bool: True if the DOI is valid, False otherwise.
    """
    return re.match(r"^10.\d{4,9}/[-._;()/:a-zA-Z0-9]+$", doi) is not None


def sanitize_filename(filename: str) -> str:
    """
    Generate a safe filename by replacing invalid characters with underscores.

    Args:
        filename (str): Original filename or ID.

    Returns:
        str: Safe filename.
    """
    return re.sub(r"[\/\\?%*:|\"<>]", "_", filename)


def get_agency(doi: str) -> Optional[str]:
    """
    Retrieve the agency responsible for the DOI from CrossRef API.

    Args:
        doi (str): DOI of the reference.

    Returns:
        Optional[str]: Agency ID if found, otherwise None.
    """
    url = f"https://api.crossref.org/works/{doi}/agency"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        agency = data["message"]["agency"]["id"]
        return agency

    except requests.exceptions.RequestException as e:
        print(f"Error fetching agency for DOI {doi}: {e}")
    except Exception as e:
        print(f"Failed to retrieve agency for DOI {doi}: {e}")
    return None


def get_pdf_link(doi: str, data: Dict[str, Any], agency: str) -> Optional[str]:
    """
    Extract PDF link from reference data.

    Args:
        doi (str): DOI of the reference.
        data (Dict[str, Any]): Reference data.
        agency (str): Agency responsible for the DOI.

    Returns:
        Optional[str]: PDF link if found, otherwise None.
    """
    if agency == "crossref":
        return _get_pdf_link_from_crossref(doi, data)
    elif agency == "datacite":
        return _get_pdf_link_from_datacite(doi, data)
    else:
        print(f"Agency not supported: {agency}")
        return None


def _get_pdf_link_from_crossref(doi: str, data: Dict[str, Any]) -> Optional[str]:
    """
    Extract PDF link from CrossRef data.

    Args:
        doi (str): DOI of the reference.
        data (Dict[str, Any]): CrossRef data.

    Returns:
        Optional[str]: PDF link if found, otherwise None.
    """
    try:
        if "link" in data:
            for link in data["link"]:
                # Check if content-type is unspecified or application/pdf
                if (
                    link.get("content-type") == "unspecified"
                    or link.get("content-type") == "application/pdf"
                ):
                    potential_pdf_link = link.get("URL")
                    return potential_pdf_link
                else:
                    print(f"No PDF link found for DOI {doi}")
                    return None

    except Exception as e:
        print(f"Failed to get PDF link from CrossRef data for DOI {doi}: {e}")
        return None


def _get_pdf_link_from_datacite(doi: str, data: Dict[str, Any]) -> Optional[str]:
    """
    Extract PDF link from DataCite data.

    Args:
        doi (str): DOI of the reference.
        data (Dict[str, Any]): DataCite data.

    Returns:
        Optional[str]: PDF link if found, otherwise None.
    """
    try:
        # Prioritize contentUrl if it's a PDF link
        if (
            "contentUrl" in data
            and data["contentUrl"]
            and data["contentUrl"].endswith(".pdf")
        ):
            return data["contentUrl"]
        # Check if url can be converted to an arXiv PDF link
        elif "url" in data and data["url"]:
            arxiv_match = re.match(r"https://arxiv.org/abs/(\d+\.\d+)", data["url"])
            if arxiv_match:
                return f"https://arxiv.org/pdf/{arxiv_match.group(1)}"
        else:
            print(f"No PDF link found for DOI {doi}")
            return None

    except Exception as e:
        print(f"Failed to get PDF link from DataCite data for DOI {doi}: {e}")
        return None

def convert_jp_to_en(jp_text: str) -> str:
    """
    Convert Japanese text to English using pykakasi.

    Args:
        jp_text (str): Japanese text to convert.

    Returns:
        str: Converted English text.
    """
    result = kks.convert(jp_text)
    converted_text = "".join([item["hepburn"] for item in result])
    return converted_text


def make_citekey(family_name: str, year: str, title: str) -> str:
    """
    Automatically generates a citekey for the reference.

    Args:
        family_name (str): The last name of the first author.
        title (str): The title of the reference.
        year (str): The publication year of the reference.
    """

    # from [extensions.zotero.translators.better-bibtex.skipWords], zotero.
    def convert_family_name(family_name):
        family_name = family_name.replace("_", "")
        return convert_jp_to_en(family_name).lower().replace(" ", "")

    def up(str_):
        if len(str_) < 2:
            return str_.upper()
        if str_[0] == " ":
            return " " + str_[1].upper() + str_[2:]
        return str_[0].upper() + str_[1:]

    def simplify(title):
        for key in ["/", "‐", "—"]:  # hyphen and dash, not minus (-).
            title = title.replace(key, " ")
        title = " " + convert_jp_to_en(title) + " "
        for key in ["'s", "'t", "'S", "'T"]:
            title = title.replace(key, "")
        title = title.translate(str.maketrans("", "", string.punctuation))
        for key in SKIPWORDS:
            key = " " + key + " "
            title = title.replace(key, " ")
            title = title.replace(key.upper(), " ").replace(up(key), " ")
        return title

    def make_shorttitle(title, n_title=1):
        while True:
            len_before = len(title.replace(" ", ""))
            title = simplify(title)
            if len_before == len(title.replace(" ", "")):
                break

        title = [up(t) for t in title.split(" ") if t]
        if len(title) < n_title:
            return "".join(title)
        return "".join(title[:n_title]).lower()

    citekey = "".join([convert_family_name(family_name), year, make_shorttitle(title)])

    return citekey


if __name__ == "__main__":
    """
    For testing
    """
    doi = "10.1007/978-3-319-10590-1_53"
    print(validate_doi(doi))
    agency = get_agency(doi)
    data = get_reference_data(doi, agency)
    pdf_link = get_pdf_link(doi, data, agency)
    print(pdf_link)

    filename = doi
    print(sanitize_filename(filename))

    doi = "10.48550/arxiv.2401.17231"
    print(validate_doi(doi))
    agency = get_agency(doi)
    print(agency)
    data = get_reference_data(doi, agency)
    pdf_link = get_pdf_link(doi, data, agency)
    print(pdf_link)

    filename = doi
    print(sanitize_filename(filename))
