#!/usr/bin/env python3
#===========================
# move hexo blog to hugo
#===========================

from pathlib import Path
import os
import yaml
import toml
from datetime import datetime, timezone, timedelta

pwddir = Path(__file__).parent.resolve()

hexo_source = pwddir.parent.joinpath('blog/source/')
hexo_posts = pwddir.parent.joinpath('blog/source/_posts')
hugo_posts = pwddir.joinpath('content/post')
hugo_content = pwddir.joinpath('content')


def check_post(f):
    front_matter = []
    body = []
    with f.open() as pf:
        fm = True
        line = pf.readline()
        while line:
            if line.startswith('---'):
                if len(front_matter) == 0:
                    line = pf.readline()
                    continue
                else:
                    fm = False
            else:
                if fm:
                    front_matter.append(line)
                else:
                    body.append(line)
            line = pf.readline()
    return {
        'front_matter': yaml.load(''.join(front_matter), Loader=yaml.SafeLoader),
        'body': ''.join(body)
    }


def mege_content(p, type_):
    ofm = p['front_matter']
    datefmt = '%Y-%m-%d %H:%M:%S'
    tzinfo = timezone(timedelta(hours=8))
    dt = ofm['date']
    if isinstance(dt, str):
        dt = datetime.strptime(ofm['date'], datefmt)
    dt = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, tzinfo=tzinfo)
    upt = ofm.get('updated')
    if isinstance(upt, str):
        upt = datetime.strptime(upt, datefmt)
    tags = ofm.get('tags')
    nicename = ofm.get('nicename')
    postid = ofm.get('postid')
    categories = ofm.get('categories')
    toc = p.get('toc', False)
    nfm = {
        'title': ofm['title'],
        'postid': int(postid),
        'aliases': ['/post/{0}.html'.format(ofm['postid'])],
        'date': dt,
        'isCJKLanguage': True,
        'toc': toc,
        'type': type_,
    }
    nfm['slug'] = str(nicename) if nicename else str(postid)
    if categories is not None:
        nfm['categories'] = [categories]
    if tags is not None:
        nfm['tags'] = tags
    if upt is not None:
        upt = datetime(upt.year, upt.month, upt.day, upt.hour, upt.minute, upt.second, tzinfo=tzinfo)
        nfm['lastmod'] = upt
    if ofm.get('attachments'):
        nfm['attachments'] = ofm['attachments']
    front_matter_toml = toml.dumps(nfm)
    return '+++\n%s+++\n\n%s' % (front_matter_toml, p['body'])
    

def build_posts():
    i = 0
    error_posts = []
    for p in os.listdir(hexo_posts):
        if not p.endswith('.md'):
            continue
        print('perform ', i, p)
        f = hexo_posts.joinpath(p)
        post_data = check_post(f)
        try:
            s = mege_content(post_data, 'post')
            hugef = hugo_posts.joinpath(p)
            hugef.write_text(s, encoding='utf8')
        except Exception as e:
            error_posts.append({'name': p, 'error': e})
            print('%s error %s' %(p, e))
            continue
        i += 1
    print(len(error_posts))


def build_pages():
    i = 0
    error_pages = []
    for p in os.listdir(hexo_source):
        if p.startswith('.') or p.startswith('_') or p in ('search', 'uploads', 'tag', 'category', 'link'):
            continue
        page_file = hexo_source.joinpath(p, 'index.md')
        page_data = check_post(page_file)
        print('perform ', i, page_file)
        try:
            s = mege_content(page_data, 'page')
            hugef = hugo_content.joinpath(p+'.md')
            hugef.write_text(s, encoding='utf8')
        except Exception as e:
            error_pages.append({'name': p, 'error': e})
            print('%s error %s' %(p, e))
            continue
        i += 1
    print(len(error_pages))

# build_posts()
build_pages()