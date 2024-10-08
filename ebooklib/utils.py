# This file is part of EbookLib.
# Copyright (c) 2013 Aleksandar Erkalovic <aerkalov@gmail.com>
#
# EbookLib is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EbookLib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with EbookLib.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations
import io
import mimetypes
from typing import Dict, List, Optional, Tuple, Union, TYPE_CHECKING


from lxml import etree
from lxml import html
from lxml.etree import ParserError
from lxml.etree import _ElementTree as ElementTree
from lxml.etree import _Element as Element

if TYPE_CHECKING:
    from epub import EpubItem

mimetype_initialised = False


def debug(obj):
    import pprint

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(obj)


def parse_string(s: str) -> ElementTree:
    parser = etree.XMLParser(recover=True, resolve_entities=False)
    try:
        tree: ElementTree = etree.fromstring(
            io.BytesIO(s.encode("utf-8")), parser=parser
        )
    except ParserError:
        tree = etree.fromstring(io.BytesIO(s), parser=parser)

    return tree


def parse_html_string(s: str) -> ElementTree:
    utf8_parser = html.HTMLParser(encoding="utf-8")

    html_tree: ElementTree = html.document_fromstring(s, parser=utf8_parser)

    return html_tree


def guess_type(extension: str) -> Tuple[Optional[str], Optional[str]]:
    global mimetype_initialised

    if not mimetype_initialised:
        mimetypes.init()
        mimetypes.add_type("application/xhtml+xml", ".xhtml")
        mimetype_initialised = True

    return mimetypes.guess_type(extension)


def create_pagebreak(
    pageref, label: Optional[str] = None, html: bool = True
) -> Union[bytes, Element]:
    from ebooklib.epub import NAMESPACES

    pageref_attributes: Dict[str, str] = {
        "{%s}type" % NAMESPACES["EPUB"]: "pagebreak",
        "title": f"{pageref}",
        "id": f"{pageref}",
    }

    pageref_elem: Element = etree.Element(
        "span", pageref_attributes, nsmap={"epub": NAMESPACES["EPUB"]}
    )

    if label:
        pageref_elem.text = label

    if html:
        return etree.tostring(pageref_elem, encoding="unicode")

    return pageref_elem


def get_headers(elem: Element) -> Optional[str]:
    for n in range(1, 7):
        headers = elem.xpath(f"./h{n}")

        if len(headers) > 0:
            text = headers[0].text_content().strip()
            if len(text) > 0:
                return text
    return None


def get_pages(item: EpubItem) -> list:
    body: ElementTree = parse_html_string(item.get_body_content())
    pages: list = []

    for elem in body.iter():
        if "epub:type" in elem.attrib and elem.get("id") is not None:
            _text = None

            if elem.text is not None and elem.text.strip() != "":
                _text = elem.text.strip()

            if _text is None:
                _text = elem.get("aria-label")

            if _text is None:
                _text = get_headers(elem)

            pages.append((
                item.get_name(),
                elem.get("id"),
                _text or elem.get("id"),
            ))

    return pages


def get_pages_for_items(items: List[EpubItem]) -> list:
    pages_from_docs: List[list] = [get_pages(item) for item in items]

    return [item for pages in pages_from_docs for item in pages]
