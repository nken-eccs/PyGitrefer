from typing import Optional, Any, Dict, List
from pygitrefer.git_api import GitHubAPI
from pygitrefer.reference_manager import ReferenceManager
from pygitrefer.pdf_to_doi import pdf_to_doi
from pygitrefer.utils import validate_doi
import json
import os
from dotenv import load_dotenv, find_dotenv
import google.generativeai as genai
from datetime import datetime
from rich import print
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree


class Gitrefer:
    """
    GitRefer class to manage references on GitHub.
    """

    def __init__(self, token: str = None, repo: str = None, gemini_api_key: str = None, debug: bool = False) -> None:
        """
        Initialize the GitRefer class. If the token, repo, or gemini_api_key is not provided, it will load from the environment variables or prompt the user to enter.

        Parameters
        ----------
        token : str, optional
            GitHub personal access token with repo scope, by default None
        repo : str, optional
            GitHub repository name in the format "{owner}/{repo}", by default None
        gemini_api_key : str, optional
            Gemini API key, by default None
        debug : bool, optional
            Enable debug mode, by default False
        """
        self.token = token
        self.repo = repo
        self.gemini_api_key = gemini_api_key
        load_dotenv(find_dotenv(usecwd=True))
        if debug:
            print()
            print("Debug mode enabled.")
            print(f"Current directory: {os.getcwd()}")
            print(f"Environment variables: {os.environ}")
            print()
        if not self.token:
            try:
                self.token = os.environ["GITREFER_TOKEN"]
            except KeyError:
                self.token = input("Enter GitHub token: ").strip()
        if not self.repo:
            try:
                self.repo = os.environ["GITREFER_REPO"]
            except KeyError:
                self.repo = input(
                    "Enter GitHub repository name [owner/repo] : "
                ).strip()
        if not self.gemini_api_key:
            try:
                self.gemini_api_key = os.environ["GITREFER_GEMINI_API_KEY"]
            except KeyError:
                self.gemini_api_key = input("Enter Gemini API key (optional): ").strip()
        self.git_api = GitHubAPI(github_token=self.token, repo_name=self.repo)
        self.reference_manager = ReferenceManager(self.git_api)


    def list(self) -> None:
        """
        List all references in a table format using rich module.
        """
        table = Table(
            title=f"All References in {self.repo}",
            title_style="bold italic",
            show_lines=True,
        )
        table.add_column("ID", style="bold blue", no_wrap=True)
        table.add_column("Title")
        table.add_column("Year", justify="right")
        table.add_column("Tags")
        for ID, reference in self.reference_manager.references.items():
            table.add_row(
                ID, reference["title"], reference["year"], ", ".join(reference["tags"])
            )
        print(table)

    def show(self, id: str) -> None:
        """
        Show detailed information for a specific reference using rich module.

        Parameters
        ----------
        ID : str
            ID of the reference to show.
        """
        reference = self.reference_manager.get_reference(id)
        if reference:
            panel = Panel(
                f"""
[b]Entry Type:[/b] {reference['entry_type']}
[b]Citekey:[/b] {reference['citekey']}
[b]Authors:[/b] {"; ".join([f"{author['family']}, {author['given']}" for author in reference['authors']])}
[b]Title:[/b] {reference['title']}
[b]Year:[/b] {reference['year']}
[b]Month:[/b] {reference['month']}
[b]Edition:[/b] {reference['edition']}
[b]Journal:[/b] {reference['journal']}
[b]Volume:[/b] {reference['volume']}
[b]Issue:[/b] {reference['issue']}
[b]First Page:[/b] {reference['firstpage']}
[b]Last Page:[/b] {reference['lastpage']}
[b]Publisher:[/b] {reference['publisher']}
[b]ISBN:[/b] {', '.join(reference['isbn'])}
[b]ISSN:[/b] {', '.join(reference['issn'])}
[b]Abstract:[/b] {reference['abstract']}
[b]Keywords:[/b] {reference['keywords']}
[b]URL:[/b] {reference['url']}
[b]Tags:[/b] {', '.join(reference['tags'])}
[b]Files:[/b] {', '.join(reference['files'])}
[b]Created At:[/b] {reference['created_at']}
[b]Updated At:[/b] {reference['updated_at']}
                """,
                title=f"Reference Details for ID: [bold blue]{id}[/]",
                expand=False,
            )
            print(panel)

    def raw(self, id: str) -> None:
        """
        Show raw data for a specific reference.

        Parameters
        ----------
        ID : str
            ID of the reference to show raw data for.
        """
        raw_data = self.reference_manager.get_raw_data(id)
        if raw_data:
            print(raw_data)

    def tree(self) -> None:
        """
        Display the contents of the references directory in a tree structure.
        """
        tree = Tree(f"[b]{self.reference_manager.dir}[/]")
        self._add_directory_to_tree(tree, self.reference_manager.dir)
        print(tree)

    def _add_directory_to_tree(self, tree: Tree, path: str) -> None:
        """
        Recursively add the contents of a directory to the tree.

        Parameters
        ----------
        tree : Tree
            Tree object to add the directory contents.
        path : str
            Path of the directory.
        """
        contents = self.git_api._get_directory_contents(path)
        for content in contents:
            if content["type"] == "dir":
                branch = tree.add(f"[b]{content['name']}[/]")
                self._add_directory_to_tree(branch, content["path"])
            else:
                tree.add(content["name"])

    def add_doi(self, doi: str, download_pdf: bool = True) -> None:
        """
        Add a new reference from a DOI.

        Parameters
        ----------
        doi : str
            DOI of the reference.
        """
        self.reference_manager.add_reference_from_doi(doi, download_pdf=download_pdf)

    def add_doi_from_file(self, file_path: str) -> None:
        """
        Add new references from a file containing a list of DOIs. Each DOI should be on a separate line.

        Parameters
        ----------
        file_path : str
            Path to the file containing DOIs.
        """
        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                lines = f.readlines()
            dois = []
            for line in lines:
                if line and validate_doi(line.strip()):
                    dois.append(line.strip())
            print(f"Found {len(dois)} DOIs in the file.")
            for i in range(len(dois)):
                print(f"Adding reference from DOI: {dois[i]} ({i+1}/{len(dois)})")
                self.add_doi(dois[i])

        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")

    def add_pdf(self, pdf_path: str) -> None:
        """
        Add a new reference from a PDF file or a directory containing PDF files.

        Parameters
        ----------
        pdf_path : str
            Path to the PDF file or directory.
        """
        pdf_path = os.path.normpath(pdf_path)
        if os.path.isdir(pdf_path):
            error_files = []
            print(f"Adding references from PDF files in the directory {pdf_path}...")
            for root, _, files in os.walk(pdf_path):
                for file in files:
                    if file.endswith(".pdf"):
                        try:
                            self._add_single_pdf(os.path.join(root, file))
                            print()

                        except Exception as e:
                            print(
                                f"Error occured while adding reference from the PDF file: {e}"
                            )
                            error_files.append(os.path.join(root, file))
                            print("Continuing with the next file...")
            if error_files:
                print(f"Failed to add references from the following PDF files:")
                for file in error_files:
                    print(file)
        elif os.path.isfile(pdf_path) and pdf_path.endswith(".pdf"):
            print(f"Adding reference from the PDF file {pdf_path}...")
            self._add_single_pdf(pdf_path)
            return
        else:
            print("Invalid path. Please provide a path to a PDF file or a directory.")
            return

    def _add_single_pdf(self, pdf_path: str) -> None:
        """
        Add a new reference from a single PDF file.

        Parameters
        ----------
        pdf_path : str
            Path to the PDF file.
        """
        if self.gemini_api_key:
            print(f"Extracting DOI from the PDF file {pdf_path} using Gemini API...")
            doi = self._extract_doi_from_pdf_by_gemini(pdf_path, self.gemini_api_key)
        else:
            print(f"Extracting DOI from the PDF file {pdf_path} using pdf2doi...")
            doi = pdf_to_doi(pdf_path)
        if doi and validate_doi(doi.strip().replace("https://doi.org/", "")):
            doi = doi.strip().replace("https://doi.org/", "")
            print(f"Extracted DOI: [bold blue]{doi}[/]")
            # Add reference from the extracted DOI
            self.add_doi(doi, download_pdf=False)
            # Add the PDF file as a data file
            self.reference_manager.add_data_file(doi, pdf_path)
        else:
            print(f"DOI not found in the PDF file {pdf_path}.")
            # Extract information from the PDF file
            if self.gemini_api_key:
                print(f"Extracting information from the PDF file {pdf_path}...")
                data = self._extract_information_from_pdf_by_gemini(
                    pdf_path, self.gemini_api_key
                )
                if data:
                    registered_titles = set(
                        [
                            reference["title"]
                            for reference in self.reference_manager.references.values()
                        ]
                    )
                    if data["title"] in registered_titles:
                        print("Reference with the same title already exists.")
                        return
                    else:
                        id = datetime.now().strftime("%Y%m%d%H%M%S")
                        self.reference_manager.add_reference_manually(id, data)
                        self.reference_manager.add_data_file(id, pdf_path)
                else:
                    print(
                        f"Failed to extract information from the PDF file {pdf_path}."
                    )
            else:
                print(
                    "Please provide the API key to extract information from the PDF file."
                )

    # def add_pdf(self, pdf_path: str) -> None:
    #     """
    #     Add a new reference from a PDF file.

    #     Parameters
    #     ----------
    #     pdf_path : str
    #         Path to the PDF file.
    #     """
    #     if self.gemini_api_key:
    #         print("Extracting DOI from the PDF file using Gemini API...")
    #         doi = self._extract_doi_from_pdf_by_gemini(pdf_path, self.gemini_api_key)
    #     else:
    #         print("Extracting DOI from the PDF file using pdf2doi...")
    #         doi = pdf_to_doi(pdf_path)
    #     if doi and validate_doi(doi):
    #         print(f"Extracted DOI: {doi}")
    #         # Add reference from the extracted DOI
    #         self.add_doi(doi, download_pdf=False)
    #         # Add the PDF file as a data file
    #         self.reference_manager.add_data_file(doi, pdf_path)
    #     else:
    #         print("DOI not found in the PDF file.")
    #         # Extract information from the PDF file
    #         if self.gemini_api_key:
    #             print("Extracting information from the PDF file...")
    #             data = self._extract_information_from_pdf_by_gemini(
    #                 pdf_path, self.gemini_api_key
    #             )
    #             if data:
    #                 registered_titles = set(
    #                     [
    #                         reference["title"]
    #                         for reference in self.reference_manager.references.values()
    #                     ]
    #                 )
    #                 if data["title"] in registered_titles:
    #                     print("Reference with the same title already exists.")
    #                     return
    #                 else:
    #                     id = datetime.now().strftime("%Y%m%d%H%M%S")
    #                     self.reference_manager.add_reference_manually(id, data)
    #                     self.reference_manager.add_data_file(id, pdf_path)
    #             else:
    #                 print("Failed to extract information from the PDF file.")
    #         else:
    #             print(
    #                 "Please provide the API key to extract information from the PDF file."
    #             )

    def _extract_doi_from_pdf_by_gemini(
        self, pdf_path: str, api_key: str
    ) -> Optional[str]:
        """
        Extract DOI from a PDF file using the Gemini API.
        """
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"},
        )
        prompt = f"Extract the doi for this document (not the one in the references section). If not found, return null."
        uploaded_file = genai.upload_file(path=pdf_path)
        retrieved_file = genai.get_file(name=uploaded_file.name)
        try:
            response = model.generate_content([retrieved_file, prompt])
            data = json.loads(response.text)
            if type(data) == str:
                return data
            if type(data) == dict and "doi" in data:
                return data["doi"]
            elif type(data) == dict and "DOI" in data:
                return data["DOI"]
            else:
                print(f"Extracted information: {data}")
                print("DOI not found in the extracted information.")
                return None
        except Exception as e:
            print(
                f"Error occured while extracting DOI from the PDF file using Gemini API: {e}"
            )
            return None

    def _extract_information_from_pdf_by_gemini(
        self, pdf_path: str, api_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract information from a PDF file using the Gemini API.
        """
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config={"response_mime_type": "application/json"},
        )
        prompt = "Extract authors (family, given), title, abstract and keywords (comma separated) of this paper."
        uploaded_file = genai.upload_file(path=pdf_path)
        retrieved_file = genai.get_file(name=uploaded_file.name)
        try:
            response = model.generate_content([retrieved_file, prompt])
            data = json.loads(response.text)
            return data
        except Exception as e:
            print(
                f"Error occured while extracting information from the PDF file using Gemini API: {e}"
            )
            return None

    def add_manual(self) -> None:
        """
        Add a new reference manually.
        """
        id = input("Enter ID for the reference: ").strip()
        reference_data = self.prompt_reference_data()
        self.reference_manager.add_reference_manually(id, reference_data)

    def find_new(self) -> None:
        """
        Find new relevant references from the raw JSON files in the GitHub repository.
        """
        new_references = self.reference_manager.find_new_references()
        if len(new_references) > 0:
            print(f"Found {len(new_references)} new references.")
            table = Table(
                title="New References Found",
                title_style="bold italic",
                show_lines=True,
            )
            table.add_column("DOI", style="bold blue", no_wrap=True)
            table.add_column("Information")
            table.add_column("Count", justify="right")
            for doi, data, int in new_references:
                table.add_row(doi, ", ".join(data), str(int))
            print(table)

    def update(self, old_id: str, new_id: str) -> None:
        """
        Update an existing reference.

        Parameters
        ----------
        old_id : str
            Old ID of the reference.
        new_id : str
            New ID of the reference.
        """
        old_reference_data = self.reference_manager.get_reference(old_id)
        if not old_reference_data:
            print(f"Reference not found for ID: {old_id}")
            return
        self.show(old_id)
        print("Please edit the reference data. Leave blank to keep the existing value.")
        new_reference_data = self.prompt_reference_data()
        for key, value in new_reference_data.items():
            if value:
                old_reference_data[key] = value
        self.reference_manager.update_reference(old_id, new_id, old_reference_data)

    def delete(self, id: str) -> None:
        """
        Delete a reference.

        Parameters
        ----------
        id : str
            ID of the reference.
        """
        self.reference_manager.delete_reference(id)

    def add_tag(self, id: str, tag: str) -> None:
        """
        Add a tag to a reference.

        Parameters
        ----------
        id : str
            ID of the reference.
        tag : str
            Tag to add.
        """
        self.reference_manager.add_tag_to_reference(id, tag)

    def remove_tag(self, id: str, tag: str) -> None:
        """
        Remove a tag from a reference.

        Parameters
        ----------
        id : str
            ID of the reference.
        tag : str
            Tag to remove.
        """
        self.reference_manager.remove_tag_from_reference(id, tag)

    def add_file(self, id: str, file_path: str) -> None:
        """
        Add a data file to a reference.

        Parameters
        ----------
        id : str
            ID of the reference.
        file_path : str
            Path to the data file.
        """
        self.reference_manager.add_data_file(id, file_path)

    def delete_file(self, id: str, file_name: str) -> None:
        """
        Delete a data file from a reference.

        Parameters
        ----------
        id : str
            ID of the reference.
        file_name : str
            Name of the data file to delete.
        """
        self.reference_manager.delete_data_file(id, file_name)

    def export(self, format: str, tag_list: List[str] = None) -> None:
        """
        Export references in the specified format.

        Parameters
        ----------
        format : str
            Citation format (e.g., "apa", "bibtex", "ris").
        tag_list : List[str], optional
            List of tags to export (references with at least one of these tags). If None, export all references. Defaults to None.
        """
        exported_references = self.reference_manager.export_references(
            format, tag_list=tag_list
        )
        if exported_references:
            for exported_reference in exported_references:
                _, reference = exported_reference
                print(reference)
                print()

    def reset(self) -> None:
        """
        Reset the references.
        """
        self.reference_manager.reset()

    def prompt_reference_data(self) -> Dict[str, Any]:
        """
        Prompt the user for reference data.

        Returns
        -------
        Dict[str, Any]
            Reference data.
        """
        reference_data = {}
        reference_data["entry_type"] = self.prompt_entry_type()
        reference_data["citekey"] = input(
            "Citekey (leave blank to auto-generate): "
        ).strip()
        reference_data["authors"] = self.prompt_authors()
        reference_data["title"] = input("Title: ").strip()
        reference_data["year"] = input("Year: ").strip()
        reference_data["month"] = input("Month: ").strip()
        reference_data["edition"] = input("Edition: ").strip()
        reference_data["journal"] = input("Journal: ").strip()
        reference_data["volume"] = input("Volume: ").strip()
        reference_data["issue"] = input("Issue: ").strip()
        reference_data["firstpage"] = input("First Page: ").strip()
        reference_data["lastpage"] = input("Last Page: ").strip()
        reference_data["publisher"] = input("Publisher: ").strip()
        reference_data["isbn"] = self.prompt_isbn()
        reference_data["issn"] = self.prompt_issn()
        reference_data["abstract"] = input("Abstract: ").strip()
        reference_data["keywords"] = input("Keywords (comma separated): ").strip()
        reference_data["url"] = input("URL: ").strip()
        reference_data["tags"] = []
        reference_data["files"] = []
        return reference_data

    def prompt_entry_type(self) -> str:
        """
        Prompt the user to select an entry type. Leave blank to skip.

        Returns
        -------
        str
            Selected entry type.
        """
        entry_types = [
            "article",
            "book",
            "booklet",
            "conference",
            "inbook",
            "incollection",
            "inproceedings",
            "manual",
            "mastersthesis",
            "misc",
            "phdthesis",
            "proceedings",
            "techreport",
            "unpublished",
        ]
        print("Select Entry Type:")
        for i, entry_type in enumerate(entry_types, start=1):
            print(f"{i}. {entry_type}")
        while True:
            choice = input(
                "Enter the number of the entry type (leave blank to skip): "
            ).strip()
            if not choice:
                return ""
            if choice.isdigit() and 1 <= int(choice) <= len(entry_types):
                return entry_types[int(choice) - 1]
            print("Invalid choice. Please enter the number of the entry type.")

    def prompt_authors(self) -> List[Dict[str, str]]:
        """
        Prompt the user for author information.

        Returns
        -------
        List[Dict[str, str]]
            List of authors.
        """
        authors = []
        while True:
            family = input("Author Family Name (leave blank to stop): ").strip()
            if not family:
                break
            given = input("Author Given Name: ").strip()
            authors.append({"family": family, "given": given})
        return authors

    def prompt_isbn(self) -> List[str]:
        """
        Prompt the user for ISBN.

        Returns
        -------
        List[str]
            List of ISBN.
        """
        isbn_list = []
        while True:
            isbn = input("ISBN (leave blank to stop): ").strip()
            if not isbn:
                break
            isbn_list.append(isbn)
        return isbn_list

    def prompt_issn(self) -> List[str]:
        """
        Prompt the user for ISSN.

        Returns
        -------
        List[str]
            List of ISSN.
        """
        issn_list = []
        while True:
            issn = input("ISSN (leave blank to stop): ").strip()
            if not issn:
                break
            issn_list.append(issn)
        return issn_list


if __name__ == "__main__":
    """
    For testing
    """
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    
    config = json.load(open("../secrets/config.json"))
    github_token = config["github_token"]
    repo = config["repo"]
    gemini_api_key = config["gemini_api_key"]
    print(f"GitHub token: {github_token}")
    print(f"Using GitHub repository: {repo}")
    print(f"Gemini API key: {gemini_api_key}")
    gitrefer = Gitrefer(token=github_token, repo=repo, gemini_api_key=gemini_api_key)
    gitrefer.list()
