from itertools import count
from itertools import islice
import math
from pydoc import doc
import requests
import time
import csv
import os
from bs4 import BeautifulSoup
from typing import Counter
from asyncio.windows_events import NULL
from webcrawler.page import Page


class Crawler:
    def __init__(self) -> None:
        self.report_info = []
        self.disallowed_url_arr = []
        self.seed_count = 0
        self.word_count = {}
        self.page_rank_dic = {}
        self.soup = None
        self.domain_url = ''
        self.depth = 0
        # list of all the pages crawled
        self.pages = []

        # For indexing
        self.indexed_words_dict = {}
        self.document_length_dict = {}

        # Check if the repository folder exists, if it doesnt make it
        self.savePath = os.path.dirname(
            os.path.abspath(__file__)) + "\\repository\\"
        if not os.path.exists(self.savePath):
            os.makedirs(self.savePath)

    def initialize(self, domain_url, depth):
        self.domain_url = domain_url
        self.depth = int(depth)

    def crawl(self):
        debug = True
        depth = 0
        visited = []

        # Check robots.txt for any restricted pages
        # Add url to the queue
        queue = []

        # delete all current files in repository
        for file in os.listdir(self.savePath):
            os.remove(self.savePath + file)

        domain = self.domain_url.split("/")[2]
        queue.append(self.domain_url)

        session = requests.Session()
        session.headers.update({'Host': domain,
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                'Connection': 'keep-alive',
                                'Pragma': 'no-cache',
                                'Cache-Control': 'no-cache'})

        while((depth < self.depth) or (len(queue) == 0)):
            depth += 1
            num_outLinks = 0
            page_name = str(depth) + ".html"
            currentUrl = queue.pop(0)

            if(debug):
                print("requesting: " + currentUrl)
            visited.append(currentUrl)

            try:
                # get the current page's html
                page = session.get(currentUrl, timeout=5)
                # save the current page's html to the repositroy folder
                completePath = os.path.normpath(
                    self.savePath + page_name)
                with open(completePath, 'w', encoding="utf-8") as file:
                    file.write(page.text)

            except requests.exceptions.Timeout:
                num_try = 0
                while(num_try < 5):
                    time.sleep(5)
                    page = session.get(currentUrl, timeout=10)
                    completePath = os.path.normpath(
                        self.savePath + page_name)
                    with open(completePath, 'w', encoding="utf-8") as file:
                        file.write(page.text)

                    if(page is not NULL):
                        break
                    num_try += 1
            except requests.exceptions.TooManyRedirects:
                print('Bad url')
            except requests.exceptions.RequestException as e:
                raise SystemExit(e)

            soup = BeautifulSoup(page.text, 'html.parser')
            outlinks = soup.find_all("a", href=True)

            # call split on link for # and only check first half
            # ex https://docs.python-requests.org/en/latest/#the-contributor-guide
            # ignore #the-contributor-guide and just go to https://docs.python-requests.org/en/latest/

            _outlinks = list()
            for tag in outlinks:
                link = tag["href"]
                # if the tag doesnt have an href skip it
                if not link:
                    pass
                # If the tag just has a comment instead of an actual link skip it
                elif link[0] == "#":
                    #print("skipping " + link["href"])
                    pass
                # ex of split: link.split("/") = ['https:', '', 'www.cpp.edu', 'index.shtml']
                elif link[0:4] == "http":
                    num_outLinks += 1
                    if(domain == link.split("/")[2]):
                        #print("adding " + link["href"])
                        _outlinks.append(link)
                        if((link not in visited) and (link not in queue)):
                            queue.append(link)

                else:
                    #print("appending then adding " + link["href"])
                    if(link.split(":")[0] == "mailto"):
                        # Skip any links that are just email addresses
                        continue
                    # Link in this case is not a direct link, looks something like this /blog_portal/category/fashion/ranking/
                    # domain would just be ameblo.jp
                    # sometimes need to add the starting /
                    if(link[0] != "/"):
                        link = "/" + link
                    newLink = "https://" + domain + link
                    num_outLinks += 1
                    if((newLink not in visited) and (newLink not in queue)):
                        queue.append(newLink)
                    _outlinks.append(newLink)
            self.pages.append(
                Page(page_name, currentUrl, _outlinks))
        print('done with crawl...')

    # returns a list of pages that link to page
    def pages_linking_to(self, page):
        pages = []
        for _page in self.pages:
            if _page.links_to(page):
                pages.append(_page)
        return pages

    def calc_page_rank(self, page):
        page_rank = 0
        # loop through all pages linking to this page and add their page_rank
        for page_linking in self.pages_linking_to(page):
            page_rank += page_linking.get_page_rank()

        return page_rank

    # give initial pagerank value to all pages
    def set_initial_pagerank_values(self):
        for page in self.pages:
            page.set_page_rank(1 / len(self.pages))

    def page_rank(self):
        self.set_initial_pagerank_values()

        is_delta_greater = True
        epsilon = 0.2
        delta = 100
        iteration = 0
        info = ''
        # while delta is greater for any page; continue calculating page rank (convergence)
        while(is_delta_greater == True and iteration < 10):
            is_delta_greater = False
            info += f'\nIteration: {str(iteration)}'
            for i, page in enumerate(self.pages):
                page_rank_prev = page.page_rank
                page_rank_new = self.calc_page_rank(page)
                delta = abs(page_rank_new - page_rank_prev)
                info += f'\npagerank:: {page_rank_new}\tdelta: {delta}'
                if delta > epsilon:
                    is_delta_greater = True
            iteration += 1
        path = os.path.dirname(os.path.abspath(__file__)) + "\\info.txt"
        with open(path, 'w', encoding="utf-8") as file:
            file.write(info)

    def cal_avg_docs_length(self):
        num_docs = len(self.document_length_dict.keys())
        total_word_count = 0

        for val in self.document_length_dict.values():
            total_word_count += val

        return (total_word_count / num_docs)

    def get_ni(self, word):
        try:
            return len(self.indexed_words_dict[word].keys())
        except:
            return 0

    def take(self, n, iterable):
        return list(islice(iterable, n))

    def calculate_BMI(self, search_phrase_words):
        ri = 0
        R = 0
        k1 = 1.2
        k2 = float(100)
        b = 0.75
        # total number of documents
        N = len(self.document_length_dict.keys())

        # calculate average document length
        avdl = self.cal_avg_docs_length()

        # get n for each term. The number of times each term appears accross all documents.
        # each list index corresponds to same index in search_phrase_words
        # documents_list is a list of sets. each set has the pages, word i appears in.
        n_list = list()
        documents_list = list()
        for word in search_phrase_words:
            word = word.lower()
            try:
                n_list.append(len(self.indexed_words_dict[word].keys()))
                documents_list.append(
                    set(self.indexed_words_dict[word].keys()))
            except:
                n_list.append(0)

        # create a set which is an intersection of all pages where all terms in search phrase appear.
        # we want to see which pages have all words in the search phrase
        pages_set = set()
        for i, item in enumerate(documents_list):
            if i == 0:
                pages_set = item
            else:
                pages_set = pages_set.intersection(item)

        # calculate BMI of each page that has the search phrase (i.e. contains all words in search phrase).
        # we return bmi_results which is a dictionary with page names as keys and
        # BMI scores as values
        # we assume ri and R to be zero and qfi to be 1
        bmi_results = dict()
        k_cap = 0.0
        for page in pages_set:
            bmi = 0
            # calculate K for each doc
            dl = float(self.document_length_dict[page])
            k_cap = k1 * ((1 - b) + b * (dl / avdl))
            for i, word in enumerate(search_phrase_words):
                word = word.lower()
                try:
                    fi = self.indexed_words_dict[word][page]
                except:
                    print('zero times appearing in {page}')
                    fi = 0
                ni = self.get_ni(word)
                bmi += math.log10(((0.5)/(0.5)) / ((ni + 0.5) / (N - ni + 0.5))) * \
                    (((k1 + 1) * fi) / (k_cap + fi)) * \
                    (((k2 + 1) * 1) / (k2 + 1))
            bmi_results[page] = bmi

        try:
            results = sorted(self.take(10, bmi_results.items()), reverse=True)
        except:
            results = sorted(self.take(len(bmi_results.keys()),
                                       bmi_results.items()), reverse=True)
        return results

    def index_webpages(self):
        # Create empty list for words that need to be cleaned
        word_list = []

        # loop through all .html files in repository folder. index the words and their frequencies
        path = os.path.dirname(os.path.abspath(__file__)) + "\\repository\\"
        files_list = os.listdir(path)

        for file_name in files_list:
            completePath = os.path.normpath(path + "\\" + file_name)
            with open(completePath, 'r', encoding="utf-8") as file:
                soup = BeautifulSoup(file, 'html.parser')
                tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']
                # Get text from the page
                for tag in soup.findAll(tags):
                    text = tag.text
                    words = text.lower().split()
                    # Append it to the wordlist and then clean the words of all symbols
                    for word in words:
                        word_list.append(word)
                self.clean_index_words(word_list, file_name)
                word_list.clear()

    def clean_index_words(self, words_list, file_name):
        cleaned_words_list = []

        # Clean the words from any symbols
        for word in words_list:
            symbols = '!@#$%^&*()_-+={[}]|\;:"<>?/., '
            for i in range(0, len(symbols)):
                word = word.replace(symbols[i], '')
            if len(word) > 0:
                cleaned_words_list.append(word)

        # add length of this document to the global dictionary
        self.document_length_dict[file_name] = len(cleaned_words_list)

        # index the words in this document
        for word in cleaned_words_list:
            # if word is there check if current page is recorded, if yes; increment it. If not, add the current page name
            # and set the count to 1
            if word in self.indexed_words_dict:
                if file_name in self.indexed_words_dict[word].keys():
                    self.indexed_words_dict[word][file_name] += 1
                else:
                    self.indexed_words_dict[word][file_name] = 1
            # if word is not indexed
            else:
                new_dict = dict()
                new_dict[file_name] = 1
                self.indexed_words_dict[word] = new_dict

    def init_robot_info(self, link):
        self.disallowed_url_arr.clear()
        url = link + 'robots.txt'
        robot_txt = requests.get(url, timeout=5).text

        robot_txt_lines = robot_txt.split('\n')
        if(len(robot_txt_lines) == 0):
            return

        for line in robot_txt_lines:
            line_arr = line.split(' ')
            if(len(line_arr) > 1):
                if((line_arr[0] == 'Disallow:') and (line_arr[1] is not NULL)):
                    self.disallowed_url_arr.append(line_arr[1])

    def isAllowed(self, link):
        for text in self.disallowed_url_arr:
            if(text in link):
                return False
        return True

    def RetrievePhrase(self, phrase):
        phrase_arr = phrase.split(' ')
        bmi_results = self.calculate_BMI(phrase_arr)

        # loop through the bmi_results (dic, with key=page_name name and value=bmi score),
        # for each result, find page (with same name)
        # multiply the page's page_rank with the bmi score
        final_result_dic = dict()
        for result in bmi_results:
            for page in self.pages:
                if page.name == result[0]:
                    final_result_dic[page.url] = page.page_rank * result[1]
        return final_result_dic
