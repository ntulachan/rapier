#!/usr/bin/env python 

import sys, codecs, os
import validate_rapier

class HTMLGenerator(object):

    def generate_property_cell(self, property):
        rslt = property.get('description', '')
        return rslt
    
    def create_link(self, uri_ref):
        uri_ref = self.validator.relative_url(uri_ref)
        split_ref = uri_ref.split('#')
        name = split_ref[1]
        url = split_ref[0]
        if url.endswith('.yaml'):
            split_ref[0] = url[:-4] + 'html'
            uri_ref = '#'.join(split_ref)
        return '<a href="{}">{}</a>'.format(uri_ref, name)
    
    def generate_property_type(self, property):
        if 'relationship' in property:
            relationship = property['relationship']
            if isinstance(relationship, basestring):
                entity_urls = relationship.split()
                multiplicity = '0:1'
            elif isinstance(relationship, list):
                entity_urls = relationship
                multiplicity = '0:1'                
            else:
                entity_urls = relationship['entities']
                if isinstance(entity_urls, basestring):
                    entity_urls = entity_urls.split()
                multiplicity = relationship.get('multiplicity', '0:1')
            entity_links = [self.create_link(entity_url) for entity_url in entity_urls]
            return '%s (%s)' % (multiplicity, ' or '.join(entity_links))
        type = property.get('type', '')
        if type == 'array':
            items = property['items']
            rslt = '[%s]' % self.generate_property_type(items)
        elif 'properties' in property:
            rslt = self.generate_properties_table(property['properties'])
        else:
            rslt = type
        return rslt
    
    def generate_property_rows(self, properties):
        rslt = ''
        for property_name, property in properties.iteritems():
            rslt += '''
                  <tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s                    </td>
                  </tr>''' % (property_name, self.generate_property_type(property), self.generate_property_cell(property))
        return rslt

    def generate_properties_table(self, properties):
        property_rows = self.generate_property_rows(properties)
        return '''
              <table class="table table-striped table-bordered">
                <thead>
                  <tr>
                    <th>Property Name</th>
                    <th>Property Type</th>
                    <th>Property Description</th>
                  </tr>
                </thead>
                <tbody>%s
                </tbody>
              </table>''' % property_rows

    def allOf(self, allOf):
        def replace_dot_yaml(url):
            split_url = url.split('#')
            if split_url[0].endswith('.yaml'):
                split_url[0] = split_url[0][:-4] + 'html'
                url = '#'.join(split_url)
        if len(allOf) > 1:
            rslt = '''
                <div> 
                Includes properties and other constraints from all of:
                <ul><{0}</a>
                </ul>
                </div>'''
            row = '''
                    <li>%s
                    </li>'''
            rows = [row.format(self.create_link(ref['$ref'])) for ref in allOf]
            return rslt % ''.join(rows)
        else:
            return '''
                <div> 
                Includes properties and other constraints from {0}
                </div>'''.format(self.create_link(self.entities[allOf[0]['$ref']]['id']))
             
    def generate_entity_cell(self, entity):
        rslt = entity.get('description', '')
        if 'allOf' in entity:
            rslt = rslt + self.allOf(entity['allOf'])
        properties = entity.get('properties')
        if properties is not None:
            rslt += self.generate_properties_table(properties)
        return rslt
    
    def create_anchor(self, name):
        return '<a name="{0}"></a>{0}'.format(name)
    
    def generate_entity_rows(self, entities):
        rslt = ''
        for entity_name, entity in entities.iteritems():
            rslt += '''
          <tr>
            <td>%s</td>
            <td>%s            </td>
          </tr>\n''' % (self.create_anchor(entity_name), self.generate_entity_cell(entity))
        return rslt

    def generate_entities_table(self, spec):
        entities = spec.get('entities')
        entity_rows = self.generate_entity_rows(entities) if entities is not None else ''
        return \
'''    <table class="table table-bordered">
        <thead>
            <tr>
                <th>Entity Name</th>
                <th>Entity Description</th>
            </tr>
        </thead>
        <tbody>%s
        </tbody>
    </table>''' % entity_rows
        
    def generate_html(self, filename):
        self.validator = validate_rapier.OASValidator()
        spec, errors = self.validator.validate(filename)
        if errors == 0:
            self.entities = self.validator.build_included_entity_map()
            entities = spec.get('entities')
            rslt = '''<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="http://design.apigee.com/ui-framework/latest/css/ui-framework-core.css">
  <link href='https://fonts.googleapis.com/css?family=Source+Sans+Pro:400,400italic,700,700italic,300,300italic' rel='stylesheet' type='text/css'>
</head>
<body>

  <div class="container">
    <div class="table-responsive">
    %s          
    </div>
  </div>

</body>
</html>
''' % self.generate_entities_table(spec) if entities is not None else ''
            UTF8Writer = codecs.getwriter('utf8')
            sys.stdout = UTF8Writer(sys.stdout)
            return rslt
        else:
            print >>sys.stderr, 'HTML generation of %s failed' % filename

def main(args):
    #try:
    html_generator = HTMLGenerator()
    rslt = html_generator.generate_html(*args)
    print rslt
    #except Exception as e:
    #    print >>sys.stderr, 'HTML generation of %s failed: %s' % (args, e)

if __name__ == "__main__":
    main(sys.argv[1:])
