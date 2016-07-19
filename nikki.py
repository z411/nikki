#!/usr/bin/env python3
# -- coding: utf-8 --

# Configuration
WLOG_TITLE = 'wlog'
WLOG_URL = '/wlog/'
SITE_URL = '/'
FORBIDDEN_CATEGORIES = ['cat']

import os
import datetime
import time
from operator import itemgetter

import mistune
from wheezy.template.engine import Engine
from wheezy.template.ext.core import CoreExtension
from wheezy.template.loader import FileLoader

MAIN_CATEGORIES = []

def parse_articles():
  articles = []
  markdown = mistune.Markdown()
  
  for root, dirs, files in os.walk("pages"):
    for name in files:
      # append article
      article = parse_page(os.path.join(root, name), markdown)
      article['fname'] = os.path.splitext(name)[0]
      if os.path.split(root)[0]:
        article['category'] = os.path.split(root)[1]
        article['url'] = '/'.join((article['category'], article['fname']))
      else:
        article['category'] = ''
        article['url'] = article['fname']
      
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
  
def parse_page(fname, markdown):
  article = {'title': '', 'date': None, 'body': '', 'cut': False}
  with open(fname) as f:
    line = f.readline().rstrip()
    while line != '':
      (cmd, val) = line.split(' ', 1)
      
      if cmd.lower() == 'title:':
        article['title'] = val
      elif cmd.lower() == 'date:':
        (article['date_str'], article['time']) = val.split(' ')
        article['date'] = parse_date(val)
        
      line = f.readline().rstrip()
    
    body = f.read().strip()
    (shorted, sep, rest) = body.partition('---CUT---')
    article['cut'] = bool(sep)
    
    article['body'] = markdown(body.replace('---CUT---', ''))
    
    if article['cut']:
      article['short'] = markdown(shorted)
    else:
      article['short'] = article['body']
    
    
  return article

def check_article(article):
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
  
  render(fname, 'article.html', context)

def generate_articles(articles, category=None):
  if category:
    mkdir('cat')
    fname = os.path.join('cat', category)
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
    'wlog_url': WLOG_URL,
    'site_url': SITE_URL,
    'categories': MAIN_CATEGORIES,
  }
  if newcontext:
    context.update(newcontext)
  
  output = template.render(context)
  
  with open("output/{}.html".format(outname), 'w') as f:
    f.write(output.encode('utf-8'))

def main():
  global MAIN_CATEGORIES
  
  print("Starting.")
  start = time.clock()
  
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
  
  print("Done. Time taken: {}".format(time.clock() - start))

main()
