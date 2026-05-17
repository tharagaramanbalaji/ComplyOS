from __future__ import annotations


class XMLExtractor:
    @staticmethod
    def field_to_xpath(field: str) -> str:
        """Convert IR field paths into XPath expressions for invoice XML."""
        if field == "line_items":
            return "/Invoice/line_items"

        if "[*]" in field:
            segments = field.split('.')
            xpath_parts = ["/Invoice"]
            for segment in segments:
                if segment.endswith('[*]'):
                    container = segment[:-3]
                    xpath_parts.append(f"{container}/line_item")
                else:
                    xpath_parts.append(segment)
            return '/'.join(xpath_parts)

        return f"/Invoice/{field}"

    @staticmethod
    def exists_expression(field: str) -> str:
        xpath = XMLExtractor.field_to_xpath(field)
        return f"boolean({xpath})"

    @staticmethod
    def numeric_expression(field: str) -> str:
        xpath = XMLExtractor.field_to_xpath(field)
        return f"number({xpath})"

    @staticmethod
    def sum_expression(field: str) -> str:
        xpath = XMLExtractor.field_to_xpath(field)
        return f"sum({xpath})"

    @staticmethod
    def exists_expression(field: str) -> str:
        xpath = XMLExtractor.field_to_xpath(field)
        return f"boolean({xpath})"

    @staticmethod
    def numeric_expression(field: str) -> str:
        xpath = XMLExtractor.field_to_xpath(field)
        return f"number({xpath})"

    @staticmethod
    def sum_expression(field: str) -> str:
        xpath = XMLExtractor.field_to_xpath(field)
        return f"sum({xpath})"
