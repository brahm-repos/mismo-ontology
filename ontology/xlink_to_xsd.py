from lxml import etree as ET
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef, BNode
from rdflib.namespace import XSD, DC, SKOS

class XLinkXSDToTurtle:
    def __init__(self, xsd_path, graph):
        self.xsd_path = xsd_path
        self.g = graph
        # self.XLINK = Namespace("http://www.w3.org/1999/xlink#")
        xkink_path = dict(graph.namespace_manager.namespaces()).get("xlink")
        if xkink_path:
            self.XLINK = Namespace(xkink_path)
        else:
            print("WARNING: XLink namespace not found in graph, using default.")
            self.XLINK = Namespace("http://www.w3.org/1999/xlink#")
            self.g.bind("xlink", self.XLINK)

        # self.XML = Namespace("http://www.w3.org/XML/1998/namespace#")
        xml_path = dict(graph.namespace_manager.namespaces()).get("xml")
        if xml_path:
            self.XML = Namespace(xml_path)
            self.g.bind("xml", self.XML)
        else:
            print("WARNING: XML namespace not found in graph, using default.")
            self.XML = Namespace("http://www.w3.org/XML/1998/namespace#")   

        # self.DC = DC
        # self.SKOS = SKOS
        # self.g.bind("rdf", RDF)
        # self.g.bind("rdfs", RDFS)
        # self.g.bind("owl", OWL)
        # self.g.bind("xsd", XSD)
        # self.g.bind("xlink", self.XLINK)
        # self.g.bind("xml", self.XML)
        # self.g.bind("dc", DC)
        # self.g.bind("skos", SKOS)

        xs_namespace = dict(graph.namespace_manager.namespaces()).get("xs")
        if xs_namespace is None:
            print("Warning: 'xs' namespace not found in graph. Using default.")
            xs_namespace = "http://www.w3.org/2001/XMLSchema"
            self.g.bind("xs", Namespace(xs_namespace))

        self.NSMAP = {'xs': xs_namespace}        
        
        # self.NSMAP = {'xs': "http://www.w3.org/2001/XMLSchema"}


    def add_ontology_header(self):
        ontology_uri = URIRef(str(self.XLINK))
        self.g.add((ontology_uri, RDF.type, OWL.Ontology))
        self.g.add((ontology_uri, RDFS.label, Literal("XLink Namespace Schema", lang="en")))
        self.g.add((ontology_uri, DC.description, Literal(
            "Version: 3.6.0 Build: B367 Date: 2024-05-01.\n"
            "Copyright 2025 Mortgage Industry Standards Maintenance Organization, Inc. All Rights Reserved. (MISMO IPR Policy details omitted for brevity but noted).\n"
            "This schema document provides attribute declarations and attribute group, complex type and simple type definitions which can be used in the construction of user schemas to define the structure of particular linking constructs.",
            lang="en"
        )))
        self.g.add((ontology_uri, OWL.imports, URIRef(str(self.XML))))
        #self.g.add((ontology_uri, OWL.imports, self.XML))

    def transform_simple_types_to_turtle_rdf(self, root, graph=None, ns=None):
        """
        Transforms XSD simpleType definitions to Turtle RDF.
        Adds log statements showing processing levels.
        """
        import logging
        from rdflib import RDF, RDFS, OWL, BNode, Literal, Namespace

        logger = logging.getLogger(__name__)

        # Get namespaces from graph or use defaults
        xsd_ns = dict(graph.namespace_manager.namespaces()).get('xsd', "http://www.w3.org/2001/XMLSchema")
        xsd = Namespace(xsd_ns if xsd_ns.endswith('#') else xsd_ns + '#')
        mismo_ns = dict(graph.namespace_manager.namespaces()).get('mismo', "http://www.mismo.org/residential/2009/schemas")
        mismo = Namespace(mismo_ns if mismo_ns.endswith('#') else mismo_ns + '#')


        # Collect all simpleType nodes by name for quick lookup and order
        simple_types = []
        simple_types_by_name = {}
        for st in root.findall('xs:simpleType', self.NSMAP):
            print(f"Caching simpleType name: {st.get('name')}...")
            name = st.get("name")
            if name:
                simple_types.append((name, st))
                simple_types_by_name[name] = st

        # Process in reverse order
        for st_name, st_node in reversed(simple_types):
            print(f"Processing simpleType: {st_name}...")
            logger.info(f"Started: Processing simpleType: {st_name}...")
            st_uri = ns[st_name]

            # Handle <xs:union memberTypes="...">
            union = st_node.find('xs:union', self.NSMAP)
            if union is not None:
                print(f"\t {st_name} is a union...")
                member_types = union.get("memberTypes", "")
                member_types_list = member_types.split()
                union_bnode = BNode()
                graph.add((st_uri, RDF.type, RDFS.Datatype))
                graph.add((st_uri, OWL.equivalentClass, union_bnode))
                graph.add((union_bnode, RDF.type, RDFS.Datatype))
                # Build RDF list for owl:unionOf
                union_list = BNode()
                graph.add((union_bnode, OWL.unionOf, union_list))
                current = union_list
                for i, mt in enumerate(member_types_list):
                    # Use XSD namespace for native types, else ex namespace
                    if mt.startswith("xlink:"):
                        mt_uri = getattr(XSD, mt.split(":")[1])
                    else:
                        mt_uri = ns[mt]
                    next_b = BNode() if i < len(member_types_list) - 1 else RDF.nil
                    graph.add((current, RDF.first, mt_uri))
                    graph.add((current, RDF.rest, next_b))
                    current = next_b
                print(f"\t union is processed and continue to next node...")
                continue

            restriction = st_node.find('xs:restriction', self.NSMAP)
            if restriction is None:
                print(f"\t ERROR 1 - {st_name} has no restriction...possible new pattern")
                print(f"\t ERROR 1 - {st_node} has no restriction...possible new pattern")
                continue


            base = restriction.get("base")
            base_short = base.split(":")[-1] if ":" in base else base
            print(f"\t Restriction base type is : base: {base} base_short: {base_short}")

            # Pattern-002: restriction base is another simpleType, with enumerations
            if base_short in simple_types_by_name:
                logger.info(f"\t {st_name} is a restriction of another simpleType: {base_short}...")
                # Add the class for the base type
                class_uri = mismo[st_name]
                graph.add((class_uri, RDF.type, OWL.Class))
                # Add rdfs:subClassOf triple (assuming mismo-ont:MISMO-3.6 is the superclass)
                graph.add((class_uri, RDFS.subClassOf, mismo['MISMO-3.6']))
                # Add rdfs:label (with spaces between words)
                label = " ".join([w if w.isupper() else w.capitalize() for w in st_name.replace('_', ' ').split()])
                graph.add((class_uri, RDFS.label, Literal(label)))

                # Handle enumerations
                for enum in restriction.findall('xs:enumeration', self.NSMAP):
                    enum_value = enum.get('value')
                    # Individual URI: use base name for all except "Other"
                    if enum_value == "Other":
                        individual_uri = mismo[f"{st_name}-Other"]
                    else:
                        individual_uri = mismo[enum_value]
                    graph.add((individual_uri, RDF.type, OWL.NamedIndividual))
                    graph.add((individual_uri, RDF.type, class_uri))
                    # Label: add spaces between words
                    enum_label = " ".join([w if w.isupper() else w.capitalize() for w in enum_value.replace('_', ' ').split()])
                    graph.add((individual_uri, RDFS.label, Literal(enum_label)))
                    # Definition (if present)
                    annotation = enum.find('xs:annotation/xs:documentation', self.NSMAP)
                    if annotation is not None and annotation.text:
                        graph.add((individual_uri, SKOS.definition, Literal(annotation.text.strip())))

            # Pattern-001: restriction base is xsd-native-base-types
            else:  # must be base=<nativeDataType> 
                # remvoe: base in xsd_native_base_types or ("xs:" + base_short) in xsd_native_base_types:
                # Find maxLength or other restrictions
                print(f"\t {st_name} is a restriction of a native type...")
                restrictions = []
                for child in restriction:
                    tag = ET.QName(child.tag).localname
                    b = BNode()
                    val = child.get("value")
                    if tag == "enumeration":
                        print(f"\t enumeration: {val} added to restrictions for {st_name}")
                    elif tag == "pattern":
                        if val is not None:
                            graph.add((b, XSD.pattern, Literal(val)))
                            # graph.add((b, URIRef(str(XSD) + tag), Literal(val, datatype=getattr(XSD, base_short))))
                            restrictions.append(b)
                        else:
                            print(f"\t ERROR 3 - {st_name} {tag} has no value in {base_short}")
                            continue                    
                    elif tag in ("fractionDigits", "totalDigits", "length", "minLength", "maxLength"):
                        # b = BNode()
                        # val = child.get("value")
                        if val is not None:
                            # graph.add((b, URIRef(str(XSD) + tag), xsd.nonNegativeInteger))
                            graph.add((b, URIRef(str(XSD) + tag), Literal(val, datatype=xsd.nonNegativeInteger)))
                            restrictions.append(b)
                        else:
                            print(f"\t ERROR 3 - {st_name} {tag} has no value in {base_short}")
                            continue
                    elif tag in ("minInclusive", "maxInclusive", "minExclusive", "maxExclusive"):
                        # b = BNode()
                        # val = child.get("value")
                        if val is not None:
                            graph.add((b, URIRef(str(XSD) + tag), Literal(val, datatype=getattr(XSD, base_short))))
                            restrictions.append(b)
                        else:   
                            print(f"\t ERROR 4 - {st_name} {tag} has no value in {base_short}")
                            continue
                    else:
                        print(f"ERROR 2 - Unhandled restriction: {st_name} {tag} in {base_short}")
                        # print(f"ERROR 2 - {child} in {base_short}")
                        # print(f"ERROR 2 - {st_name} in {base_short}")
                        continue

                graph.add((st_uri, RDF.type, RDFS.Datatype))
                graph.add((st_uri, RDFS.label, Literal(st_name )))
                eq_bnode = BNode()
                graph.add((st_uri, OWL.equivalentClass, eq_bnode))
                graph.add((eq_bnode, RDF.type, RDFS.Datatype))
                graph.add((eq_bnode, OWL.onDatatype, getattr(XSD, base_short)))

                # Add owl:withRestrictions list if any restrictions found
                if restrictions:
                    from rdflib.collection import Collection
                    restrictions_list = BNode()
                    Collection(graph, restrictions_list, restrictions)
                    graph.add((eq_bnode, OWL.withRestrictions, restrictions_list))
            logger.info(f"Completed: Processing simpleType: {st_name}...")
        return graph

    def process_simple_types(self, root):
        for st in root.findall('xs:simpleType', self.NSMAP):
            name = st.get("name")
            if not name:
                continue
            st_uri = self.XLINK[name]
            self.g.add((st_uri, RDF.type, RDFS.Datatype))
            self.g.add((st_uri, RDFS.label, Literal(name, lang="en")))
            annotation = st.find('xs:annotation/xs:documentation', self.NSMAP)
            if annotation is not None:
                self.g.add((st_uri, RDFS.comment, Literal(annotation.text.strip(), lang="en")))
            restriction = st.find('xs:restriction', self.NSMAP)
            union = st.find('xs:union', self.NSMAP)
            if restriction is not None:
                base = restriction.get("base")
                if base:
                    base_uri = getattr(XSD, base.split(":")[-1], None)
                    if base_uri:
                        self.g.add((st_uri, OWL.onDatatype, base_uri))
                enums = restriction.findall('xs:enumeration', self.NSMAP)
                patterns = restriction.findall('xs:pattern', self.NSMAP)
                minLength = restriction.find('xs:minLength', self.NSMAP)
                if enums or patterns or minLength is not None:
                    restr_list = BNode()
                    self.g.add((st_uri, OWL.withRestrictions, restr_list))
                    cur = restr_list
                    for enum in enums:
                        enum_val = enum.get("value")
                        enum_bnode = BNode()
                        self.g.add((enum_bnode, XSD.enumeration, Literal(enum_val)))
                        self.g.add((cur, RDF.first, enum_bnode))
                        next_bnode = BNode()
                        self.g.add((cur, RDF.rest, next_bnode))
                        cur = next_bnode
                    for pat in patterns:
                        pat_val = pat.get("value")
                        pat_bnode = BNode()
                        self.g.add((pat_bnode, XSD.pattern, Literal(pat_val)))
                        self.g.add((cur, RDF.first, pat_bnode))
                        next_bnode = BNode()
                        self.g.add((cur, RDF.rest, next_bnode))
                        cur = next_bnode
                    if minLength is not None:
                        min_val = minLength.get("value")
                        min_bnode = BNode()
                        self.g.add((min_bnode, XSD.minLength, Literal(min_val, datatype=XSD.nonNegativeInteger)))
                        self.g.add((cur, RDF.first, min_bnode))
                        next_bnode = BNode()
                        self.g.add((cur, RDF.rest, next_bnode))
                        cur = next_bnode
                    self.g.add((cur, RDF.rest, RDF.nil))
            elif union is not None:
                member_types = union.get("memberTypes")
                if member_types:
                    union_bnode = BNode()
                    self.g.add((st_uri, OWL.unionOf, union_bnode))
                    types = [self.XLINK[t.strip().split(":")[-1]] for t in member_types.split()]
                    cur = union_bnode
                    for t_uri in types:
                        self.g.add((cur, RDF.first, t_uri))
                        next_bnode = BNode()
                        self.g.add((cur, RDF.rest, next_bnode))
                        cur = next_bnode
                    self.g.add((cur, RDF.rest, RDF.nil))

    def process_attributes(self, root):
        for attr in root.findall('xs:attribute', self.NSMAP):
            name = attr.get("name")
            if not name:
                continue
            attr_uri = self.XLINK[name]
            self.g.add((attr_uri, RDF.type, RDF.Property))
            self.g.add((attr_uri, RDF.type, OWL.DatatypeProperty))
            self.g.add((attr_uri, RDFS.label, Literal(f"{name} attribute", lang="en")))
            annotation = attr.find('xs:annotation/xs:documentation', self.NSMAP)
            if annotation is not None:
                self.g.add((attr_uri, RDFS.comment, Literal(annotation.text.strip(), lang="en")))
            attr_type = attr.get("type")
            if attr_type:
                self.g.add((attr_uri, RDFS.range, self.XLINK[attr_type.split(":")[-1]]))

    def process_attribute_groups(self, root):
        for ag in root.findall('xs:attributeGroup', self.NSMAP):
            name = ag.get("name")
            if not name:
                continue
            ag_uri = self.XLINK[name]
            self.g.add((ag_uri, RDF.type, RDFS.Resource))
            self.g.add((ag_uri, RDFS.label, Literal(f"{name} attribute group", lang="en")))
            annotation = ag.find('xs:annotation/xs:documentation', self.NSMAP)
            if annotation is not None:
                self.g.add((ag_uri, RDFS.comment, Literal(annotation.text.strip(), lang="en")))
            for attr in ag.findall('xs:attribute', self.NSMAP):
                ref = attr.get("ref")
                if ref:
                    self.g.add((ag_uri, RDFS.member, self.XLINK[ref.split(":")[-1]]))

    def process_complex_types(self, root):
        for ct in root.findall('xs:complexType', self.NSMAP):
            name = ct.get("name")
            if not name:
                continue
            ct_uri = self.XLINK[name]
            self.g.add((ct_uri, RDF.type, OWL.Class))
            self.g.add((ct_uri, RDFS.label, Literal(f"{name} XLink type", lang="en")))
            annotation = ct.find('xs:annotation/xs:documentation', self.NSMAP)
            if annotation is not None:
                self.g.add((ct_uri, RDFS.comment, Literal(annotation.text.strip(), lang="en")))

    def process_elements(self, root):
        for el in root.findall('xs:element', self.NSMAP):
            name = el.get("name")
            if not name:
                continue
            el_uri = self.XLINK[name]
            self.g.add((el_uri, RDF.type, OWL.Class))
            self.g.add((el_uri, RDFS.label, Literal(f"{name} element", lang="en")))
            annotation = el.find('xs:annotation/xs:documentation', self.NSMAP)
            if annotation is not None:
                self.g.add((el_uri, RDFS.comment, Literal(annotation.text.strip(), lang="en")))

    def process(self):
        tree = ET.parse(self.xsd_path)
        root = tree.getroot()
        #self.add_ontology_header()
        #self.process_simple_types(root)
        print("START")
        self.transform_simple_types_to_turtle_rdf(root, self.g, self.XLINK)
        self.process_attributes(root)
        self.process_attribute_groups(root)
        self.process_complex_types(root)
        self.process_elements(root)

if __name__ == "__main__":
    from rdflib import Graph
    xsd_path = r"c:\Users\brahmeswara.y\Downloads\mismo-3.6-xml-fliles\xlinkMISMOB367.xsd"
    output_ttl_path = "xlink-xsd.ttl"
    g = Graph()
    XLinkXSDToTurtle(xsd_path, g).process()
    with open(output_ttl_path, "w", encoding="utf-8") as fout:
        fout.write(g.serialize(format="turtle"))
    print(f"Turtle written to {output_ttl_path}")