import re
import pandas as pd


def correct_cypher(schema, cypher_statement, correct_statement):
    new_cypher = cypher_statement
    node_pattern = r'\(([\w]+)?:?[\w$]+(\s{.*})?\)'
    arrow_pattern = r'<?-\[([\w]+)?:?([\w$]+)?(\s{.*})?\]->?'
    rel_pattern = node_pattern+r'\s*'+arrow_pattern+r'\s*'+node_pattern+r'(\s*'+arrow_pattern+r'\s*'+node_pattern+r')?'
    matches = list(re.finditer(rel_pattern, cypher_statement))
    if matches:
        for match in matches:
            relationship = match if isinstance(match, str) else match.group()

            if relationship.count('-') > 2:
                relation_bits = relationship.split(')')
                relationship1 = relation_bits[0] + ')' + relation_bits[1] + ')'
                relationship2 = '(' + relation_bits[1].split('(')[1] + ')' + relation_bits[2] + ')'
                relationship = relationship1
                matches.append(relationship2)

            print(relationship)

            try:
                arrow = next(re.finditer(arrow_pattern, relationship)).group()
            except:
                print('No arrows found - check cypher.')

            arrow_dir = detect_arrow_direction(arrow, cypher_statement)
            print('Arrow: '+arrow+', Direction: '+str(arrow_dir))

            rel_type = extract_rel_type(arrow, cypher_statement)

            nodes = list(re.finditer(node_pattern, relationship))
            l_node = nodes[0].group()
            r_node = nodes[1].group()
            l_node_type = extract_node_type(l_node, cypher_statement)
            r_node_type = extract_node_type(r_node, cypher_statement)

            schemas = schema.split('), ')
            for index, schema in enumerate(schemas):
                if index != len(schemas)-1:
                    schemas[index] = schema+')'
            if (arrow_dir == 1 and '('+l_node_type+', '+rel_type+', '+r_node_type+')' in schemas) or (arrow_dir == -1 and '('+r_node_type+', '+rel_type+', '+l_node_type+')' in schemas):
                print('Relationship fits schema.')
            else:
                if (arrow_dir == 1 and '('+r_node_type+', '+rel_type+', '+l_node_type+')' in schemas) or (arrow_dir == -1 and '('+l_node_type+', '+rel_type+', '+r_node_type+')' in schemas):
                    print('Direction change needed.')
                    if arrow_dir == 1:
                        new_arrow = '<'+arrow[:-1]
                    else:
                        new_arrow = arrow[1:]+'>'

                    print('New arrow: '+new_arrow)
                    new_rel = l_node + new_arrow + r_node
                    new_cypher = new_cypher.replace(relationship, new_rel)
                elif arrow_dir == 0:
                    print('No direction given in query; no changes are made.')
                else:
                    print('Relationship does not fit schema - watch out. No modifications made.')

    print(new_cypher == correct_statement)
    print()
    return new_cypher



def detect_arrow_direction(arrow, cypher_statement):
    if arrow[0] == '<' and arrow[-1] != '>':
        return -1
    elif arrow[0] != '<' and arrow[-1] == '>':
        return 1
    else:
        return 0


def extract_rel_type(arrow, cypher_statement):
    type_pattern = r'(:[\w$]+(\s{.*})?\])'
    if ':' in arrow:
        type = next(re.finditer(type_pattern, arrow)).group()[1:-1].split(' ')[0]
        return type
    else:
        rel_name_pattern = r'(\[[\w$](\s{.*})?\])'
        rel_name = next(re.finditer(rel_name_pattern, arrow)).group()[1:-1]
        rel_pattern = r'(\['+rel_name+':[\w$]+(\s{.*})?\])'
        matches = list(re.finditer(rel_pattern, cypher_statement))
        if matches:
            match = matches[0].group()
            if ':' in match:
                return next(re.finditer(type_pattern, match)).group()[1:-1].split(' ')[0]
        else:
            return 'No type'


# TODO: clean up the patterns
def extract_node_type(node, cypher_statement):
    type_pattern = r'(:[\w$]+(\s{.*})?\))'
    if ':' in node:
        return re.findall(type_pattern, node)[0][0][1:-1].split(' ')[0]
    else:
        node_name = node[1:-1]
        node_pattern = '(\('+node_name+':[\w$]+(\s{.*})?\))'
        matches = list(re.findall(node_pattern, cypher_statement))
        if len(matches) != 0:
            print(matches[0][0])
            node_type = re.findall(type_pattern, matches[0][0])[0][0][1:-1].split(' ')[0]
            return node_type
        else:
            return 'No type'


test_dataset = pd.read_csv('cypher_examples.csv')
for row in test_dataset.iterrows():
    print(row[1][0])
    corrected_row = correct_cypher(row[1][1], row[1][0], row[1][2])
