from pygitrefer.gitrefer import Gitrefer
import argparse


def main() -> None:
    """
    Main function to run the Gitrefer CLI.
    """
    cli = Gitrefer()

    # Create the argument parser
    parser = argparse.ArgumentParser(description="Manage references using GitRefer.")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command")

    # list_references
    parser_list = subparsers.add_parser("list", help="List all references")

    # show_reference
    parser_show = subparsers.add_parser("show", help="Show details of a reference")
    parser_show.add_argument("id", help="ID of the reference to show")

    # raw_data
    parser_raw = subparsers.add_parser("raw", help="Show raw data for a reference")
    parser_raw.add_argument("id", help="ID of the reference to show raw data for")

    # tree
    parser_tree = subparsers.add_parser("tree", help="Display the directory structure")

    # add_reference_from_doi
    parser_add_doi = subparsers.add_parser("add_doi", help="Add reference by DOI")
    parser_add_doi.add_argument("doi", help="DOI of the reference")

    # add_reference_from_doi_file
    parser_add_doi_file = subparsers.add_parser(
        "add_doi_from_file", help="Add references from a file containing DOIs"
    )
    parser_add_doi_file.add_argument("file", help="Path to the file containing DOIs")

    # add_reference_from_pdf
    parser_add_pdf = subparsers.add_parser("add_pdf", help="Add reference by PDF")
    parser_add_pdf.add_argument("pdf", help="Path to the PDF file")

    # add_reference_manually
    parser_add_manual = subparsers.add_parser(
        "add_manual", help="Add reference manually"
    )

    # find_new_references
    parser_find_new = subparsers.add_parser(
        "find_new", help="Find new references from raw JSON files"
    )

    # update_reference
    parser_update = subparsers.add_parser("update", help="Update reference")
    parser_update.add_argument("old_id", help="Old ID of the reference")
    parser_update.add_argument("new_id", help="New ID of the reference", nargs="?")

    # delete_reference
    parser_delete = subparsers.add_parser("delete", help="Delete reference")
    parser_delete.add_argument("id", help="ID of the reference to delete")

    # add_tag
    parser_add_tag = subparsers.add_parser("add_tag", help="Add tag to reference")
    parser_add_tag.add_argument("id", help="ID of the reference")
    parser_add_tag.add_argument("tag", help="Tag to add")

    # remove_tag
    parser_remove_tag = subparsers.add_parser(
        "remove_tag", help="Remove tag from reference"
    )
    parser_remove_tag.add_argument("id", help="ID of the reference")
    parser_remove_tag.add_argument("tag", help="Tag to remove")

    # add_data_file
    parser_add_file = subparsers.add_parser(
        "add_file", help="Add data file to reference"
    )
    parser_add_file.add_argument("id", help="ID of the reference")
    parser_add_file.add_argument("file", help="Path to the file to add")

    # delete_data_file
    parser_delete_file = subparsers.add_parser(
        "delete_file", help="Delete data file from reference"
    )
    parser_delete_file.add_argument("id", help="ID of the reference")
    parser_delete_file.add_argument("file_name", help="Name of the file to delete")

    # export_references
    parser_export = subparsers.add_parser("export", help="Export references")
    parser_export.add_argument(
        "format", help="Citation format (e.g., bibtex, apa, ris)"
    )
    parser_export.add_argument("-t", help="Tag to filter references", action="append")

    # reset
    parser_reset = subparsers.add_parser("reset", help="Reset all references and files")

    # Parse the arguments
    args = parser.parse_args()

    # Execute the commands based on the arguments
    if args.command == "list":
        cli.list()

    elif args.command == "show":
        cli.show(args.id)

    elif args.command == "raw":
        cli.raw(args.id)

    elif args.command == "tree":
        cli.tree()

    elif args.command == "add_doi":
        cli.add_doi(args.doi)

    elif args.command == "add_doi_from_file":
        cli.add_doi_from_file(args.file)

    elif args.command == "add_pdf":
        cli.add_pdf(args.pdf)

    elif args.command == "add_manual":
        cli.add_manual()

    elif args.command == "find_new":
        cli.find_new()

    elif args.command == "update":
        if args.new_id:
            cli.update(args.old_id, args.new_id)
        else:
            cli.update(args.old_id, args.old_id)

    elif args.command == "delete":
        print(
            f"Waring: This will delete the reference data and files for ID: [bold blue]{args.id}[/]."
        )
        confirmation = input("Type 'DELETE' to confirm: ")
        if confirmation == "DELETE":
            cli.delete(args.id)
        else:
            print("Delete operation aborted.")

    elif args.command == "add_tag":
        cli.add_tag(args.id, args.tag)

    elif args.command == "remove_tag":
        cli.remove_tag(args.id, args.tag)

    elif args.command == "add_file":
        cli.add_file(args.id, args.file)

    elif args.command == "delete_file":
        print(
            f"Waring: This will delete the data file: {args.file_name} for reference: {args.id}."
        )
        confirmation = input("Type 'DELETE' to confirm: ")
        if confirmation == "DELETE":
            cli.delete_file(args.id, args.file_name)
        else:
            print("Delete operation aborted.")

    elif args.command == "export":
        cli.export(args.format, tag_list=args.t)

    elif args.command == "reset":
        print(
            "Warning: This will delete ALL references data and files in the repository."
        )
        confirmation = input("Type 'RESET' to confirm: ")
        if confirmation == "RESET":
            cli.reset()
        else:
            print("Reset operation aborted.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()