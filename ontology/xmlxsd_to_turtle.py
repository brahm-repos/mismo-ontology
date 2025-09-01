from lxml import etree as ET
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef, BNode
from rdflib.namespace import XSD

class XMLXSDToTurtle:
    def __init__(self, xml_xsd_path, g=None):
        self.xml_xsd_path = xml_xsd_path
        #self.output_ttl_path = output_ttl_path

        if ( g is None):
            self.g = Graph()
            print("Graph is created")
            self.g.bind("rdf", RDF)
            self.g.bind("rdfs", RDFS)
            self.g.bind("owl", OWL)
            self.g.bind("xsd", XSD)
            self.g.bind("xml", self.XML)
            self.g.bind("xs", Namespace("http://www.w3.org/2001/XMLSchema#"))
            self.g.bind("xml", Namespace("http://www.w3.org/XML/1998/namespace#"))
        else:
            self.g = g  
            print("Graph is already created")

        # Get namespaces from graph by prefix, with fallback defaults
        xs_ns = dict(g.namespace_manager.namespaces()).get('xs')
        if xs_ns is None:
            print("Warning: 'xs' namespace not found in graph. Using default.")
            xs_ns = "http://www.w3.org/2001/XMLSchema"

        xml_ns = dict(g.namespace_manager.namespaces()).get('xml')
        if xml_ns is None:
            print("Warning: 'xml' namespace not found in graph. Using default.")
            xml_ns = "http://www.w3.org/XML/1998/namespace"

        self.NSMAP = {'xs': xs_ns}
        self.XML = Namespace(xml_ns + "#")

        # self.NSMAP = {'xs': "http://www.w3.org/2001/XMLSchema"}
        # self.XML = Namespace("http://www.w3.org/XML/1998/namespace#")


    def get_graph(self):
        return self.g

    def add_ontology_header(self, ontology_uri, label, comment, version_info, see_also=[]):
        self.g.add((ontology_uri, RDF.type, OWL.Ontology))
        self.g.add((ontology_uri, RDFS.label, Literal(label, lang="en")))
        self.g.add((ontology_uri, RDFS.comment, Literal(comment, lang="en")))
        self.g.add((ontology_uri, OWL.versionInfo, Literal(version_info, lang="en")))
        for uri in see_also:
            self.g.add((ontology_uri, RDFS.seeAlso, URIRef(uri)))

    def process_xml_lang(self, node):
        prop = self.XML["lang"]
        self.g.add((prop, RDF.type, RDF.Property))
        self.g.add((prop, RDF.type, OWL.DatatypeProperty))
        self.g.add((prop, RDFS.label, Literal("lang", lang="en")))
        self.g.add((prop, RDFS.comment, Literal(
            "Denotes an attribute whose value is a language code for the natural language of the content of any element; its value is inherited. This name is reserved by virtue of its definition in the XML specification.\n"
            "Notes:\n"
            "Attempting to install the relevant ISO 2- and 3-letter codes as the enumerated possible values is probably never going to be a realistic possibility.\n"
            "See BCP 47 (http://www.rfc-editor.org/rfc/bcp/bcp47.txt) and the IANA language subtag registry (http://www.iana.org/assignments/language-subtag-registry) for further information.\n"
            "The union allows for the 'un-declaration' of xml:lang with the empty string.", lang="en"
        )))
        union_bnode = BNode()
        self.g.add((prop, RDFS.range, union_bnode))
        self.g.add((union_bnode, RDF.type, RDFS.Datatype))
        union_list = BNode()
        self.g.add((union_bnode, OWL.unionOf, union_list))
        restriction_bnode = BNode()
        self.g.add((restriction_bnode, RDF.type, RDFS.Datatype))
        self.g.add((restriction_bnode, OWL.onDatatype, XSD.string))
        restr_list = BNode()
        self.g.add((restriction_bnode, OWL.withRestrictions, restr_list))
        enum_bnode = BNode()
        self.g.add((enum_bnode, XSD.enumeration, Literal("")))
        self.g.add((restr_list, RDF.first, enum_bnode))
        self.g.add((restr_list, RDF.rest, RDF.nil))
        self.g.add((union_list, RDF.first, XSD.language))
        rest2 = BNode()
        self.g.add((union_list, RDF.rest, rest2))
        self.g.add((rest2, RDF.first, restriction_bnode))
        self.g.add((rest2, RDF.rest, RDF.nil))

    def process_xml_space(self, node):
        prop = self.XML["space"]
        self.g.add((prop, RDF.type, RDF.Property))
        self.g.add((prop, RDF.type, OWL.DatatypeProperty))
        self.g.add((prop, RDFS.label, Literal("space", lang="en")))
        self.g.add((prop, RDFS.comment, Literal(
            "Denotes an attribute whose value is a keyword indicating what whitespace processing discipline is intended for the content of the element; its value is inherited. This name is reserved by virtue of its definition in the XML specification.", lang="en"
        )))
        range_bnode = BNode()
        self.g.add((prop, RDFS.range, range_bnode))
        self.g.add((range_bnode, RDF.type, RDFS.Datatype))
        self.g.add((range_bnode, OWL.onDatatype, XSD.NCName))
        restr_list = BNode()
        self.g.add((range_bnode, OWL.withRestrictions, restr_list))
        enum1 = BNode()
        enum2 = BNode()
        self.g.add((enum1, XSD.enumeration, Literal("default")))
        self.g.add((enum2, XSD.enumeration, Literal("preserve")))
        self.g.add((restr_list, RDF.first, enum1))
        rest2 = BNode()
        self.g.add((restr_list, RDF.rest, rest2))
        self.g.add((rest2, RDF.first, enum2))
        self.g.add((rest2, RDF.rest, RDF.nil))

    def process_xml_base(self, node):
        prop = self.XML["base"]
        self.g.add((prop, RDF.type, RDF.Property))
        self.g.add((prop, RDF.type, OWL.DatatypeProperty))
        self.g.add((prop, RDFS.label, Literal("base", lang="en")))
        self.g.add((prop, RDFS.comment, Literal(
            "Denotes an attribute whose value provides a URI to be used as the base for interpreting any relative URIs in the scope of the element on which it appears; its value is inherited. This name is reserved by virtue of its definition in the XML Base specification.\n"
            "See http://www.w3.org/TR/xmlbase/ for information about this attribute.", lang="en"
        )))
        self.g.add((prop, RDFS.range, XSD.anyURI))

    def process_xml_id(self, node):
        prop = self.XML["id"]
        self.g.add((prop, RDF.type, RDF.Property))
        self.g.add((prop, RDF.type, OWL.DatatypeProperty))
        self.g.add((prop, RDFS.label, Literal("id", lang="en")))
        self.g.add((prop, RDFS.comment, Literal(
            "Denotes an attribute whose value should be interpreted as if declared to be of type ID. This name is reserved by virtue of its definition in the xml:id specification.\n"
            "See http://www.w3.org/TR/xml-id/ for information about this attribute.", lang="en"
        )))
        self.g.add((prop, RDFS.range, XSD.ID))

    def process_attribute_group_specialAttrs(self, node):
        # group = self.XML["specialAttrs"]
        # self.g.add((group, RDF.type, RDFS.Resource))
        # self.g.add((group, RDFS.label, Literal("specialAttrs", lang="en")))
        # self.g.add((group, RDFS.comment, Literal(
        #     "Attribute group for common XML attributes (xml:base, xml:lang, xml:space, xml:id).\n"
        #     "Usage: This schema defines attributes and an attribute group suitable for use by schemas wishing to allow xml:base, xml:lang, xml:space or xml:id attributes on elements they define.\n"
        #     "To enable this, such a schema must import this schema for the XML namespace (e.g., <import namespace=\"http://www.w3.org/XML/1998/namespace\" schemaLocation=\"http://www.w3.org/2001/xml.xsd\"/>).\n"
        #     "Subsequently, qualified reference to any of the attributes or the group defined will have the desired effect (e.g., <attributeGroup ref=\"xml:specialAttrs\"/>).", lang="en"
        # )))
        # self.g.add((group, RDFS.member, self.XML["base"]))
        # self.g.add((group, RDFS.member, self.XML["lang"]))
        # self.g.add((group, RDFS.member, self.XML["space"]))
        # self.g.add((group, RDFS.member, self.XML["id"]))
        return

    def process_father_reservation(self):
        res = self.XML["FatherReservation"]
        self.g.add((res, RDF.type, RDFS.Resource))
        self.g.add((res, RDFS.label, Literal("XML Father Reservation", lang="en")))
        self.g.add((res, RDFS.comment, Literal(
            'In appreciation for his vision, leadership and dedication the W3C XML Plenary on this 10th day of February, 2000, reserves for Jon Bosak in perpetuity the XML name "xml:Father".', lang="en"
        )))

    def process(self):
        tree = ET.parse(self.xml_xsd_path)
        root = tree.getroot()

        # Ontology header
        ontology_uri = URIRef(str(self.XML))
        label = "XML Namespace Schema"
        doc = ""
        version_info = ""
        see_also = []
        for ann in root.findall('xs:annotation', self.NSMAP):
            for doc_el in ann.findall('xs:documentation', self.NSMAP):
                doc_text = "".join(doc_el.itertext()).strip()
                if "versioning" in doc_text.lower():
                    version_info += doc_text + "\n"
                else:
                    doc += doc_text + "\n"
                for a in doc_el.findall('.//a'):
                    href = a.get("href")
                    if href:
                        see_also.append(href)
        #self.add_ontology_header(ontology_uri, label, doc.strip(), version_info.strip(), see_also)

        # Process attributes
        for attr in root.findall('xs:attribute', self.NSMAP):
            name = attr.get("name")
            if name == "lang":
                continue
                # self.process_xml_lang(attr)
            elif name == "space":
                continue 
                # self.process_xml_space(attr)
            elif name == "base":
                continue
                # self.process_xml_base(attr)
            elif name == "id":
                continue
                # self.process_xml_id(attr)

        # Process attributeGroup
        for ag in root.findall('xs:attributeGroup', self.NSMAP):
            if ag.get("name") == "specialAttrs":
                self.process_attribute_group_specialAttrs(ag)

        # Add Father reservation as a resource
        self.process_father_reservation()



if __name__ == "__main__":
    xml_xsd_path = r"c:\Users\brahmeswara.y\Downloads\mismo-3.6-xml-fliles\xml.xsd"
    output_ttl_path = "xml-xsd.ttl"
    g = Graph()
    xmlxsd=XMLXSDToTurtle(xml_xsd_path, g)
    xmlxsd.process()
    #g = xmlxsd.get_graph()
    # Output Turtle
    with open(output_ttl_path, "w", encoding="utf-8") as fout:
        fout.write(g.serialize(format="turtle"))
    print(f"Turtle written to {output_ttl_path}")