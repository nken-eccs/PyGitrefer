from typing import Optional, Tuple, Dict, List, Any
from pygitrefer.utils import (
    get_reference_data,
    get_pdf_link,
    validate_doi,
    sanitize_filename,
    get_agency,
    make_citekey,
)
from pygitrefer.const import CROSSREF_TO_BIB
from pygitrefer.git_api import GitHubAPI
import requests
import json
import os
from datetime import datetime
from rich import print


class ReferenceManager:
    """
    Manages references data and interacts with the GitHub API.
    """

    def __init__(self, git_api: GitHubAPI, dir_name: str = "references"):
        """
        Initializes the ReferenceManager.

        Args:
            git_api (GitHubAPI): An instance of the GitHubAPI class.
            dir_name (str, optional): The directory name for storing references data. Defaults to "references".
        """
        self.git_api = git_api
        self.dir = dir_name
        self.data_dir = f"{self.dir}/data"
        self.raw_dir = f"{self.dir}/raw"
        self.references_file = f"{self.dir}/references.json"
        self.references: Dict[str, Any] = self._initialize_references()

    def _initialize_references(self) -> Dict[str, Any]:
        """
        Initializes the references data from the references.json file. If the file does not exist, it is created.

        Returns:
            Dict[str, Any]: The references data.
        """
        try:
            references = self.git_api._get_file_content(
                self.references_file, required=False
            )
            if references:
                return json.loads(references)
            else:
                self.git_api._create_file(
                    self.references_file,
                    "Initialize references file",
                    json.dumps({}, indent=2),
                )
                return {}

        except Exception as e:
            print(f"Failed to initialize references file: {e}")
            raise

    def validate_reference_data(self, reference_data: Dict[str, Any]) -> bool:
        """
        Validates the reference data to ensure all required keys are present.

        Args:
            reference_data (Dict[str, Any]): The reference data.

        Returns:
            bool: True if the reference data is valid, otherwise False.
        """
        required_keys = [
            "is_doi",
            "entry_type",
            "citekey",
            "authors",
            "title",
            "year",
            "month",
            "edition",
            "journal",
            "volume",
            "issue",
            "firstpage",
            "lastpage",
            "publisher",
            "isbn",
            "issn",
            "abstract",
            "keywords",
            "url",
            "tags",
            "files",
            "created_at",
            "updated_at",
        ]
        for key in required_keys:
            if key not in reference_data:
                print(f"{key} key is missing in reference data.")
                return False
        return True

    def _save_references(self) -> None:
        """
        Saves the current references data to the references.json file.
        """
        try:
            self.git_api._update_file(
                self.references_file,
                "Update references file",
                json.dumps(self.references, indent=2),
            )

        except Exception as e:
            print(f"Failed to save references file: {e}")
            raise

    def add_reference_from_doi(self, doi: str, download_pdf: bool = True) -> None:
        """
        Adds a new reference from a DOI.

        Args:
            doi (str): The DOI of the reference.
            download_pdf (bool, optional): Whether to download the PDF file if available. Defaults to True.
        """
        if doi in self.references:
            print(f"Reference already exists for DOI: [bold blue]{doi}[/]")
            return

        if not validate_doi(doi):
            print(f"Invalid DOI: [bold blue]{doi}[/]")
            return

        agency = get_agency(doi)
        if not agency:
            print(
                f"Failed to retrieve agency for DOI: [bold blue]{doi}[/]. Aborting reference addition."
            )
            return

        data = get_reference_data(doi, agency)
        if not data:
            print(
                f"Failed to retrieve reference data for DOI: [bold blue]{doi}[/]. Aborting reference addition."
            )
            return

        safe_filename = sanitize_filename(doi)
        self.git_api._create_file(
            f"{self.raw_dir}/{safe_filename}.json",
            f"Add raw data for {doi}",
            json.dumps(data, indent=2),
        )

        try:
            if agency == "crossref":
                entry_type = data.get("type", "") if data.get("type") else ""
                authors = [
                    {
                        "family": author.get("family", ""),
                        "given": author.get("given", ""),
                    }
                    for author in data.get("author", [])
                ]
                title = data.get("title", [""])[0] if "title" in data else ""
                if data.get("published-print", data.get("published-online", {})).get(
                    "date-parts", [[None]]
                )[0]:
                    data_parts = data.get(
                        "published-print", data.get("published-online", {})
                    ).get("date-parts", [[None]])[0]
                    if len(data_parts) == 1:
                        year = str(data_parts[0])
                        month = ""
                    elif len(data_parts) > 1:
                        year = str(data_parts[0])
                        month = str(data_parts[1])
                    else:
                        year = ""
                        month = ""
                else:
                    year = ""
                    month = ""
                edition = (
                    data.get("edition-number") if data.get("edition-number") else ""
                )
                journal = (
                    data.get("container-title", [""])[0]
                    if data.get("container-title", [""])
                    and len(data.get("container-title", [""])) > 0
                    else ""
                )
                volume = str(data.get("volume")) if data.get("volume") else ""
                issue = str(data.get("issue")) if data.get("issue") else ""
                firstpage = data.get("page").split("-")[0] if data.get("page") else ""
                lastpage = data.get("page").split("-")[-1] if data.get("page") else ""
                publisher = data.get("publisher") if data.get("publisher") else ""
                isbn = data.get("ISBN") if data.get("ISBN") else []
                issn = data.get("ISSN") if data.get("ISSN") else []
                abstract = data.get("abstract") if data.get("abstract") else ""
                keywords = ", ".join(data.get("subject", []))
                url = (
                    data.get("resource").get("primary").get("URL")
                    if data.get("resource").get("primary").get("URL")
                    else f"https://doi.org/{doi}"
                )
            elif agency == "datacite":
                entry_type = (
                    data.get("types", {}).get("bibtex", "")
                    if data.get("types", {}).get("bibtex")
                    else ""
                )
                authors = [
                    {
                        "family": creator.get("familyName", ""),
                        "given": creator.get("givenName", ""),
                    }
                    for creator in data.get("creators", [])
                ]
                title = (
                    data.get("titles", [{}])[0].get("title", "")
                    if "titles" in data
                    else ""
                )
                year = (
                    str(data.get("publicationYear"))
                    if data.get("publicationYear")
                    else ""
                )
                month = ""  # DataCite does not provide publication month information
                edition = ""  # DataCite does not provide edition information
                journal = ""  # DataCite does not provide journal information
                volume = str(data.get("volume")) if data.get("volume") else ""
                issue = str(data.get("issue")) if data.get("issue") else ""
                firstpage = data.get("page").split("-")[0] if data.get("page") else ""
                lastpage = data.get("page").split("-")[-1] if data.get("page") else ""
                publisher = data.get("publisher") if data.get("publisher") else ""
                isbn = [] # DataCite does not provide ISBN information
                issn = [] # DataCite does not provide ISSN information
                abstract = (
                    data.get("descriptions", [{}])[0].get("description", "")
                    if "descriptions" in data
                    else ""
                )
                keywords = ", ".join(
                    [subject["subject"] for subject in data.get("subjects", [])]
                )
                url = data.get("url") if data.get("url") else f"https://doi.org/{doi}"
        except KeyError as key_err:
            print(
                f"Key error occurred while processing reference data for DOI: [bold blue]{doi}[/]: {key_err}"
            )
            raise

        files = []
        if download_pdf:
            pdf_link = get_pdf_link(doi, data, agency)
            if pdf_link:
                file_name = self._download_pdf(doi, pdf_link)
                if file_name:
                    files.append(file_name)
            else:
                print(f"PDF not detected for DOI: [bold blue]{doi}[/]")
                print(f"Please add the PDF manually to the reference if you need to.")

        if authors[0]["family"] and year and title:
            citekey = make_citekey(
                authors[0]["family"], year, title
            )
        else:
            citekey = f"Gitrefer:{sanitize_filename(doi)}"
        new_reference_data = {
            "is_doi": True,
            "entry_type": entry_type,
            "citekey": citekey,
            "authors": authors,
            "title": title,
            "year": year,
            "month": month,
            "edition": edition,
            "journal": journal,
            "volume": volume,
            "issue": issue,
            "firstpage": firstpage,
            "lastpage": lastpage,
            "publisher": publisher,
            "isbn": isbn,
            "issn": issn,
            "abstract": abstract,
            "keywords": keywords,
            "url": url,
            "tags": [],
            "files": files,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        self.references[doi] = new_reference_data
        self._save_references()
        print(f"Reference added successfully for DOI: [bold blue]{doi}[/]")

    def _download_pdf(self, doi: str, pdf_link: str) -> Optional[str]:
        """
        Downloads the PDF file from the given link and saves it to the data directory.

        Args:
            doi (str): The DOI of the reference.
            pdf_link (str): The URL of the PDF file.

        Returns:
            Optional[str]: The filename of the downloaded PDF if successful, otherwise None.
        """
        safe_filename = sanitize_filename(doi)
        pdf_file_name = pdf_link.split("/")[-1]
        if not pdf_file_name.endswith(".pdf"):
            pdf_file_name = f"{pdf_file_name}.pdf"
        try:
            print(f"Downloading PDF for DOI [bold blue]{doi}[/]: {pdf_file_name}...")
            response = requests.get(pdf_link)
            response.raise_for_status()
            self.git_api._create_file(
                f"{self.dir}/data/{safe_filename}/{pdf_file_name}",
                f"Download PDF for DOI {doi}",
                response.content,
                is_binary=True,
            )
            print(f"Downloaded PDF for DOI [bold blue]{doi}[/]: {pdf_file_name}")
            return pdf_file_name

        except Exception as e:
            print(f"Failed to download PDF for DOI [bold blue]{doi}[/]: {e}")
            print(f"Please add the PDF manually to the reference if you need to.")
            return None

    def add_reference_manually(self, ID: str, reference_data: Dict[str, Any]) -> None:
        """
        Adds a new reference manually.

        Args:
            ID (str): The ID of the reference.
            reference_data (Dict[str, Any]): The reference data.
        """
        if ID in self.references:
            print(f"Reference already exists for ID: [bold blue]{ID}[/]")
            return

        if validate_doi(ID):
            print("ID cannot be a DOI or DOI-like string.")
            return

        citekey = reference_data.get("citekey", "")
        authors = reference_data.get("authors", [])
        title = reference_data.get("title", "")
        year = reference_data.get("year", "")
        if not citekey:
            if authors[0]["family"] and year and title:
                citekey = make_citekey(
                    authors[0]["family"], year, title
                )
            else:
                citekey = f"Gitrefer:{sanitize_filename(ID)}"
        new_reference_data = {
            "is_doi": False,
            "entry_type": reference_data.get("entry_type", ""),
            "citekey": citekey,
            "authors": authors,
            "title": title,
            "year": year,
            "month": reference_data.get("month", ""),
            "edition": reference_data.get("edition", ""),
            "journal": reference_data.get("journal", ""),
            "volume": reference_data.get("volume", ""),
            "issue": reference_data.get("issue", ""),
            "firstpage": reference_data.get("firstpage", ""),
            "lastpage": reference_data.get("lastpage", ""),
            "publisher": reference_data.get("publisher", ""),
            "isbn": reference_data.get("isbn", []),
            "issn": reference_data.get("issn", []),
            "abstract": reference_data.get("abstract", ""),
            "keywords": reference_data.get("keywords", ""),
            "url": reference_data.get("url", ""),
            "tags": [],
            "files": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        self.references[ID] = new_reference_data
        self._save_references()
        print(f"Reference added successfully for ID: [bold blue]{ID}[/]")

    def find_new_references(self) -> List[Tuple[str, List[str], int]]:
        """
        Finds new references from the raw JSON files in the GitHub repository and displays them in a table.
        Compares DOIs with existing references to identify new ones.

        Returns:
            List[Tuple[str, List[str], int]]: List of new references with DOI, unstructured info, and count.
        """
        registered_dois = [
            ref["DOI"] for ref in self.references.values() if "DOI" in ref
        ]
        new_references = []
        try:
            contents = self.git_api._get_directory_contents(self.raw_dir)
            doi_data = {}
            no_doi_data = []
            for content in contents:
                if content["type"] == "file" and content["name"].endswith(".json"):
                    data = json.loads(self.git_api._get_file_content(content["path"]))
                    if "reference" in data:
                        for ref in data["reference"]:
                            doi = ref.get("DOI")
                            unstructured_info = []
                            for key, value in ref.items():
                                if key not in [
                                    "DOI",
                                    "key",
                                    "doi-asserted-by",
                                    "first-page",
                                    "volume",
                                ]:
                                    unstructured_info.append(f"{key}: {value}")

                            if doi:
                                if doi not in registered_dois:
                                    if doi in doi_data:
                                        # DOI found in multiple files, compare info
                                        if len(unstructured_info) > len(
                                            doi_data[doi][0]
                                        ):
                                            doi_data[doi] = (
                                                unstructured_info,
                                                doi_data[doi][1] + 1,
                                            )
                                        else:
                                            doi_data[doi] = (
                                                doi_data[doi][0],
                                                doi_data[doi][1] + 1,
                                            )
                                    else:
                                        doi_data[doi] = (unstructured_info, 1)
                            else:
                                # No DOI, display without comparison
                                no_doi_data.append(("N/A", unstructured_info, 1))
            # Sort by count in descending order
            doi_data = dict(
                sorted(doi_data.items(), key=lambda x: x[1][1], reverse=True)
            )

        except Exception as e:
            print(f"An error occurred while fetching files from the raw directory: {e}")
            raise

        for doi, (info, count) in doi_data.items():
            new_references.append((doi, info, count))
        new_references.extend(no_doi_data)
        if not new_references:
            print("No new references found.")
            return []
        return new_references

    def get_reference(self, ID: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a specific reference by ID.

        Args:
            ID (str): The ID of the reference.

        Returns:
            Optional[Dict[str, Any]]: The reference data if found, otherwise None.
        """
        if ID not in self.references:
            print(f"Reference not found for ID: [bold blue]{ID}[/]")
            return None
        return self.references.get(ID, None)

    def get_raw_data(self, ID: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the raw data of a reference by ID.

        Args:
            ID (str): The ID of the reference.

        Returns:
            Optional[Dict[str, Any]]: The raw data if found, otherwise None.
        """
        safe_filename = sanitize_filename(ID)
        raw_file_path = f"{self.dir}/raw/{safe_filename}.json"
        try:
            raw_data = self.git_api._get_file_content(raw_file_path)
            return json.loads(raw_data)

        except Exception as e:
            print(f"Failed to retrieve raw data for ID: [bold blue]{ID}[/]: {e}")
            return None

    def update_reference(
        self, old_ID: str, new_ID: str, new_reference_data: Dict[str, Any] = None
    ) -> None:
        """
        Updates an existing reference.

        Args:
            old_ID (str): The old ID of the reference.
            new_ID (str): The new ID of the reference.
            new_reference_data (Dict[str, Any]): The new reference data.
        """
        if old_ID not in self.references:
            print(f"Reference not found for ID: [bold blue]{old_ID}[/]")
            return

        if old_ID != new_ID and new_ID in self.references:
            print(f"Reference already exists for ID: [bold blue]{new_ID}[/]")
            return

        if not new_reference_data:
            print("No new reference data provided.")
            return

        # Do not change files and tags
        new_reference_data["files"] = self.references[old_ID]["files"]
        new_reference_data["tags"] = self.references[old_ID]["tags"]

        old_reference_data = self.references[old_ID]
        if old_reference_data["is_doi"] and old_ID != new_ID:
            print("DOI cannot be changed manually.")
            return

        if old_reference_data["is_doi"] != new_reference_data["is_doi"]:
            print("DOI status cannot be changed manually.")
            return

        self.references[new_ID] = new_reference_data
        if old_ID != new_ID:
            self._move_data_files(old_ID, new_ID)
            del self.references[old_ID]
        self.references[new_ID]["updated_at"] = datetime.now().isoformat()
        self._save_references()
        print(
            f"Reference updated successfully for ID: [bold blue]{old_ID}[/] -> [bold blue]{new_ID}[/]"
        )

    def delete_reference(self, ID: str) -> None:
        """
        Deletes a reference and its associated data and raw files.

        Args:
            ID (str): The ID of the reference to delete.
        """
        if ID not in self.references:
            print(f"Reference not found for ID: [bold blue]{ID}[/]")
            return
        # Delete data files
        if len(self.references[ID]["files"]) > 0:
            file_name_list = self.references[ID]["files"].copy()
            for file_name in file_name_list:
                self.delete_data_file(ID, file_name)
        # Delete raw data
        safe_filename = sanitize_filename(ID)
        raw_file_path = f"{self.dir}/raw/{safe_filename}.json"
        self.git_api._delete_file(
            raw_file_path, f"Delete raw data for {ID}", required=False
        )
        # Delete reference data
        del self.references[ID]
        self._save_references()
        print(f"Reference deleted successfully for ID: [bold blue]{ID}[/]")

    def _move_data_files(self, old_ID: str, new_ID: str) -> None:
        """
        Moves data files associated with a reference when the ID is updated.

        Args:
            old_ID (str): The old ID of the reference.
            new_ID (str): The new ID of the reference.
        """
        old_safe_filename = sanitize_filename(old_ID)
        new_safe_filename = sanitize_filename(new_ID)

        old_data_dir = f"{self.data_dir}/{old_safe_filename}"
        new_data_dir = f"{self.data_dir}/{new_safe_filename}"

        try:
            contents = self.git_api._get_directory_contents(old_data_dir)
            for content in contents:
                if content["type"] == "file":
                    old_path = content["path"]
                    new_path = f"{new_data_dir}/{content['name']}"
                    self.git_api._move_file(old_path, new_path)
            print(
                f"All Data files moved successfully: [bold blue]{old_ID}[/] -> [bold blue]{new_ID}[/]"
            )

        except Exception as e:
            print(f"Error occurred while moving data files: {e}")
            raise

    def add_tag_to_reference(self, ID: str, tag: str) -> None:
        """
        Adds a tag to a reference.

        Args:
            ID (str): The ID of the reference.
            tag (str): The tag to add.
        """
        if ID not in self.references:
            print(f"Reference not found for ID: [bold blue]{ID}[/]")
            return
        if "tags" not in self.references[ID]:
            self.references[ID]["tags"] = []
        if tag not in self.references[ID]["tags"]:
            self.references[ID]["tags"].append(tag)
            self.references[ID]["updated_at"] = datetime.now().isoformat()
            self._save_references()
            print(f"Tag '{tag}' added to ID: [bold blue]{ID}[/]")
        else:
            print(f"Tag '{tag}' already exists in ID: [bold blue]{ID}[/]")

    def remove_tag_from_reference(self, ID: str, tag: str) -> None:
        """
        Removes a tag from a reference.

        Args:
            ID (str): The ID of the reference.
            tag (str): The tag to remove.
        """
        if ID not in self.references:
            print(f"Reference not found for ID: [bold blue]{ID}[/]")
            return
        elif "tags" in self.references[ID] and tag in self.references[ID]["tags"]:
            self.references[ID]["tags"].remove(tag)
            self.references[ID]["updated_at"] = datetime.now().isoformat()
            self._save_references()
            print(f"Tag '{tag}' removed from ID: [bold blue]{ID}[/]")
        else:
            print(f"Tag '{tag}' not found in ID: [bold blue]{ID}[/]")

    def add_data_file(self, ID: str, path_to_file: str) -> None:
        """
        Adds a data file to a reference.

        Args:
            ID (str): The ID of the reference.
            path_to_file (str): The path to the data file.
        """
        if ID not in self.references:
            print(f"Reference not found for ID: [bold blue]{ID}[/]")
            return
        safe_filename = sanitize_filename(ID)
        file_name = os.path.basename(path_to_file)
        if file_name in self.references[ID]["files"]:
            print(f"Data file: {file_name} already exists for [bold blue]{ID}[/].")
            return
        try:
            with open(path_to_file, "rb") as f:
                file_content = f.read()
            if not file_content:
                print(f"Failed to read data file: {path_to_file}")
                return
            self.git_api._create_file(
                f"{self.dir}/data/{safe_filename}/{file_name}",
                f"Add data file: {file_name} for {ID}",
                file_content,
                is_binary=True,
            )
            self.references[ID]["files"].append(file_name)
            self.references[ID]["updated_at"] = datetime.now().isoformat()
            self._save_references()
            print(f"Data file: {file_name} added successfully for [bold blue]{ID}[/]")

        except Exception as e:
            print(f"Failed to add data file: {file_name} for [bold blue]{ID}[/]: {e}")
            raise

    def delete_data_file(self, ID: str, file_name: str) -> None:
        """
        Deletes a data file from a reference.

        Args:
            ID (str): The ID of the reference.
            file_name (str): The name of the data file to delete.
        """
        if ID not in self.references:
            print(f"Reference not found for ID: [bold blue]{ID}[/]")
            return
        if file_name not in self.references[ID]["files"]:
            print(f"Data file {file_name} not found for ID: [bold blue]{ID}[/]")
            return
        safe_filename = sanitize_filename(ID)
        try:
            file_path = f"{self.dir}/data/{safe_filename}/{file_name}"
            self.git_api._delete_file(
                file_path,
                f"Delete data file: {file_name} for {ID}",
            )
            self.references[ID]["files"].remove(file_name)
            self.references[ID]["updated_at"] = datetime.now().isoformat()
            self._save_references()
            print(f"Data file: {file_name} deleted successfully for [bold blue]{ID}[/]")

        except Exception as e:
            print(
                f"Failed to delete data file: {file_name} for [bold blue]{ID}[/]: {e}"
            )

    def rename_data_file(self, ID: str, old_file_name: str, new_file_name: str) -> None:
        """
        Renames a data file associated with a reference.

        Args:
            ID (str): The ID of the reference.
            old_file_name (str): The current name of the data file.
            new_file_name (str): The new name for the data file.
        """
        if ID not in self.references:
            print(f"Reference not found for ID: [bold blue]{ID}[/]")
            return
        safe_filename = sanitize_filename(ID)
        try:
            file_path = f"{self.dir}/data/{safe_filename}/{old_file_name}"
            new_file_path = f"{self.dir}/data/{safe_filename}/{new_file_name}"
            self.git_api._move_file(file_path, new_file_path)
            # Update the reference data
            self.references[ID]["files"].remove(old_file_name)
            self.references[ID]["files"].append(new_file_name)
            self.references[ID]["updated_at"] = datetime.now().isoformat()
            self._save_references()
            print(
                f"Data file: {old_file_name} renamed to {new_file_name} for [bold blue]{ID}[/]"
            )

        except Exception as e:
            print(
                f"Failed to rename data file: {old_file_name} to {new_file_name} for [bold blue]{ID}[/]: {e}"
            )
            raise

    def export_references(self, format: str = "bibtex", tag_list: List[str] = None) -> List[Tuple[str, str]]:
        """
        Exports references in various citation formats.

        Args:
            format (str, optional): The citation format (e.g., "bibtex", "apa", "ris"). Defaults to "bibtex".
            tag_list (List[str], optional): List of tags to export (references with at least one of these tags will be exported). If None, all references are exported. Defaults to None.

        Returns:
            List[Tuple[str, str]]: List of references in the specified format with ID and formatted reference.
        """
        # TODO: Add support for more citation formats and loading custom citation styles with CSL files
        supported_formats = ["bibtex", "apa", "ris"]
        if format.lower() not in supported_formats:
            print(
                f"Unsupported format: {format}. Supported formats are: {supported_formats}"
            )
            return

        exported_references = []
        for ID, reference_data in self.references.items():
            if tag_list:
                if not any(tag in reference_data.get("tags", []) for tag in tag_list):
                    continue
            formatted_reference = self.formatter(ID, reference_data, format)
            if formatted_reference:
                exported_references.append((ID, formatted_reference))
        if not exported_references:
            print("No references found to export.")
            return []
        return exported_references

    def formatter(self, ID: str, reference: Dict[str, Any], format: str = "bibtex") -> str:
        """
        Formats a reference in the specified citation format.

        Args:
            ID (str): The ID of the reference.
            reference (Dict[str, Any]): The reference data.
            format (str, optional): The citation format (e.g., "bibtex", "apa", "ris"). Defaults to "bibtex".

        Returns:
            str: The formatted reference.
        """
        if format.lower() == "bibtex":
            formatted_reference = self._format_bibtex(ID, reference)
        elif format.lower() == "apa":
            formatted_reference = self._format_apa(ID, reference)
        elif format.lower() == "ris":
            formatted_reference = self._format_ris(ID, reference)
        else:
            print(f"Unsupported format: {format}")
            return
        return formatted_reference

    def _format_bibtex(self, ID: str, reference: Dict[str, Any]) -> str:
        """
        Formats a reference in BibTeX format.

        Args:
            ID (str): The ID of the reference.
            reference (Dict[str, Any]): The reference data.

        Returns:
            str: The BibTeX formatted reference.
        """
        # convert entry type to BibTeX format
        entry_type = reference["entry_type"]
        if entry_type == "":
            entry_type = "misc" # unpublished
        elif entry_type in CROSSREF_TO_BIB:
            entry_type = CROSSREF_TO_BIB[entry_type]
        authors = " and ".join(
            [
                f"{author['family']}, {author['given']}"
                for author in reference["authors"]
            ]
        )
        formatted_reference = (
            f"@{entry_type}" + "{" + f"{reference['citekey']},\n"
            f"  author={{{authors}}},\n"
        )
        if reference.get("title"):
            formatted_reference += f"  title={{{reference['title']}}},\n"
        if reference.get("year"):
            formatted_reference += f"  year={{{reference['year']}}},\n"
        if reference.get("month"):
            formatted_reference += f"  month={{{reference['month']}}},\n"
        if reference.get("edition"):
            formatted_reference += f"  edition={{{reference['edition']}}},\n"
        if reference.get("journal"):
            formatted_reference += f"  journal={{{reference['journal']}}},\n"
        if reference.get("volume"):
            formatted_reference += f"  volume={{{reference['volume']}}},\n"
        if reference.get("number"):
            formatted_reference += f"  number={{{reference['number']}}},\n"
        if reference.get("pages"):
            formatted_reference += (
                f"  pages={{{reference['firstpage']}-{reference['lastpage']}}},\n"
            )
        if reference.get("publisher"):
            formatted_reference += f"  publisher={{{reference['publisher']}}},\n"
        if reference.get("url"):
            formatted_reference += f"  url={{{reference['url']}}},\n"
        # if reference.get("isbn"):
        #     for isbn in reference.get("isbn", []):
        #         formatted_reference += f"  isbn={{{isbn}}},\n"
        # if reference.get("issn"):
        #     for issn in reference.get("issn", []):
        #         formatted_reference += f"  issn={{{issn}}},\n"
        if reference.get("is_doi"):
            formatted_reference += f"  doi={{{ID}}},\n"
        formatted_reference += "}"
        return formatted_reference

    def _format_apa(self, ID: str, reference: Dict[str, Any]) -> str:
        """
        Formats a reference in APA format.

        Args:
            ID (str): The ID of the reference.
            reference (Dict[str, Any]): The reference data.

        Returns:
            str: The APA formatted reference.
        """
        authors = ""
        for i, author in enumerate(reference["authors"]):
            if i == len(reference["authors"]) - 1 and len(reference["authors"]) > 1:
                authors += f"& {author['family']}, {author['given'][0]}."
            elif i == len(reference["authors"]) - 2 and len(reference["authors"]) > 2:
                authors += f"{author['family']}, {author['given'][0]}., "
            else:
                authors += f"{author['family']}, {author['given'][0]}., "
        year = f"({reference['year']})." if reference['year'] else ""
        title = f"{reference['title']}. " if reference['title'] else ""
        journal = f"_{reference['journal']}_" if reference['journal'] else ""
        volume = f", _{reference['volume']}_" if reference['volume'] else ""
        issue = f"({reference['issue']})" if reference['issue'] else ""
        pages = f", {reference['firstpage']}-{reference['lastpage']}" if reference['firstpage'] and reference['lastpage'] else ""
        doi = f". https://doi.org/{ID}" if reference['is_doi'] else ""
        url = f". {reference['url']}" if reference['url'] and not reference['is_doi'] else ""
        formatted_reference = f"{authors} {year} {title}{journal}{volume}{issue}{pages}{doi}{url}"
        return formatted_reference

    def _format_ris(self, ID: str, reference: Dict[str, Any]) -> str:
        """
        Formats a reference in RIS format.

        Args:
            ID (str): The ID of the reference.
            reference (Dict[str, Any]): The reference data.

        Returns:
            str: The RIS formatted reference.
        """
        entry_type = reference['entry_type']
        ris_type = ""
        if entry_type.lower() == "article":
            ris_type = "JOUR"
        elif entry_type.lower() in ["book", "inbook", "incollection"]:
            ris_type = "BOOK"
        elif entry_type.lower() == "thesis":
            ris_type = "THES"
        elif entry_type.lower() == "inproceedings":
            ris_type = "CONF"
        else:
            ris_type = "GEN"

        formatted_reference = f"TY  - {ris_type}\n"
        for author in reference["authors"]:
            formatted_reference += f"AU  - {author['family']}, {author['given']}\n"
        formatted_reference += f"TI  - {reference['title']}\n"
        if reference['year']:
            formatted_reference += f"PY  - {reference['year']}\n"
        if reference['journal']:
            formatted_reference += f"JF  - {reference['journal']}\n"
        if reference['volume']:
            formatted_reference += f"VL  - {reference['volume']}\n"
        if reference['issue']:
            formatted_reference += f"IS  - {reference['issue']}\n"
        if reference['firstpage'] and reference['lastpage']:
            formatted_reference += f"SP  - {reference['firstpage']}\n"
            formatted_reference += f"EP  - {reference['lastpage']}\n"
        if reference['publisher']:
            formatted_reference += f"PB  - {reference['publisher']}\n"
        if reference['is_doi']:
            formatted_reference += f"DO  - {ID}\n"
        if reference['url'] and not reference['is_doi']:
            formatted_reference += f"UR  - {reference['url']}\n"
        formatted_reference += "ER  - \n"
        return formatted_reference

    def reset(self) -> None:
        """
        Resets the references by deleting all data and raw files, and the references.json file.
        """
        try:
            # Delete all files in the data directory
            contents = self.git_api._get_directory_contents(self.data_dir)
            while contents:
                file_content = contents.pop(0)
                if file_content["type"] == "dir":
                    contents.extend(
                        self.git_api._get_directory_contents(file_content["path"])
                    )
                else:
                    self.git_api._delete_file(
                        file_content["path"],
                        f"Delete data file: {file_content['name']}",
                    )
            # Delete all files in the raw directory
            contents = self.git_api._get_directory_contents(self.raw_dir)
            while contents:
                file_content = contents.pop(0)
                if file_content["type"] == "dir":
                    contents.extend(
                        self.git_api._get_directory_contents(file_content["path"])
                    )
                else:
                    self.git_api._delete_file(
                        file_content["path"],
                        f"Delete raw data file: {file_content['name']}",
                    )
            # Delete the references.json file
            self.git_api._delete_file(self.references_file, "Delete references.json")
            self.references = {}
            print(f"References has been reset.")

        except Exception as e:
            print(f"An error occurred while resetting references: {e}")
            raise


if __name__ == "__main__":
    """
    For testing
    """
    import os

    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    config = json.load(open("../secrets/config.json"))
    github_token = config["github_token"]
    repo = config["repo"]
    api = GitHubAPI(github_token, repo)
    ref_manager = ReferenceManager(api)
    ref_manager.find_new_references()
    ref_manager.export_references()
