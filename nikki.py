#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "wenmode>=0.15.3",
#     "wheezy.template",
# ]
# ///

# Configuration
WLOG_TITLE = 'wlog'
WLOG_DESCRIPTION = 'Personal weblog for ramblings about tech and media.'
WLOG_URL = '/wlog/'
WLOG_AUTHOR = 'z411'
WLOG_AUTHOR_URL = '/notme'
SITE_URL = '/'
WLOG_VIA = 'z411_'
FORBIDDEN_CATEGORIES = ['img']
PRETTY_URLS = True

import os
import datetime
import time
import urllib
import re
from operator import itemgetter

from wenmode import Wenmode, HTMLRenderer
from wenmode.plugins import heading_ids
from wenmode.directives import Admonition
from wenmode.presets import commonmark
from wenmode.rules import ContainerDirective, LeafDirective, TextDirective

from wheezy.template.engine import Engine
from wheezy.template.ext.core import CoreExtension
from wheezy.template.loader import FileLoader

MAIN_CATEGORIES = []
VERSION = "0.4"

class MyFigure:
    node_type = "leafDirective"

    def __init__(self, names: Iterable[str] = ('myFigure',)) -> None:
        self.names = frozenset(names)

    def render(self, renderer, node, context) -> str:
        title = node.children[0].value
        src = node.attributes['src']
        return f"<figure><img src=\"{src}\"><figcaption>{title}</figcaption></figure>"

def parse_articles():
  articles = []

  wen = Wenmode([*commonmark(), TextDirective, LeafDirective, ContainerDirective],
                renderer=HTMLRenderer(escape=False),
                plugins=[heading_ids],
                directives=[MyFigure(), Admonition(names=['note', 'warn'])]
            )
  
  for root, dirs, files in os.walk("pages"):
    for name in files:
      # ignore hidden and non-md files
      if name.startswith(".") or not name.endswith(".md"):
        continue

      print(name)
      
      # append article
      article = parse_page(os.path.join(root, name), wen)
      article['fname'] = os.path.splitext(name)[0]

      # parse category and urls
      if os.path.split(root)[0]:
        article['category'] = os.path.split(root)[1]
        article['url'] = '/'.join((article['category'], article['fname']))
      else:
        article['category'] = ''
        article['url'] = article['fname']

      if not PRETTY_URLS:
        article['url'] += ".html"
      
      # create share links
      share_twitter_q = urllib.parse.urlencode({
        'url': WLOG_URL + article['url'],
        'via': WLOG_VIA,
        'text': article['title']
      })
      article['share_twitter'] = "https://twitter.com/intent/tweet?{}".format(share_twitter_q)

      check_article(article)
      articles.append(article)
  
  # sort articles by date
  return sorted(articles, key=itemgetter('date'), reverse=True)
  
def split_categories(articles):
  categories = {}
  for article in articles:
    cat = article['category']
    if cat:
      if cat in categories:
        categories[cat].append(article)
      else:
        categories[cat] = [article]
  return categories

def parse_date(str):
  return datetime.datetime.strptime(str, "%Y-%m-%d %H:%M")
  
def parse_page(fname, wen):
  article = {'title': '',
             'date': None,
             'body': '',
             'cut': False,
             'author': WLOG_AUTHOR,
             'author_url': WLOG_AUTHOR_URL}

  with open(fname) as f:
    line = f.readline().rstrip()
    while line != '':
      (cmd, val) = line.split(' ', 1)
      
      if cmd.lower() == 'title:':
        article['title'] = val
      elif cmd.lower() == 'date:':
        (article['date_str'], article['time']) = val.split(' ')
        article['date'] = parse_date(val)
      elif cmd.lower() == 'description:':
        article['description'] = val
      elif cmd.lower() == 'image:':
        article['image'] = val
      elif cmd.lower() == 'author:':
        article['author'] = val
      elif cmd.lower() == 'author_url:':
        article['author_url'] = val
        
      line = f.readline().rstrip()
    
    body = f.read().strip()
    (shorted, sep, rest) = body.partition('---CUT---')
    article['cut'] = bool(sep)
    
    article['body'] = wen.render(body.replace('---CUT---', ''))
    
    if article['cut']:
      shorted = re.sub(r"\[\^.*\]", "", shorted)
      article['short'] = wen.render(shorted)
    else:
      article['short'] = article['body']
    
    
  return article

def check_article(article):
  fname = article['fname']
  if not article['title']:
    raise Exception("Article {} doesn't have a title.".format(fname))
  if not article['date']:
    raise Exception("Article {} doesn't have a date.".format(fname))
  if article['category'] in FORBIDDEN_CATEGORIES:
    raise Exception("This article can't have this category.")
        
def generate_article(article):
  # create category directory if necessary
  if article['category']:
    mkdir(article['category'])
  
  fname = os.path.join(article['category'], article['fname'])
  context = {
    'title': ' // '.join((article['title'], WLOG_TITLE)),
    'article': article,
  }
  if 'description' in article:
    context['description'] = article['description']
  if 'image' in article:
    context['image'] = article['image']
  
  render(fname, 'article.html', context)

def generate_articles(articles, category=None):
  if category:
    mkdir(category)
    fname = os.path.join(category, 'index')
    title = ' // '.join((category, WLOG_TITLE))
  else:
    fname = 'index'
    title = WLOG_TITLE
    
  context = {
    'title': title,
    'articles': articles,
  }
  render(fname, 'articles.html', context)
  
def mkdir(dirname):
  try:
    os.makedirs(os.path.join('output', dirname))
  except OSError:
    pass
  
def render(outname, templatename, newcontext=None):
  engine = Engine(
    loader=FileLoader(['templates'], 'UTF-8'),
    extensions=[CoreExtension()]
  )
  template = engine.get_template(templatename)
  context = {
    'title': WLOG_TITLE,
    'description': WLOG_DESCRIPTION,
    'image': None,
    'wlog_url': WLOG_URL,
    'wlog_via': WLOG_VIA,
    'site_url': SITE_URL,
    'version': VERSION,
    'categories': MAIN_CATEGORIES,
    'article': None,
  }
  if newcontext:
    context.update(newcontext)
  
  output = template.render(context)
  
  with open("output/{}.html".format(outname), 'w') as f:
    f.write(output)

def main():
  global MAIN_CATEGORIES
  
  print("nikki v{}".format(VERSION))
  start = time.time()
  
  print("Parsing articles...")
  articles = parse_articles()
  
  print("Sorting categories...")
  categories = split_categories(articles)
  MAIN_CATEGORIES = categories.keys()
  
  print("Rendering article pages...")
  for article in articles:
    generate_article(article)
    
  print("Rendering indexes by category...")
  for catname, catlist in categories.items():
    generate_articles(catlist, catname)
    
  print("Rendering main index...")
  generate_articles(articles)
  
  print("Done. Time taken: {}".format(time.time() - start))

main()
