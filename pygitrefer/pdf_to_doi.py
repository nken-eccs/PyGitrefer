from typing import Optional, Union
from pathlib import Path
from pdf2doi import pdf2doi


def pdf_to_doi(path_pdf: Union[Path, str]) -> Optional[str]:
    try:
        return pdf2doi(str(path_pdf))["identifier"]
    except TypeError:
        return None


if __name__ == "__main__":
    """
    For testing
    """
    import os

    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    print(pdf_to_doi("../samples/PDF/test.pdf"))
