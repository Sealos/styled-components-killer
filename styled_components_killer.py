#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import argparse

styled_component_regex_no_capture = re.compile('const \w+ = styled\.\w+`.+?`;', re.DOTALL)
styled_component_regex_capture = re.compile('const (\w+) = styled\.(\w+)`(.+)`;', re.DOTALL)

style_identifiers = re.compile('\.\s*([\w]+[\w-]*)+')

class_name_attribute_capture = re.compile('className=(["{])`?([\w\s-]+?)`?(["}])')
class_name_attribute_no_capture = re.compile('className=["{]`?[\w\s-]+?`?["}]')

style_file_import = 'styleManual'
style_file_name = style_file_import + '.module.scss'


def lower_first(str):
    return str[0].lower() + str[1:]


def class_name_to_camel_case(string):
    if '-' not in string and '_' not in string:
        return lower_first(string)

    no_double_dash = string.replace('--', '-')

    camel_case = ''.join(x.capitalize() or '_' for x in no_double_dash.split('-'))
    return lower_first(camel_case)


def transform_class_name_attribute(class_name_attribute, class_names_replacement):
    group = class_name_attribute_capture.match(class_name_attribute).groups()
    classes_in_group = group[1].split(' ')

    classes_transformed = []

    for class_in_group in classes_in_group:
        if class_in_group in class_names_replacement:
            classes_transformed.append('${' + style_file_import + "." + class_names_replacement[class_in_group] + '}')
        else:
            print("!  Warning: using global class", class_in_group)
            classes_transformed.append(class_in_group)

    class_names_transformed = ' '.join(classes_transformed)

    transformed = "className={`" + class_names_transformed + "`}"
    return transformed


# Transforms a component by extracting the css into 2 strings
def transform_component(component_text, verbose=False):
    group = styled_component_regex_capture.match(component_text)
    component_name = group[1].strip()
    component_type = group[2].strip()
    component_style = group[3].strip()

    # In case the component uses $(props)
    if "=>" in component_text:
        if verbose:
            print('>  Skipping ' + component_name + ' because contains props')
        return

    # In case the component uses ${Mixing}
    if "${" in component_text:
        if verbose:
            print('>  Skipping ' + component_name + ' because contains mixins')
        return

    if verbose:
        print('>  Transforming ' + component_name)

    component_style_name = lower_first(component_name)

    component = """const {component_name} = (props) => {{
                  const {{children}} = props;
                  return (<{component_type} {{...props}} className={{{style_file_import}.{component_style_name}}}>
                      {{children}}
                  </{component_type}>);
              }};""".format(component_name=component_name,
                           style_file_import=style_file_import,
                           component_style_name=component_style_name,
                           component_type=component_type)

    component_style = """.{component_style_name} {{
    {component_style}
  }}
  """.format(component_style_name=component_style_name, component_style=component_style)

    return {
        "component": component,
        "component_text": component_text,
        "component_style_name": component_style_name,
        "component_style": component_style
    }


