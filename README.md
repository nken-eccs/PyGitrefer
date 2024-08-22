# 📚 PyGitrefer: Your GitHub-Powered Bibliography Manager!

Welcome to *PyGitrefer*, your daily assistant for effortlessly managing bibliographic information directly within your GitHub repositories!

Say goodbye to messy spreadsheets and hello to a streamlined, version-controlled, and collaborative approach to keeping your research references in order.

## What is PyGitrefer?

PyGitrefer is a Python package designed to make managing your references on GitHub a breeze. It allows you to:

* **Manage References:** Easily add new references from DOIs or PDFs, even extracting information automatically if DOI is missing. You can also add, edit, and remove references manually.
* **Attach Files:** Link PDFs, notes, or any relevant files directly to your references.
* **Organize with Tags:** Categorize your references with custom tags for quick filtering, searching and custom exports.
* **Version Control:** Leverage the power of Git to track any changes to your references.
* **Collaborate with Ease:** Share your references with collaborators, keep track of changes, and maintain a clean and consistent bibliography.
* **Export in Multiple Formats:** Generate citations in BibTeX, APA, RIS, and more!

PyGitrefer is a perfect tool for researchers, students, and anyone who wants to keep their references organized, accessible, and up-to-date. You can easily integrate it into existing repositories or start fresh with a dedicated bibliography repository.

## Getting Started 🚀

### Requirements

### Installation

1. **Install directly from GitHub:**

   ```bash
   pip install git+https://github.com/nken-eccs/PyGitrefer.git
   ```

2. **Install using pip (coming soon):**

   ```bash
   pip install pygitrefer
   ```

### Setup

You need to set up the following environment variables before you can start using PyGitrefer:

1. **GitHub Personal Access Token (`GITREFER_TOKEN`):**
   - Generate a personal access token on GitHub with `repo` scope.

2. **Repository Information (`GITREFER_REPO`):**
   - Determine the owner and name of your GitHub repository (e.g., `owner_name/repository_name`).
   - If you start with a new repository, please create a repository first before initializing PyGitrefer!

> [!NOTE]
> You can find this information in the URL of a repository on GitHub. For example, in the URL `https://github.com/nken-eccs/PyGitrefer`, the `owner_name` is `nken-eccs` and the `repository_name` is `PyGitrefer`. Even though the owner name is not your username, you can still access the repository with your personal access token if you are a collaborator.

3. **Gemini API Key (Optional) (`GITREFER_GEMINI_API_KEY`):**
   - If you want to use the AI-powered reference extraction feature, please get an API key from [Google AI Studio](https://aistudio.google.com/). Anyone who has a Google account can sign up for free.

> [!NOTE]
> Currently, Gemini 1.5 Flash is set as the default model. You can make requests up to 1500 times per day [[source](https://ai.google.dev/pricing)].

The easiest way to set these environment variables is to create a `.env` file in the root directory of your project and add the following lines:

   ```bash:.env
   GITREFER_TOKEN=<your_github_personal_access_token>
   GITREFER_REPO=<owner_name/repository_name>
   GITREFER_GEMINI_API_KEY=<your_google_ai_studio_api_key>
   ```

For exmaple,

   ```bash:.env
   GITREFER_TOKEN=abcdefgh1234567890
   GITREFER_REPO=nken-eccs/PyGitrefer
   GITREFER_GEMINI_API_KEY=1234567890abcdefgh
   ```

> [!WARNING]
> Keep your `.env` file secure and never share it publicly. It contains sensitive information that could compromise your GitHub account.


PyGitrefer will try to load these environment variables when you run the commands. It will search for the `.env` file in the current working directory or higher directories. If these environment variables are not set, you will be prompted to enter them manually.

### Usage

Here's a breakdown of the commands you can use with PyGitrefer:

1. **List All References:**

   ```bash
   gitrefer list
   ```

2. **Show Reference Details:**

   ```bash
   gitrefer show <ID>
   ```

3. **Show Raw Metadata of a Reference:**

   ```bash
   gitrefer raw <ID>
   ```

4. **Show Directory Structure of the References Folder:**

   ```bash
   gitrefer tree
   ```

5. **Add Reference from a Single DOI:**

   ```bash
   gitrefer add_doi <DOI>
   ```

6. **Add Reference from Multiple DOIs Listed in a Text File:**

   ```bash
   gitrefer add_doi_from_file <path/to/file>
   ```

7. **Add Reference from PDF (if a directory path is given, all PDFs in the directory will be added):** 

   ```bash
   gitrefer add_pdf <path/to/pdf> or <path/to/directory>
   ```

8. **Add Reference Manually:**

   ```bash
   gitrefer add_manual
   ```

9. **Find New References:**

   ```bash
   gitrefer find_new
   ```

10. **Update Reference:**

   ```bash
   gitrefer update <old_ID> [<new_ID>] 
   ```

11. **Delete Reference:**

   ```bash
   gitrefer delete <ID>
   ```

12. **Add Tag to Reference:**

   ```bash
   gitrefer add_tag <ID> <tag>
   ```

13. **Remove Tag from Reference:**

   ```bash
   gitrefer remove_tag <ID> <tag>
   ```

14. **Add File to Reference:**

   ```bash
   gitrefer add_file <ID> <path/to/file>
   ```

15. **Delete File from Reference:**

   ```bash
   gitrefer delete_file <ID> <filename>
   ```

16. **Export References in a Specific Format:**

   ```bash
   gitrefer export <format> [-t <tag>] ...
   ```

17. **Reset References:**

   ```bash
   gitrefer reset
   ```

## Why Use PyGitrefer?

* **Collaboration Made Easy:** Work seamlessly with colleagues on shared research projects.
* **Version Control:** Track changes to your references over time, ensuring data integrity.
* **Organization and Efficiency:** Keep your references neatly organized and easily accessible from anywhere.
* **Integration with GitHub:** Leverage the familiar and powerful platform of GitHub.

## Roadmap 🗺️

Here are some exciting features I plan to add in the future:

* **AI-Powered Reference Search:** Use AI to search for new references that match your research interests, based on your existing bibliography. Github Actions may be used to automate this process.
* **Custom Citation Styles:** Generate citations in any format you need, with customizable templates.

Finally, I'm planning to create a GUI interface (Gitrefer) to make it even easier to manage your references.

If you have any feature requests or suggestions, please feel free to open an issue on GitHub.

## Contributions

If you'd like to contribute to this project, please feel free to submit a pull request or open an issue on GitHub. I really appreciate your support and feedback!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


---

Happy referencing!

Let PyGitrefer be your trusted guide in the vast world of academic literature. 🚢🧭