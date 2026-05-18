from typing import Dict
from lxml import etree

class NamespaceUtils:
    @staticmethod
    def extract_namespaces(xml_tree: etree._ElementTree) -> Dict[str, str]:
        """
        Extracts all namespaces from the given XML tree dynamically.
        Returns a dictionary mapping prefixes to namespace URIs.
        """
        namespaces = {}
        for _, elem in etree.iterparse(xml_tree, events=("start-ns",)):
            prefix, uri = elem
            # Handle default namespace
            prefix_key = prefix if prefix else "default"
            namespaces[prefix_key] = uri
        return namespaces

    @staticmethod
    def get_common_namespaces() -> Dict[str, str]:
        """
        Returns a set of common UBL/Invoice namespaces as a fallback.
        """
        return {
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "ubl": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
            "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
        }
