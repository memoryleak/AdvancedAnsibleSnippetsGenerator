#!/usr/bin/env python3
# Based on https://github.com/h-hirokawa/atom-autocomplete-ansible/blob/master/libs/parse_ansible.py

# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
from tqdm import tqdm
from ansible.cli.doc import DocCLI
from ansible.errors import AnsibleParserError
from ansible.plugins.loader import fragment_loader
from ansible.plugins.loader import module_loader
from ansible.utils import plugin_docs
from jinja2 import Environment, FileSystemLoader, select_autoescape

USE_FRAGMENT_LOADER = True

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape()
)

tpl_snippet = env.get_template("snippet.yml.j2")
tpl_sublime = env.get_template("sublime.xml.j2")
tpl_code = env.get_template("code.json.j2")
tpl_code_merged = env.get_template("code-merged.json.j2")
doc_cli = DocCLI(['ansible snippet generator'])

PATH_BUILD = 'build'
PATH_YAML = os.path.join(PATH_BUILD, 'yaml')
PATH_SUBLIME = os.path.join(PATH_BUILD, 'sublime')
PATH_CODE = os.path.join(PATH_BUILD, 'code')
PATH_PACKAGES = os.path.join(PATH_BUILD, 'packages')
PATH_EXTRAS = os.path.join('extras')


def get_module_list():
    module_paths = module_loader._get_paths()
    for path in module_paths:
        try:
            founds = doc_cli.find_plugins(path, 'module')
        except TypeError:
            founds = doc_cli.find_plugins(path, 'plugins', 'module')
        if founds:
            doc_cli.plugin_list.update(founds)
    module_list = doc_cli.plugin_list
    return sorted(set(module_list))


def ansible_filter(text):
    text_type = type(text).__name__

    if text_type == 'AnsibleSequence':
        if len(text) > 0:
            text = text[0]
        else:
            text = "No description available"

    text = text.split('.')[0]
    text = text.replace("\"", "'")
    text = text.replace('\\', '\\\\')
    return text


def ansible_tags(module):
    tags = module.split(".")

    if tags[0] == 'ansible':
        return tags[-1:]

    return tags


# Option description filter for jinja2 template
def ansible_option_description(index, description):
    description = ansible_filter(description['description'])
    return "${{{}:{}}}".format(index, '# ' + description)


def create_yaml(module, doc):
    snippet_yaml_path = os.path.join(PATH_YAML, module + ".yml")
    snippet_rendered = tpl_snippet.render(
        module_doc=doc,
        module=module,
        ansible_option_description=ansible_option_description,
        ansible_filter=ansible_filter,
        ansible_tags=ansible_tags
    )
    with open(snippet_yaml_path, 'w') as snippet_yaml_file:
        snippet_yaml_file.write(snippet_rendered)

    create_sublime_snippet(module, doc['short_description'], snippet_rendered)


def create_sublime_snippet(module, description, snippet):
    snippet_sublime_path = os.path.join(PATH_SUBLIME, module + ".sublime-snippet")
    snippet_rendered = tpl_sublime.render(
        module_snippet=snippet,
        module=module,
        module_description=description,
        ansible_filter=ansible_filter
    )
    with open(snippet_sublime_path, 'w') as snippet_file:
        snippet_file.write(snippet_rendered)


def create_code_snippet(module, description, snippet):
    snippet_code_path = os.path.join(PATH_CODE, module + ".json")
    snippet_rendered = tpl_code.render(
        module_snippet=snippet,
        module=module,
        module_description=description,
        ansible_filter=ansible_filter
    )

    with open(snippet_code_path, 'w') as snippet_file:
        snippet_file.write(snippet_rendered)


def create_code_merged(snippets):
    snippet_rendered = tpl_code_merged.render(
        snippets=snippets
    )

    with open(os.path.join(PATH_CODE, 'ansible.json'), 'w') as snippet_file:
        snippet_file.write(snippet_rendered)


def main():
    #parse_ansible_modules()

    yaml_snippets = [os.path.join(PATH_EXTRAS, f) for f in os.listdir(PATH_EXTRAS) if
                     os.path.isfile(os.path.join(PATH_EXTRAS, f))]
    yaml_snippets.extend(
        [os.path.join(PATH_YAML, f) for f in os.listdir(PATH_YAML) if os.path.isfile(os.path.join(PATH_YAML, f))])

    for module in tqdm(yaml_snippets, desc="Editor Snippets"):
        module_name = os.path.basename(module).split('/')[-1]
        module_name = '.'.join(module_name.split('.')[0:-1])

        with open(module, 'r') as yaml_file:
            content = yaml_file.readlines()
            create_sublime_snippet(module_name, module_name, content)
            create_code_snippet(module_name, module_name, content)

    code_snippets = [os.path.join(PATH_CODE, f) for f in os.listdir(PATH_CODE) if
                     os.path.isfile(os.path.join(PATH_CODE, f))]

    snippets = []

    for module in tqdm(code_snippets, desc="Merge Code Snippets"):
        with open(module, 'r') as code_file:
            content = code_file.readlines()
            snippets.append(content)

    create_code_merged(snippets)


def parse_ansible_modules():
    with tqdm(get_module_list(), desc="Ansible YAML Snippets") as modules:
        for module in modules:
            filename = module_loader.find_plugin(module, mod_type='.py')
            if filename is None:
                continue
            if filename.endswith(".ps1"):
                continue
            if os.path.isdir(filename):
                continue

            get_docstring_args = (filename, fragment_loader)
            try:
                doc = plugin_docs.get_docstring(*get_docstring_args)[0]
            except AnsibleParserError as e:
                print("Error getting documentation for '{}'".format(module))
                continue

            create_yaml(module, doc)


if __name__ == '__main__':
    os.makedirs(PATH_YAML, exist_ok=True)
    os.makedirs(PATH_SUBLIME, exist_ok=True)
    os.makedirs(PATH_CODE, exist_ok=True)
    os.makedirs(PATH_PACKAGES, exist_ok=True)
    main()
