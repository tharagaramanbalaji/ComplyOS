from typing import List, Any, Dict, Optional
from lxml import etree

class XPathUtils:
    def __init__(self, namespaces: Optional[Dict[str, str]] = None):
        self.namespaces = namespaces or {}

    def extract_single_value(self, element: etree._Element, xpath_expr: str) -> Optional[str]:
        """
        Extracts a single text value using XPath.
        """
        try:
            result = element.xpath(xpath_expr, namespaces=self.namespaces)
            if result:
                if isinstance(result[0], str):
                    return result[0].strip()
                elif hasattr(result[0], 'text') and result[0].text:
                    return result[0].text.strip()
            return None
        except Exception as e:
            return None

    def extract_list(self, element: etree._Element, xpath_expr: str) -> List[etree._Element]:
        """
        Extracts a list of elements using XPath.
        """
        try:
            result = element.xpath(xpath_expr, namespaces=self.namespaces)
            return result if isinstance(result, list) else []
        except Exception as e:
            return []
