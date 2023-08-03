import re
import pandas as pd

cypher_path = "cypher.cyp"
output_path = "corrected_cypher.cyp"

try:
    with open(cypher_path, "r") as file:
        cypher_statement = file.read()
except FileNotFoundError:
    print("File not found. Please check the file path.")


def correct_cypher(schema, cypher_statement):
    new_cypher = cypher_statement
    rel_creation_attempt_pattern = r'((CREATE|MERGE) \(([\w]+)?:?[\w$]+\)\s*<?-\[([\w]+)?:?([\w$]+)?\]->?\s*\(([\w]+)?:?[\w$]+\))'
    matches = re.finditer(rel_creation_attempt_pattern, cypher_statement)
    if matches:
        for match in matches:
            match_group = match.group()
            match_span = list(match.span())

            relationship = match_group.split(' ')[1]
            print("Relationship: "+relationship)

            arrow_pattern = r'(<?-\[([\w]+)?:?([\w$]+)?\]->?)'
            arrow = next(re.finditer(arrow_pattern, relationship)).group()
            arrow_dir = detect_arrow_direction(arrow, cypher_statement)
            print('Arrow: '+arrow+', Direction: '+str(arrow_dir))

            rel_type = extract_rel_type(arrow, cypher_statement)
            print('Relationship type: '+rel_type)

            node_pattern = r'(\(([\w]+)?:?[\w$]+\))'
            nodes = list(re.finditer(node_pattern, relationship))

            (l_node, r_node) = (nodes[0].group(), nodes[1].group())
            print("Left node: "+l_node)
            print("Right node: "+r_node)
            l_node_type = extract_node_type(l_node, cypher_statement)
            r_node_type = extract_node_type(r_node, cypher_statement)
            print("Left node type: "+l_node_type)
            print("Right node type: "+r_node_type)

            try:
                if (arrow_dir == 1 and rel_type in schema[l_node_type][r_node_type]) or (arrow_dir == -1 and rel_type in schema[r_node_type][l_node_type]):
                    print("Relationship direction fits schema!")
                elif rel_type in schema[l_node_type][r_node_type] or rel_type in schema[r_node_type][l_node_type]:
                    print("Relationship direction does not fit schema but could exist, needs to be corrected.")
                    if arrow_dir == 1:
                        new_arrow = '<'+arrow[:-1]
                    elif arrow_dir == -1:
                        new_arrow = arrow[1:]+'>'
                    else:
                        if arrow[0] != '-':
                            arrow = arrow[1:-1]

                        if rel_type in schema[l_node_type][r_node_type]:
                            new_arrow = arrow+'>'
                        else:
                            new_arrow = '<'+arrow
                    print('New arrow: '+new_arrow)

                    command = 'CREATE' if match_group[:6] == 'CREATE' else 'MERGE'
                    new_match = command + ' ' + l_node + new_arrow + r_node
                    new_cypher = new_cypher.replace(match_group, new_match)
                else:
                    print("Error: One of the node or relationship types is not valid/in the schema. Review Cypher.")
                    print("Line will be commented out.")
                    new_match = '// ' + match_group
                    new_cypher = new_cypher.replace(match_group, new_match)

            except Exception as e:
                print('Error: One of the nodes or relationships types is not valid/in the schema. Review Cypher.')
                print("Line will be commented out.")
                print(f'Error code: {e}')
                new_match = '// ' + match_group
                new_cypher = new_cypher.replace(match_group, new_match)

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
    type_pattern = r'(:[\w$]+\])'
    if ':' in arrow:
        type = next(re.finditer(type_pattern, arrow)).group()[1:-1]
        print(type)
        return type
    else:
        rel_name_pattern = r'(\[[\w$]\])'
        rel_name = next(re.finditer(rel_name_pattern, arrow)).group()[1:-1]
        print('rel_name '+rel_name)
        rel_pattern = r'(\['+rel_name+':[\w$]+\])'
        matches = list(re.finditer(rel_pattern, cypher_statement))
        if matches:
            match = matches[0].group()
            if ':' in match:
                return next(re.finditer(type_pattern, match)).group()[1:-1]
        else:
            return 'No type'


# TODO: clean up the patterns
def extract_node_type(node, cypher_statement):
    type_pattern = r'(:[\w$]+\))'
    if ':' in node:
        return re.findall(type_pattern, node)[0][1:-1]
    else:
        node_name = node[1:-1]
        node_pattern = '(\('+node_name+':[\w$]+\))'
        matches = re.findall(node_pattern, cypher_statement)
        if len(matches) != 0:
            return re.findall(type_pattern, matches[0])[0][1:-1]
        else:
            return 'No type'


schema_data = {'index': ['Person', 'Movie', 'Equipment'],
               'Person': [[],['ACTED_IN','PRODUCED'],['USED']],
               'Movie': [[],[],['REQUIRED']],
               'Equipment':[[],[],[]]}

schema_df = pd.DataFrame.from_dict(schema_data).set_index('index')

corrected_cypher_statement = correct_cypher(schema_df, cypher_statement)
try:
    with open(output_path, "w") as output_file:
        output_file.write(corrected_cypher_statement)
    print("Corrected cypher written to new_cypher.cyp file.")
except Exception as e:
    print(f"Error writing to the file: {e}")