def handle_file(file_path, components, verbose=False, dry_run=False):
    if "app/pages" in file_path:
        return

    all_styles = []

    components_replacement = []

    all_styles_class_names_replacement = {}

    for component in components:
        component_style = component["component_style"]
        styles_class_names = style_identifiers.findall(component_style)

        for styles_class_name in styles_class_names:
            all_styles_class_names_replacement[styles_class_name] = class_name_to_camel_case(styles_class_name)

        all_styles.append(component_style)
        components_replacement.append([component["component_text"], component["component"], component_style])

    if verbose and False:
        for replacement in components_replacement:
            print('Replacing: ---')
            print()
            print(replacement[0])
            print()
            print('---')
            print()
            print('jsx')
            print()
            print(replacement[1])
            print()
            print('scss')
            print()
            print(replacement[2])

    path_components = file_path.split('/')
    file_name = path_components.pop()

    src_path = '/'.join(path_components)

    with open(src_path + '/' + file_name, 'r') as component_file_read:
        component_file = component_file_read.read()
        component_file_read.close()

    styled_declaration = "import styled from 'styled-components';"
    style_decl_with_import = "import styled from 'styled-components';\nimport " + style_file_import + " from './" + style_file_name + "';"
    component_file = component_file.replace(styled_declaration, style_decl_with_import)

    for replacement in components_replacement:
        component_file = component_file.replace(replacement[0], replacement[1])

    class_name_attributes = class_name_attribute_no_capture.findall(component_file)

    for class_name_attribute in class_name_attributes:
        new_class_name_attribute = transform_class_name_attribute(class_name_attribute, all_styles_class_names_replacement)
        component_file = component_file.replace(class_name_attribute, new_class_name_attribute)

    style_file_content = '\n'.join(all_styles)

    for class_replacement_original, class_replacement_new in all_styles_class_names_replacement.items():
        style_file_content = style_file_content.replace('.'+ class_replacement_original, '.'+class_replacement_new)

    if dry_run:
        return

    if file_name.endswith('style.js') or file_name.endswith('index.js') or file_name.endswith('index.jsx') or file_name.endswith('style.jsx'):

        style_file = src_path + '/' + style_file_name

        style_file_open = 'w'

        if os.path.isfile(style_file):
            style_file_open = 'a'

        with open(style_file, style_file_open) as style_file:
            style_file.write(style_file_content)
            style_file.close()

        with open(src_path + '/' + file_name, 'w') as component_file_write:
            component_file_write.write(component_file)
            component_file_write.close()
    else:
        file_dir = file_name.split('.')[0]
        file_extension = file_name.split('.')[1]
        new_folder = src_path + '/' + file_dir
        try:
            os.mkdir(new_folder)
        except FileExistsError:
            pass

        style_file = new_folder + '/' + style_file_name

        style_file_open = 'w'

        if os.path.isfile(style_file):
            style_file_open = 'a'

        with open(style_file, style_file_open) as style_file:
            style_file.write(style_file_content)
            style_file.close()

        component_file = component_file.replace("'../", "'../../")
        component_file = component_file.replace("'./style.module", "'../style.module")

        component_file = re.sub("'./([A-Z])", "'../\\1", component_file)

        with open(new_folder + '/index.jsx', 'w') as component_file_write:
            component_file_write.write(component_file)
            component_file_write.close()

        os.remove(file_path)


def process_dir(walk_dir='src', verbose=False, dry_run=False):
    # Iterate through all the files
    for root, subdirs, files in os.walk(walk_dir):
        for filename in files:
            file_path = os.path.join(root, filename)

            if file_path.endswith(".jsx") or file_path.endswith(".js"):
                with open(file_path, 'r') as f_in:
                    string = f_in.read()
                    f_in.close()
                    contains_styled = "import styled from" in string
                    styled_components_in_file = []

                    if contains_styled:
                        if verbose:
                            print(file_path)

                        if "app/pages" in file_path:
                            if verbose:
                                print('>> Requires manual rewrite')
                            continue

                        matches = styled_component_regex_no_capture.findall(string)

                        for match in matches:
                            a = transform_component(match, verbose)
                            if a is not None:
                                styled_components_in_file.append(a)

                        items_to_process_len = len(styled_components_in_file)
                        total_matches_len = len(matches)

                        if verbose:
                            if total_matches_len == 0:
                                print('>> Requires manual rewrite')
                            else:
                                print('>> Total components:', str(items_to_process_len) + '/' + str(total_matches_len))
                            print()

                        if items_to_process_len != 0:
                            handle_file(file_path, styled_components_in_file, verbose, dry_run)


def main(argv):
    parser = argparse.ArgumentParser(description='Kills styled components.')
    parser.add_argument('--dir', help='directory to run', default="src")
    parser.add_argument('--verbose', help='directory to run', action="store_true")
    parser.add_argument('--dry_run', help='runs without side effects', action="store_true")

    args = vars(parser.parse_args())

    dir = args["dir"]
    verbose = args["verbose"]
    dry_run = args["dry_run"]

    process_dir(dir, verbose, dry_run)


if __name__ == "__main__":
    main(sys.argv[1:])
