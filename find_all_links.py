#!/usr/bin/env python
from sys import argv
import requests
import bs4
from urlparse import urlparse


class Finder(object):
    """Finds all internal links on all pages within a domain."""

    def __init__(self, url):
        self.url = str(url)
        self.parsed_url = self.parse_url(url)
        self.domain = '.'.join(self.parsed_url.netloc.split('.')[-2:])
        self.links = self.find_all_links()

    def __len__(self):
        return len(self.links)

    def __iter__(self):
        return self.links.__iter__()

    @staticmethod
    def parse_url(base_url):
        # used to extract the scheme, subdomain, and domain from the url
        parsed_url = urlparse(base_url)
        return parsed_url

    def find_all_links(self):
        # finds all internal links in the whole domain
        links_to_visit = self.search_page(self.url)

        # keeps track of all urls that have been searched
        visited_urls = set()

        # search links recursively until all links have been searched
        while len(links_to_visit) > 0:
            current_page = links_to_visit.pop()
            urls = self.search_page(current_page)
            for url in urls:
                if url not in visited_urls:
                    visited_urls.add(url)

        self.links = visited_urls
        return self.links

    def search_page(self, url):
        # get all links on page at url
        print 'Finding links at %s' % url
        page_links = self.extract_page_links(url)
        cleaned_links = self.clean_links(page_links)
        links_on_page = set(cleaned_links)

        return links_on_page

    def extract_page_links(self, url):
        # use bs4 to extract all links from the page
        html_string = self.get_page(url)
        soup = bs4.BeautifulSoup(html_string)
        link_list = soup.find_all('a')
        return link_list

    @staticmethod
    def get_page(url):
        # returns html string from url
        try:
            data = requests.get(url)
        except requests.exceptions.ConnectionError:
            raise BadURL('Unable to connect to the given URL.  Check that you typed it correctly.')
        return data.text

    def clean_links(self, html_link_list):
        # normalizes URLs and removes external links
        relevant_links = []
        link_targets = [html_link_list[i].get('href') for i in range(len(html_link_list))]
        for target in link_targets:
            if target and len(target) > 0:

                # convert relative path to absolute
                # TODO account for internal links that don't begin with /
                if target[0] == '/':
                    target = self.parsed_url.scheme + '://' + self.parsed_url.netloc + target

                # check if link is internal (same domain)
                link_domain = '.'.join(self.parse_url(target).netloc.split('.')[-2:])
                if self.domain == link_domain:

                    # check that links is not an id, data uri, mailto, etc.
                    if 'http' in target and 'mailto:' not in target:
                        relevant_links.append(target)

        return relevant_links


class BadURL(Exception):
    """Wraps ConnectionError from request module."""
    pass


if __name__ == '__main__':
    if len(argv) <= 1:
        print 'Enter an absolute url after the command, e.g. python find_links.py http://www.google.com'

    else:
        finder = Finder(argv[1])
        print 'Found %d internal links at %s.' % (len(finder), finder.url)
        for number, link in enumerate(finder.links):
            print number + 1, link
