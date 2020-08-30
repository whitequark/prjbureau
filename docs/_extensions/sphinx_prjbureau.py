from docutils import nodes, utils
from sphinx.util.nodes import split_explicit_title


def setup(app):
    app.add_role('fa', fa_role)
    app.add_role('wiki', wiki_role)
    app.add_crossref_type(
        directivename='fuse',
        rolename='fuse',
        indextemplate='',
        ref_nodeclass=nodes.literal
    )
    app.add_generic_role('pin', nodes.strong)


def fa_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    classes = [f"fa-{klass.strip()}" for klass in text.split(',')]
    node = nodes.emphasis(classes=['fa', *classes])
    return [node], []


def wiki_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    has_explicit, title, target = split_explicit_title(text)
    title = utils.unescape(title)
    target = utils.unescape(target)
    node = nodes.reference(title, title,
        refuri=f"https://en.wikipedia.org/wiki/{target}", **options)
    return [node], []
