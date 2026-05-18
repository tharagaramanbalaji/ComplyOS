import io
from typing import Dict, Any, Optional
from lxml import etree
from .namespace_utils import NamespaceUtils
from .xpath_utils import XPathUtils

class XMLReader:
    def __init__(self, xml_content: bytes):
        self.xml_content = xml_content
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            self.tree = etree.parse(io.BytesIO(xml_content), parser)
            self.root = self.tree.getroot()
            self.namespaces = self._resolve_namespaces()
            self.xpath_utils = XPathUtils(self.namespaces)
        except Exception as e:
            raise ValueError(f"Failed to parse XML: {str(e)}")

    def _resolve_namespaces(self) -> Dict[str, str]:
        ns = NamespaceUtils.get_common_namespaces()
        try:
            dynamic_ns = NamespaceUtils.extract_namespaces(io.BytesIO(self.xml_content))
            ns.update(dynamic_ns)
        except:
            pass
        if "default" in ns and "ubl" not in ns:
            ns["ubl"] = ns["default"]
        return ns

    def _get_first_match(self, xpaths: list) -> Optional[str]:
        for path in xpaths:
            val = self.xpath_utils.extract_single_value(self.root, path)
            if val: return val
        return None

    def extract_invoice_data(self) -> Dict[str, Any]:
        """
        Extracts standard invoice fields with a generalization layer fallback strategy.
        """
        data = {
            "invoice_id": self._get_first_match(["//cbc:ID", "//InvoiceID", "//ID"]),
            "issue_date": self._get_first_match(["//cbc:IssueDate", "//IssueDate", "//Date"]),
            "currency_code": self._get_first_match(["//cbc:DocumentCurrencyCode", "//CurrencyCode", "//Currency"]),
            "payable_amount": self._extract_amount(["//cac:LegalMonetaryTotal/cbc:PayableAmount", "//PayableAmount"]),
            "taxable_amount": self._extract_amount(["//cac:TaxTotal/cac:TaxSubtotal/cbc:TaxableAmount", "//TaxableAmount"]),
            "tax_amount": self._extract_amount(["//cac:TaxTotal/cbc:TaxAmount", "//TaxAmount"]),
            "tax_category": self._get_first_match(["//cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:ID", "//TaxCategory"]),
            "tax_exemption_reason": self._get_first_match(["//cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:TaxExemptionReason", "//TaxExemptionReason"]),
            "seller_name": self._get_first_match(["//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name", "//SellerName"]),
            "buyer_name": self._get_first_match(["//cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name", "//BuyerName"]),
            "line_items": self._extract_line_items()
        }
        return data

    def _extract_amount(self, xpaths: list) -> Optional[float]:
        val = self._get_first_match(xpaths)
        if val:
            try:
                return float(val)
            except ValueError:
                return None
        return None

    def _extract_line_items(self) -> list:
        items = []
        lines = self.xpath_utils.extract_list(self.root, "//cac:InvoiceLine")
        if not lines:
            lines = self.xpath_utils.extract_list(self.root, "//InvoiceLine")
            
        for line in lines:
            item = {
                "id": self.xpath_utils.extract_single_value(line, "cbc:ID") or self.xpath_utils.extract_single_value(line, "ID"),
                "quantity": self._extract_amount_from_element(line, "cbc:InvoicedQuantity") or self._extract_amount_from_element(line, "InvoicedQuantity"),
                "line_extension_amount": self._extract_amount_from_element(line, "cbc:LineExtensionAmount") or self._extract_amount_from_element(line, "LineExtensionAmount"),
                "item_name": self.xpath_utils.extract_single_value(line, "cac:Item/cbc:Name") or self.xpath_utils.extract_single_value(line, "Item/Name"),
                "tax_category": self.xpath_utils.extract_single_value(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:ID") or self.xpath_utils.extract_single_value(line, "TaxCategory"),
                "tax_percent": self._extract_amount_from_element(line, "cac:Item/cac:ClassifiedTaxCategory/cbc:Percent") or self._extract_amount_from_element(line, "TaxPercent"),
            }
            items.append(item)
        return items

    def _extract_amount_from_element(self, element: etree._Element, xpath: str) -> Optional[float]:
        val = self.xpath_utils.extract_single_value(element, xpath)
        if val:
            try:
                return float(val)
            except ValueError:
                return None
        return None
