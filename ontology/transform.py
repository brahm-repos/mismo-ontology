from lxml import etree as ET
import os
import sys
import logging
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, URIRef, BNode
from rdflib.namespace import XSD, SKOS

from xmlxsd_to_turtle import XMLXSDToTurtle
from xlink_to_xsd import XLinkXSDToTurtle

class XSDTransformer:
    ##logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    def __init__(self, main_xsd, output_ttl_path="trf_output.ttl", skip_import=False):
        self.logger = logging.getLogger(__name__)
        self.main_xsd = main_xsd
        self.output_ttl_path = output_ttl_path
        self.skip_import = skip_import
        self.g = Graph()
        self.complex_type_names = []
        self.ns = Namespace("http://www.mismo.org/residential/2009/schemas#")
        self.NSMAP = {'xsd': "http://www.w3.org/2001/XMLSchema"}
        self._bind_namespaces()

    def _bind_namespaces(self):
        self.g.bind("xml", "http://www.w3.org/XML/1998/namespace")
        self.g.bind("xlink", "http://www.w3.org/1999/xlink")
        self.g.bind("dct", "http://purl.org/dc/terms/")
        self.g.bind("skos", "http://www.w3.org/2004/02/skos/core#")
        self.g.bind("mismo", "http://www.mismo.org/residential/2009/schemas#")
        self.g.bind("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        self.g.bind("xsd", "http://www.w3.org/2001/XMLSchema")
        self.g.bind("xs", "http://www.w3.org/2001/XMLSchema")
        self.g.bind("owl", "http://www.w3.org/2002/07/owl#")
        self.g.bind("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
        xsd_ns = dict(self.g.namespace_manager.namespaces()).get('xsd', "http://www.w3.org/2001/XMLSchema")
        self.xsd = Namespace(xsd_ns if xsd_ns.endswith('#') else xsd_ns + '#')
        mismo_ns = dict(self.g.namespace_manager.namespaces()).get('mismo', "http://www.mismo.org/residential/2009/schemas")
        self.mismo = Namespace(mismo_ns if mismo_ns.endswith('#') else mismo_ns + '#')

    def log_element(self, node, schema_path, level, msg="Processing"):
        tag = ET.QName(node.tag).localname
        name = node.get("name") or node.get("ref") or ""
        indent = "  " * level
        self.logger.info(f"{indent}{msg} {tag}: {name} (from {schema_path})")

    # def process_attribute(self, node, schema_path, level, parent_class=None):
    #     self.log_element(node, schema_path, level)
    #     name = node.get("name")
    #     ref = node.get("ref")
    #     attr_type = node.get("type")
    #     indent = "  " * level

    #     if ref == "xml:lang" or name == "lang":
    #         prop = self.ns["lang"]
    #         self.g.add((prop, RDF.type, RDF.Property))
    #         self.g.add((prop, RDFS.label, Literal("xml:lang")))
    #         self.g.add((prop, RDFS.range, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#langString")))
    #         print(f"{indent}Added RDF property for xml:lang")
    #         if parent_class:
    #             self.g.add((prop, RDFS.domain, self.ns[parent_class]))
    #             print(f"{indent}Added domain ex:{parent_class} for ex:lang")
    #     else:
    #         prop_name = ref or name
    #         if prop_name:
    #             prop = self.ns[prop_name]
    #             self.g.add((prop, RDF.type, RDF.Property))
    #             self.g.add((prop, RDFS.label, Literal(prop_name)))
    #             # TODO: Add range/domain logic if needed
    #             print(f"{indent}Added RDF property for {prop_name}")
    #             if parent_class:
    #                 self.g.add((prop, RDFS.domain, self.ns[parent_class]))
    #                 print(f"{indent}Added domain ex:{parent_class} for {prop_name}")

    # def process_attribute_group(self, node, schema_path, level, parent_class=None):
    #     self.log_element(node, schema_path, level)
    #     name = node.get("name")
    #     ref = node.get("ref")
    #     indent = "  " * level

    #     if name == "lang" or ref == "xml:lang":
    #         prop = self.ns["lang"]
    #         self.g.add((prop, RDF.type, RDF.Property))
    #         self.g.add((prop, RDFS.label, Literal("xml:lang")))
    #         self.g.add((prop, RDFS.range, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#langString")))
    #         print(f"{indent}Added RDF property for xml:lang (attributeGroup)")
    #         if parent_class:
    #             self.g.add((prop, RDFS.domain, self.ns[parent_class]))
    #             print(f"{indent}Added domain ex:{parent_class} for ex:lang (attributeGroup)")
    #     else:
    #         group_name = name or ref
    #         if group_name:
    #             print(f"{indent}Attribute group: {group_name}")
    #             # Optionally, process child attributes here

    # def process_simple_type(self, node, schema_path, level):
    #     self.log_element(node, schema_path, level)
    #     # TODO: Add your transformation logic here

    # def process_complex_type(self, node, schema_path, level):
    #     self.log_element(node, schema_path, level)
    #     # TODO: Add your transformation logic here

    # def process_element(self, node, schema_path, level):
    #     self.log_element(node, schema_path, level)
    #     # TODO: Add your transformation logic here

    # def process_group(self, node, schema_path, level):
    #     self.log_element(node, schema_path, level)
    #     # TODO: Add your transformation logic here

    # def process_annotation(self, node, schema_path, level):
    #     self.log_element(node, schema_path, level)
    #     # TODO: Add your transformation logic here

    def process_import(self, node, schema_path, processed_files, level):
        self.log_element(node, schema_path, level)
        schema_location = node.get('schemaLocation')
        if not schema_location:
            self.logger.info(f"{'  ' * (level+1)}Import in {schema_path} has no schemaLocation, skipping.")
            return
        base_dir = os.path.dirname(schema_path)
        import_path = os.path.normpath(os.path.join(base_dir, schema_location))
        if import_path in processed_files:
            self.logger.info(f"{'  ' * (level+1)}Already processed {import_path}, skipping.")
            return
        print(f"{'  ' * (level+1)}Processing import: {import_path}")

        if "xml.xsd" in os.path.basename(import_path):
            self.logger.info(f"{'  ' * (level+1)}Processing xml.xsd with XMLXSDToTurtle...")
            xmlxsd = XMLXSDToTurtle(import_path, self.g)
            xmlxsd.process()
            self.logger.info(f"{'  ' * (level+1)}Completed processing xml.xsd")
        elif "xlinkMISMOB367.xsd" in os.path.basename(import_path):
            print(f"{'  ' * (level+1)}Processing xlink.xsd with XLinkXSDToTurtle...")
            xlinkxsd = XLinkXSDToTurtle(import_path, self.g)
            xlinkxsd.process()
            self.logger.info(f"{'  ' * (level+1)}Completed processing xlink.xsd")
        else:
            self.logger.error(f"{'  ' * (level+1)}Unhandled import file...{import_path}")
            # Optionally, process other imports



    def process_imports(self, xsd_path, processed_files=None, level=0):
        if processed_files is None:
            processed_files = set()
        if xsd_path in processed_files:
            return {}
        processed_files.add(xsd_path)
        print(f"\n{'  '*level}=== Processing XSD: {xsd_path} ===")
        tree = ET.parse(xsd_path)
        root = tree.getroot()

        # mismo_ns = dict(self.g.namespace_manager.namespaces()).get('mismo', "http://www.mismo.org/residential/2009/schemas")
        # mismo = self.mismo

        for imp in root.findall('xsd:import', self.NSMAP):
            self.process_import(imp, xsd_path, processed_files, level+1)
        for inc in root.findall('xsd:include', self.NSMAP):
            self.process_import(inc, xsd_path, processed_files, level+1)




        # tag_dict = {}
        # for node in root:
        #     # Skip comments and other non-element nodes
        #     if not isinstance(node.tag, str):
        #         continue
        #     tag = ET.QName(node.tag).localname
        #     if tag == "import":
        #         self.process_import(node, xsd_path, processed_files, level+1)
        #     else:
        #         name = node.get("name") or node.get("ref") or ""
        #         if tag not in tag_dict:
        #             tag_dict[tag] = []
        #         tag_dict[tag].append(name)
        # return tag_dict

    def transform_simple_types_to_turtle_rdf(self,root):
        """
        Transforms XSD simpleType definitions to Turtle RDF.
        Adds log statements showing processing levels.
        """

        logger = logging.getLogger(__name__)

        # Get namespaces from graph or use defaults
        # xsd_ns = dict(self.g.namespace_manager.namespaces()).get('xsd', "http://www.w3.org/2001/XMLSchema")
        # xsd = Namespace(xsd_ns if xsd_ns.endswith('#') else xsd_ns + '#')
        # mismo_ns = dict(self.g.namespace_manager.namespaces()).get('mismo', "http://www.mismo.org/residential/2009/schemas")
        # mismo = Namespace(mismo_ns if mismo_ns.endswith('#') else mismo_ns + '#')
        xsd = self.xsd
        mismo = self.mismo


        # Collect all simpleType nodes by name for quick lookup and order
        simple_types = []
        simple_types_by_name = {}
        for st in root.findall('xsd:simpleType', self.NSMAP):
            name = st.get("name")
            if name:
                simple_types.append((name, st))
                simple_types_by_name[name] = st

        # Process in reverse order
        for st_name, st_node in reversed(simple_types):

            st_uri = self.mismo[st_name]
            logger.info(f"Started: Processing simpleType: {st_name}...")

            # Handle <xsd:union memberTypes="...">
            union = st_node.find('xsd:union', self.NSMAP)
            if union is not None:
                print(f"\t {st_name} is a union...")
                member_types = union.get("memberTypes", "")
                member_types_list = member_types.split()
                union_bnode = BNode()
                self.g.add((st_uri, RDF.type, RDFS.Datatype))
                self.g.add((st_uri, OWL.equivalentClass, union_bnode))
                self.g.add((union_bnode, RDF.type, RDFS.Datatype))
                # Build RDF list for owl:unionOf
                union_list = BNode()
                self.g.add((union_bnode, OWL.unionOf, union_list))
                current = union_list
                for i, mt in enumerate(member_types_list):
                    # Use XSD namespace for native types, else ex namespace
                    if mt.startswith("xsd:"):
                        mt_uri = getattr(XSD, mt.split(":")[1])
                    else:
                        mt_uri = self.mismo[mt]
                    next_b = BNode() if i < len(member_types_list) - 1 else RDF.nil
                    self.g.add((current, RDF.first, mt_uri))
                    self.g.add((current, RDF.rest, next_b))
                    current = next_b
                print(f"\t union is processed and continue to next node...")
                continue

            restriction = st_node.find('xsd:restriction', self.NSMAP)
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
                class_uri = self.mismo[st_name]
                self.g.add((class_uri, RDF.type, OWL.Class))
                # Add rdfs:subClassOf triple (assuming mismo-ont:MISMO-3.6 is the superclass)
                self.g.add((class_uri, RDFS.subClassOf, self.mismo['MISMO-3.6']))
                # Add rdfs:label (with spaces between words)
                label = " ".join([w if w.isupper() else w.capitalize() for w in st_name.replace('_', ' ').split()])
                self.g.add((class_uri, RDFS.label, Literal(label)))

                # Handle enumerations
                for enum in restriction.findall('xsd:enumeration', self.NSMAP):
                    enum_value = enum.get('value')
                    # Individual URI: use base name for all except "Other"
                    if enum_value == "Other":
                        individual_uri = self.mismo[f"{st_name}-Other"]
                    else:
                        individual_uri = self.mismo[enum_value]
                    self.g.add((individual_uri, RDF.type, OWL.NamedIndividual))
                    self.g.add((individual_uri, RDF.type, class_uri))
                    # Label: add spaces between words
                    enum_label = " ".join([w if w.isupper() else w.capitalize() for w in enum_value.replace('_', ' ').split()])
                    self.g.add((individual_uri, RDFS.label, Literal(enum_label)))
                    # Definition (if present)
                    annotation = enum.find('xsd:annotation/xsd:documentation', self.NSMAP)
                    if annotation is not None and annotation.text:
                        self.g.add((individual_uri, SKOS.definition, Literal(annotation.text.strip())))

            # Pattern-001: restriction base is xsd-native-base-types
            else:  # must be base=<nativeDataType> 
                # remvoe: base in xsd_native_base_types or ("xsd:" + base_short) in xsd_native_base_types:
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
                            self.g.add((b, XSD.pattern, Literal(val)))
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
                            self.g.add((b, URIRef(str(XSD) + tag), Literal(val, datatype=xsd.nonNegativeInteger)))
                            restrictions.append(b)
                        else:
                            print(f"\t ERROR 3 - {st_name} {tag} has no value in {base_short}")
                            continue
                    elif tag in ("minInclusive", "maxInclusive", "minExclusive", "maxExclusive"):
                        # b = BNode()
                        # val = child.get("value")
                        if val is not None:
                            self.g.add((b, URIRef(str(XSD) + tag), Literal(val, datatype=getattr(XSD, base_short))))
                            restrictions.append(b)
                        else:   
                            print(f"\t ERROR 4 - {st_name} {tag} has no value in {base_short}")
                            continue
                    else:
                        print(f"ERROR 2 - Unhandled restriction: {st_name} {tag} in {base_short}")
                        # print(f"ERROR 2 - {child} in {base_short}")
                        # print(f"ERROR 2 - {st_name} in {base_short}")
                        continue

                self.g.add((st_uri, RDF.type, RDFS.Datatype))
                self.g.add((st_uri, RDFS.label, Literal(st_name )))
                eq_bnode = BNode()
                self.g.add((st_uri, OWL.equivalentClass, eq_bnode))
                self.g.add((eq_bnode, RDF.type, RDFS.Datatype))
                self.g.add((eq_bnode, OWL.onDatatype, getattr(XSD, base_short)))

                # Add owl:withRestrictions list if any restrictions found
                if restrictions:
                    from rdflib.collection import Collection
                    restrictions_list = BNode()
                    Collection(self.g, restrictions_list, restrictions)
                    self.g.add((eq_bnode, OWL.withRestrictions, restrictions_list))
            logger.info(f"Completed: Processing simpleType: {st_name}...")
        return self.g


    def init_complex_type_names(self, root):
        self.complex_type_names = []
        for ct in root.findall('xsd:complexType', self.NSMAP):
            ct_name = ct.get("name")
            if not ct_name:
                continue
            self.complex_type_names.append(ct_name)

    def is_complex_type(self, type_name):
        """
        Check if a type name exists in the complex_type_names list
        Args:
            type_name (str): The type name to check
        Returns:
            bool: True if type_name exists in self.complex_type_names, False otherwise
        """
        return type_name in self.complex_type_names
    
    def create_owl_class(self, class_uri,  subclass_of=None, class_label=None, class_comment=None):
        """
        Creates an OWL class with the given URI, name, and optional comment.
        Adds the class to the RDF graph.
        """
        self.g.add((class_uri, RDF.type, OWL.Class))


        if subclass_of:
            self.g.add((class_uri, RDFS.subClassOf, subclass_of))

        if class_label:
            self.g.add((class_uri, RDFS.label, Literal(class_label)))

        if class_comment:
            self.g.add((class_uri, RDFS.comment, Literal(class_comment)))

        # self.g.add((class_uri, RDFS.subClassOf, self.mismo['MISMO-3.6']))
    
    def is_ignorable_type(self, type_name):
        """
        Check if a string should be ignored based on specific patterns
        Args:
            type_name (str): The string to check
        Returns:
            bool: True if text equals 'MISMO_BASE' or ends with 'EXTENSION' or ends with '_OTHER_BASE', False otherwise
        """
        if type_name == "MISMO_BASE":
            return True
        if type_name.endswith("EXTENSION"):
            return True
        if type_name.endswith("_OTHER_BASE"):
            return True
        return False

    def transform_complex_type_with_attributes_only(self, ct, ct_name, ct_uri):
        print(f"\tPattern 009: Only Attributes..Creating OWL class for {ct_name}...")
        class_comment = ct.find('xsd:annotation/xsd:documentation', self.NSMAP)
        self.create_owl_class(
            class_uri=ct_uri,
            subclass_of=self.mismo['MISMO-3.6'],
            class_label=ct_name.replace('_', ' ').title(),
            class_comment=class_comment
        )

        # Handle attributes of the compelx type
        for attribute in ct.findall('xsd:attribute', self.NSMAP):
            attr_name = attribute.get('name')
            print(f"\t\t Processing attribute: {attr_name}  of {ct_name}...")
            if not attr_name:
                continue
            prop_uri = self.mismo[attr_name]

            attr_type = attribute.get('type')
            if attr_type:
                print(f"\t\t\t Attribute type: {attr_type} for {attr_name} in {ct_name}")
                # Property URI
                prop_uri = self.mismo[f"has{attr_name}"]
                print(f"\t\t\t Property URI: {prop_uri}")
                # Property label and comment
                # prop_label = f"has{attr_name}"
                el_annotation = attribute.find('xsd:annotation/xsd:documentation', self.NSMAP)
                prop_comment = el_annotation.text.strip() if el_annotation is not None and el_annotation.text else None

                # Add property triples
                if (self.is_complex_type(attr_type)):
                    self.g.add((prop_uri, RDF.type, OWL.ObjectProperty))
                else:
                    self.g.add((prop_uri, RDF.type, OWL.DatatypeProperty))

                if prop_comment:
                    self.g.add((prop_uri, RDFS.comment, Literal(prop_comment)))

                self.g.add((prop_uri, RDFS.domain, ct_uri))
                self.g.add((prop_uri, RDFS.range, self.mismo[attr_type]))

    def transform_complex_types_to_turtle_rdf(self,root):
        """
        Processes complexType elements in the XSD root and adds corresponding triples to the RDF graph
        according to patterns 003, 004, 005, and 006 as described in the prompt.
        """

        # complex_type_names = self.get_complex_type_names(root)

        for ct in root.findall('xsd:complexType', self.NSMAP):
            ct_name = ct.get("name")
            print(f"--> Processing complexType: {ct_name}...")
            if not ct_name:
                print(f"\t ERROR 1 - {ct_name} has no name...possible new pattern")
                continue

            if ( self.is_ignorable_type(ct_name) ):
                print(f"\t WARNING: Skipping complexType {ct_name} as it is not modelled and ignored...")
                continue    
                
            ct_uri = self.mismo[ct_name]

            # Get class-level documentation
            annotation = ct.find('xsd:annotation/xsd:documentation', self.NSMAP)
            class_comment = annotation.text.strip() if annotation is not None and annotation.text else None

            class_uri = self.mismo[ct_name]
            # self.g.add((class_uri, RDF.type, OWL.Class))
            # self.g.add((class_uri, RDFS.subClassOf, self.mismo['MISMO-3.6']))
            # self.g.add((class_uri, RDFS.label, Literal(ct_name)))
            # if class_comment:
            #     self.g.add((class_uri, RDFS.comment, Literal(class_comment)))

            # Pattern-003: complexType - sequence - xsd:any
            # Pattern-005 and Pattern-006: complexType - sequence - element(s) of complexType, attributeGroup, attribute with simpleType
            sequence = ct.find('xsd:sequence', self.NSMAP)
            if (sequence is not None):
                any_elem = sequence.find('xsd:any', self.NSMAP)
            else:
                any_elem = None

            simple_content = ct.find('xsd:simpleContent', self.NSMAP)
            print(f"\t sequence: {sequence}")
            print(f"\t any_elem: {any_elem}")
            print(f"\t simple_content: {simple_content}")
            # note: We are strict on defined patterns
            if ( (sequence is not None or simple_content is not None) and any_elem is None):
                print(f"\tCreating OWL class for {ct_name}...")
                self.create_owl_class(
                    class_uri=ct_uri,
                    subclass_of=self.mismo['MISMO-3.6'],
                    class_label=ct_name.replace('_', ' ').title(),
                    class_comment=class_comment
                )
            else:
                print(f"\tWARNING: New Class not created.possible xsd:any pattern-003")
        

            if sequence is not None and any_elem is not None:
                any_attr = ct.findall('xsd:attribute', self.NSMAP) 
                if ( any_attr is not None ):
                    print(f"\tPattern 009: Only Attributes..Creating OWL class for {ct_name}...")
                    self.transform_complex_type_with_attributes_only(ct, ct_name, ct_uri)
                else:
                    print(f"\t pattern-003 (ignored): {ct_name} is a sequence with xsd:any...Ignored pattern")
                
                # any_elem = sequence.find('xsd:any', self.NSMAP)
                # if any_elem is not None:
                # Pattern-003
                
                # self.g.add((ct_uri, RDF.type, OWL.Class))
                # self.g.add((ct_uri, RDFS.label, Literal(ct_name)))
                # self.g.add((ct_uri, RDFS.comment, Literal(
                #     "Open content: allows any elements from the target namespace (xsd:any, namespace=##targetNamespace, processContents=lax)."
                # )))
                continue 
            # # Handle xs:sequence/xs:element
            # sequence = ct.find('xsd:sequence', self.NSMAP)
            elif sequence is not None:
                for element in sequence.findall('xsd:element', self.NSMAP):
                    el_name = element.get('name')
                    el_type = element.get('type')
                    if not el_name or not el_type or self.is_ignorable_type(el_type):
                        print(f"\t\t WARNING: Ignoring element {el_name} with type {el_type} in {ct_name}...")
                        continue

                    # Property URI
                    prop_uri = self.mismo[f"has{el_name}"]
                    # Property label and comment
                    prop_label = f"has {el_name}"
                    el_annotation = element.find('xsd:annotation/xsd:documentation', self.NSMAP)
                    prop_comment = el_annotation.text.strip() if el_annotation is not None and el_annotation.text else None

                    # Add property triples
                    if ( self.is_complex_type(el_type) ):
                        self.g.add((prop_uri, RDF.type, OWL.ObjectProperty))
                    else:
                        self.g.add((prop_uri, RDF.type, OWL.DatatypeProperty))

                    self.g.add((prop_uri, RDFS.label, Literal(prop_label)))
                    if prop_comment:
                        self.g.add((prop_uri, RDFS.comment, Literal(prop_comment)))
                    self.g.add((prop_uri, RDFS.domain, class_uri))
                    self.g.add((prop_uri, RDFS.range, self.mismo[el_type]))

                    # attributes = element.attrib  # This is a dict of all attributes
    
                    # restriction = BNode()
                    # self.g.add((class_uri, RDFS.subClassOf, restriction))
                    # self.g.add((restriction, RDF.type, OWL.Restriction))
                    # self.g.add((restriction, OWL.onProperty, prop_uri))

                    # restrictions = []
                    # # Iterate all attributes of the element and create restrictions
                    # for attr_name, attr_value in element.attrib.items():
                    #     #restriction = BNode()
                    #     # graph.add((class_uri, RDFS.subClassOf, restriction))
                    #     # graph.add((restriction, RDF.type, OWL.Restriction))
                    #     # graph.add((restriction, OWL.onProperty, prop_uri))
                    #     # Example: handle minOccurs/maxOccurs/nillable as cardinality or annotation
                    #     if attr_name == "minOccurs":
                    #         self.g.add((restriction, OWL.minCardinality, Literal(int(attr_value), datatype=XSD.nonNegativeInteger)))
                    #         # restrictions.append(restriction)
                    #     elif attr_name == "maxOccurs":
                    #         # Handle "unbounded" as a special case if needed
                    #         if attr_value == "unbounded":
                    #             continue  # skip or handle as needed
                    #         self.g.add((restriction, OWL.maxCardinality, Literal(int(attr_value), datatype=XSD.nonNegativeInteger)))
                    #         # restrictions.append(restriction)
                    #     elif attr_name == "nillable":
                    #         # Add as annotation or custom property if desired
                    #         self.g.add((restriction, RDFS.comment, Literal(f"nillable: {attr_value}")))
                    #         # restrictions.append(restriction)
                    #     else:
                    #         if ( attr_name not in ["name", "type"]):
                    #             # Handle unhandled attributes   
                    #             print(f"ERROR - X: Unhandled attribute {attr_name} with value {attr_value} for element {el_name}")
                    #             # Generic annotation for other attributes
                    #             #graph.add((restriction, RDFS.comment, Literal(f"{attr_name}: {attr_value}")))
                    
                # Handle xs:attribute
                for attribute in ct.findall('xsd:attribute', self.NSMAP):
                    attr_name = attribute.get('name')
                    attr_type = attribute.get('type')
                    print(f"\t\t Processing attribute: {attr_name} with type {attr_type} in {ct_name}...")
                    if not attr_name or not attr_type or self.is_ignorable_type(attr_type) :
                        print(f"\t\t WARNING: Ignoring attribute {attr_name} with type {attr_type} in {ct_name}...")
                        continue

                    # Property URI
                    attr_uri = self.mismo[f"has{attr_name}"]
                    # Property label and comment
                    attr_label = f"has {attr_name}"
                    attr_annotation = attribute.find('xsd:annotation/xsd:documentation', self.NSMAP)
                    attr_comment = attr_annotation.text.strip() if attr_annotation is not None and attr_annotation.text else None

                    # Add has<attr_name> property triples
                    if (self.is_complex_type(attr_type)):
                        self.g.add((attr_uri, RDF.type, OWL.ObjectProperty))
                    else:
                        self.g.add((attr_uri, RDF.type, OWL.DatatypeProperty))

                    self.g.add((attr_uri, RDFS.label, Literal(attr_label)))
                    if attr_comment:
                        self.g.add((attr_uri, RDFS.comment, Literal(attr_comment)))

                    self.g.add((attr_uri, RDFS.domain, class_uri))
                    self.g.add((attr_uri, RDFS.range, self.mismo[attr_type]))

                    # # add has<attr_name> restriction
                    # restriction = BNode()
                    # self.g.add((class_uri, RDFS.subClassOf, restriction))
                    # self.g.add((restriction, RDF.type, OWL.Restriction))
                    # self.g.add((restriction, OWL.onProperty, attr_uri))
                    # # TO DO: Review
                    # self.g.add((restriction, OWL.maxCardinality, Literal(1, datatype=XSD.nonNegativeInteger)))

                # Handle xs:attributeGroup
                for attr_group in ct.findall('xsd:attributeGroup', self.NSMAP):
                    ref = attr_group.get('ref')
                    if not ref:
                        continue
                    if ref == "AttributeExtension" or ref.startswith("AttributeExtension:"):
                        print(f"\t\t WARNING: Ignoring Processing attributeGroup: {ref} in {ct_name}...")
                    else:
                        print(f"\t\t ERROR X: Ignoring Processing attributeGroup: {ref} in {ct_name}...")
                    
                    # # If xlink, use xlink:label as property
                    # if ref.startswith('xlink:'):
                    #     prop_uri = xlink['label']
                    # else:
                    #     prop_uri = mismo[ref]
                    # restriction = BNode()
                    # graph.add((class_uri, RDFS.subClassOf, restriction))
                    # graph.add((restriction, RDF.type, OWL.Restriction))
                    # graph.add((restriction, OWL.onProperty, prop_uri))
                    # graph.add((restriction, OWL.maxCardinality, Literal(1, datatype=XSD.nonNegativeInteger)))

                continue
            # Pattern-004: complexType - simpleContent - extension with base=simpleType & attributes of simpleType
            # simple_content = ct.find('xsd:simpleContent', self.NSMAP)
            # print(f"\t simple_content: {simple_content}")
            elif simple_content is not None:
                print(f"\t pattern-004: {ct_name} is a simpleContent with extension...")
                extension = simple_content.find('xsd:extension', self.NSMAP)
                if extension is not None:
                    # Add restriction for rdf:value someValuesFrom base
                    base_type = extension.get('base')
                    print(f"\t pattern-004: {ct_name} is a simpleContent with extension of base {base_type}...")
                    if base_type:
                        # restriction = BNode()
                        # self.g.add((class_uri, RDFS.subClassOf, restriction))
                        # self.g.add((restriction, RDF.type, OWL.Restriction))
                        # self.g.add((restriction, OWL.onProperty, RDF.value))
                        # self.g.add((restriction, OWL.someValuesFrom, self.mismo[base_type]))
                        base_prop_uri = self.mismo[f"has{ct_name}Value"]
                        self.g.add((base_prop_uri, RDF.type, OWL.DatatypeProperty)) 
                        self.g.add((base_prop_uri, RDF.type, OWL.FunctionalProperty))  # Added FunctionalProperty
                        # self.g.add((base_prop_uri, RDFS.label, Literal(f"has {ct_name} base type {base_type}")))
                        self.g.add((base_prop_uri, RDFS.domain, class_uri))
                        self.g.add((base_prop_uri, RDFS.range, self.mismo[base_type]))

                        # Property for the simpleContent's base value (the actual identifier string)
                        # mismo:hasIdentifierValue a owl:DatatypeProperty , owl:FunctionalProperty ; # Added FunctionalProperty
                        #     rdfs:domain mismo:MISMOIdentifier ;
                        #     rdfs:range mismo:MISMOIdentifier_Base ;
                        #     rdfs:comment "The actual value of the identifier, corresp

                    # Handle attributes in extension
                    for attribute in extension.findall('xsd:attribute', self.NSMAP):
                        attr_name = attribute.get('name')
                        print(f"\t\t Processing attribute: {attr_name} in extension of {ct_name}...")
                        if not attr_name:
                            continue
                        prop_uri = self.mismo[attr_name]

                        attr_type = attribute.get('type')
                        if attr_type:
                            print(f"\t\t\t Attribute type: {attr_type} for {attr_name} in {ct_name}")
                            # Property URI
                            prop_uri = self.mismo[f"has{attr_name}"]
                            print(f"\t\t\t Property URI: {prop_uri}")
                            # Property label and comment
                            prop_label = f"has {attr_name}"
                            el_annotation = attribute.find('xsd:annotation/xsd:documentation', self.NSMAP)
                            prop_comment = el_annotation.text.strip() if el_annotation is not None and el_annotation.text else None

                            # Add property triples
                            if (self.is_complex_type(attr_type)):
                                self.g.add((prop_uri, RDF.type, OWL.ObjectProperty))
                            else:
                                self.g.add((prop_uri, RDF.type, OWL.DatatypeProperty))

                            if prop_comment:
                                self.g.add((prop_uri, RDFS.comment, Literal(prop_comment)))

                            self.g.add((prop_uri, RDFS.domain, class_uri))
                            self.g.add((prop_uri, RDFS.range, self.mismo[attr_type]))
                            
                        # # Add restriction for propert name of the class 
                        # print(f"\t\t\t Adding restriction for property {prop_uri} in {ct_name}...")
                        # restriction = BNode()
                        # self.g.add((class_uri, RDFS.subClassOf, restriction))
                        # self.g.add((restriction, RDF.type, OWL.Restriction))
                        # self.g.add((restriction, OWL.onProperty, prop_uri))
                        # # TO DO: Review
                        # self.g.add((restriction, OWL.maxCardinality, Literal(1, datatype=XSD.nonNegativeInteger)))

                    # Handle attributeGroups in extension
                    for attr_group in extension.findall('xsd:attributeGroup', self.NSMAP):
                        ref = attr_group.get('ref')
                        print(f"\t\t WARNING: Ignoring Processing attributeGroup: {ref} in extension of {ct_name}...")
                        print(f"\t\t\t Note: Extension is not applicable as OWL is extendable")
                        # if not ref:
                        #     continue
                        # if ref.startswith('xlink:'):
                        #     prop_uri = xlink['label']
                        # else:
                        #     prop_uri = mismo[ref]

                        # restriction = BNode()
                        # graph.add((class_uri, RDFS.subClassOf, restriction))
                        # graph.add((restriction, RDF.type, OWL.Restriction))
                        # graph.add((restriction, OWL.onProperty, prop_uri))
                        # graph.add((restriction, OWL.maxCardinality, Literal(1, datatype=XSD.nonNegativeInteger)))

                    # # Add label and comment
                    # label = " ".join([w if w.isupper() else w.capitalize() for w in ct_name.replace('_', ' ').split()])
                    # self.g.add((class_uri, RDFS.label, Literal(label)))
                    # if class_comment:
                    #     self.g.add((class_uri, RDFS.comment, Literal(class_comment)))
                    continue
            else:
                print(f"\tPattern 009: Only Attributes..Creating OWL class for {ct_name}...")
                self.transform_complex_type_with_attributes_only(ct, ct_name, ct_uri)
                # class_comment = ct.find('xsd:annotation/xsd:documentation', self.NSMAP)
                # self.create_owl_class(
                #     class_uri=ct_uri,
                #     subclass_of=self.mismo['MISMO-3.6'],
                #     class_label=ct_name.replace('_', ' ').title(),
                #     class_comment=class_comment
                # )
                # # Assume pattern 008 : complexType has attributes only
                # # Handle attributes in extension
                # for attribute in ct.findall('xsd:attribute', self.NSMAP):
                #     attr_name = attribute.get('name')
                #     print(f"\t\t Processing attribute: {attr_name}  of {ct_name}...")
                #     if not attr_name:
                #         continue
                #     prop_uri = self.mismo[attr_name]

                #     attr_type = attribute.get('type')
                #     if attr_type:
                #         print(f"\t\t\t Attribute type: {attr_type} for {attr_name} in {ct_name}")
                #         # Property URI
                #         prop_uri = self.mismo[f"has{attr_name}"]
                #         print(f"\t\t\t Property URI: {prop_uri}")
                #         # Property label and comment
                #         # prop_label = f"has{attr_name}"
                #         el_annotation = attribute.find('xsd:annotation/xsd:documentation', self.NSMAP)
                #         prop_comment = el_annotation.text.strip() if el_annotation is not None and el_annotation.text else None

                #         # Add property triples
                #         if (self.is_complex_type(attr_type)):
                #             self.g.add((prop_uri, RDF.type, OWL.ObjectProperty))
                #         else:
                #             self.g.add((prop_uri, RDF.type, OWL.DatatypeProperty))

                #         if prop_comment:
                #             self.g.add((prop_uri, RDFS.comment, Literal(prop_comment)))

                #         self.g.add((prop_uri, RDFS.domain, class_uri))
                #         self.g.add((prop_uri, RDFS.range, self.mismo[attr_type]))
                # print(f"ERROR X - {ct_name} has no simpleContent or extension...possible new pattern")

        return self.g

    def process_root_elements(self, root ):
        
        for inc in root.findall('xsd:element', self.NSMAP):
            name = inc.get("name")
            inc_type = inc.get("type")
            print(f"Processing xsd:element {name} with type {inc_type}...")
            ct_uri = self.mismo[name]
            self.g.add((ct_uri, RDF.type, OWL.Class))
            self.g.add((ct_uri, RDFS.label, Literal(name)))
            annotation = inc.find('xsd:documentation', self.NSMAP)
            if annotation is not None and annotation.text:
                self.g.add((ct_uri, RDFS.comment, Literal(annotation.text.strip())))
            self.g.add((ct_uri, RDFS.subClassOf, self.mismo['MISMO-3.6']))

    def run(self):
        logger = logging.getLogger(__name__)
        logger.info("Starting XSD to Turtle RDF transformation...")
        logger.info(f"Processing main XSD file: {self.main_xsd}")
        
        if not self.skip_import:
            tags_dict = self.process_imports(self.main_xsd)
            logger.info(f"Completed Processing imports")
        else:
            logger.info("Skipping import processing as requested")
            
        tree = ET.parse(self.main_xsd)
        root = tree.getroot()
        self.g.add((self.mismo["MISMO-3.6"], RDF.type, OWL.Class))
        self.g.add((self.mismo["MISMO-3.6"], RDFS.label, Literal("MISMO-3.6")))
        self.process_root_elements(root)
        self.init_complex_type_names(root)
        self.transform_simple_types_to_turtle_rdf(root)
        self.transform_complex_types_to_turtle_rdf(root)
        with open(self.output_ttl_path, "w", encoding="utf-8") as fout:
            fout.write(self.g.serialize(format="turtle"))
        print(f"Turtle written to {self.output_ttl_path}")


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    if len(sys.argv) < 2:
        print("Usage: python transform.py <xsd_file> [output_ttl_file] [--skipimport]")
        sys.exit(1)

    xsd_file = sys.argv[1]
    output_file = "mismo-turtle.ttl"
    skip_import = False
    
    # Parse remaining arguments
    for i in range(2, len(sys.argv)):
        arg = sys.argv[i]
        if arg == "--skipimport":
            skip_import = True
        elif not arg.startswith("--"):
            output_file = arg
    
    logger.info(f"Processing main XSD file: {xsd_file}")
    logger.info(f"Output Turtle file: {output_file}")
    logger.info(f"Skip import processing: {skip_import}")

    transformer = XSDTransformer(xsd_file, output_file, skip_import)
    transformer.run()

if __name__ == "__main__":
    main()
