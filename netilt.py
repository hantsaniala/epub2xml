from epub import EpubArchive, EpubPageSection
from lxml import etree

def convert_xhtml_elements(xhtml_elements):
    if xhtml_elements:
        xhtml_elements.insert(0, etree.Comment("BEGIN XHTML CONTENT"))
        xhtml_elements.append(etree.Comment("END XHTML CONTENT"))
    return xhtml_elements

def add_element_with_text(target_element, tag, text):
    elem = etree.Element(tag)
    elem.text = text
    target_element.append(elem)
    return elem

def epub_page_section_to_netilt(section, element_name, section_order):
    section_elem = etree.Element(element_name)
    if section.title is not None and section_order != 0:
        add_element_with_text(section_elem, "title", section.title)

    xhtml_elements = []
    for (index, elem) in enumerate(section.content_elements):
        if isinstance(elem, EpubPageSection):
            section_elem.extend(convert_xhtml_elements(xhtml_elements))
            xhtml_elements = []
            section_elem.append(epub_page_section_to_netilt(elem, "subsection", None))
        else:
            xhtml_elements.append(elem)
    section_elem.extend(convert_xhtml_elements(xhtml_elements))
    return section_elem

def get_netilt_doc_structure(netilt_doc):
    res = ""
    for elem in netilt_doc.iter():
        if elem.tag not in ("chapter", "page", "section", "subsection"):
            continue
        elem_string = "+--" * (len([e for e in elem.iterancestors()]) -1)
        if elem.getchildren()[0].tag == "title" and elem.getchildren()[0].text:
            elem_string = "%s%s " %(elem_string, elem.getchildren()[0].text)
        elem_string = "%s(%s)" %(elem_string, elem.tag.upper())
        res = "%s%s\n" %(res, elem_string)
    return res.encode("utf-8")


class NetiltDoc(object):
    def __init__(self, epub_filename):
        self.epub_filename = epub_filename
        self.epub_archive = None
        self.chapter_elements = {}

    def get_netilt_xml(self, use_spine_as_toc):
        self.epub_archive = EpubArchive(self.epub_filename, use_spine_as_toc)
        document = etree.Element("document")
        add_element_with_text(document, "title", self.epub_archive.title)
        add_element_with_text(document, "authors", ", ".join(self.epub_archive.authors))

        for page in self.epub_archive.pages:
            page_root_elem = self.chapter_elements.get(page.parent_page, document)
            page_elem = etree.Element("page")
            if page.children_pages:
                add_element_with_text(page_elem, "title", "Overview")
                chapter_elem = etree.Element("chapter")
                if page.get_page_title() is not None:
                    add_element_with_text(chapter_elem, "title", page.get_page_title())
                page_root_elem.append(chapter_elem)
                self.chapter_elements[page] = chapter_elem
                page_root_elem = chapter_elem
            else:
                if page.get_page_title() is not None:
                    add_element_with_text(page_elem, "title", page.get_page_title())
            page_root_elem.append(page_elem)
            for index, section in enumerate(page.sections):
                page_elem.append(epub_page_section_to_netilt(section, "section", index))
        return document

    def process(self, use_spine_as_toc):
        return etree.tostring(self.get_netilt_xml(use_spine_as_toc), xml_declaration=True, encoding="UTF-8", pretty_print=True)
