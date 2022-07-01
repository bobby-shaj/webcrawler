import math
from flask import render_template, request, redirect, url_for, flash, abort, session, jsonify, Blueprint
from webcrawler.crawler import Crawler
# from . import crawler

bp = Blueprint('webcrawler', __name__)
crawler = Crawler()


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/crawl', methods=['GET', 'POST'])
def crawl():
    if request.method == 'POST':
        crawler.initialize(request.form['url'], request.form['depth'])
        crawler.crawl()
        crawler.page_rank()
        crawler.index_webpages()
        return redirect(url_for('webcrawler.search'))
    else:
        return redirect(url_for('webcrawler.home'))


@bp.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        print('in search...')
        results = crawler.RetrievePhrase(request.form['search-phrase'])
        return render_template('search_results.html', results=results, phrase=request.form['search-phrase'])
    else:
        return render_template('search.html')


@bp.route('/search-results', methods=['GET', 'POST'])
def search_results():
    if request.method == 'POST':
        print('in search results...')
        results = crawler.RetrievePhrase(request.form['search-phrase'])
        return render_template('search_results.html', results=results, phrase=request.form['search-phrase'])
    else:
        return render_template('search.html')
