from __future__ import unicode_literals, division, absolute_import
import re
import logging
from urlparse import urlparse, urlunparse
from requests import RequestException

from flexget import plugin
from flexget.event import event
from flexget.plugins.plugin_urlrewriting import UrlRewritingError
from flexget.utils import requests
from flexget.utils.soup import get_soup

log = logging.getLogger('eztv')

EZTV_MIRRORS = [
    ('http', 'eztv.it'),
    ('https', 'eztv-proxy.net'),
    ('http', 'eztv.come.in')]


class UrlRewriteEztv(object):
    """Eztv url rewriter."""

    def url_rewritable(self, task, entry):
        return urlparse(entry['url']).netloc == 'eztv.it'

    def url_rewrite(self, task, entry):
        url = entry['url']
        for (scheme, netloc) in EZTV_MIRRORS:
            try:
                _, _, path, params, query, fragment = urlparse(url)
                url = urlunparse((scheme, netloc, path, params, query, fragment))
                page = requests.get(url).content
            except RequestException as e:
                log.debug('Eztv mirror `%s` seems to be down', url)
                continue
            break

        if not page:
            raise UrlRewritingError('No mirrors found for url %s' % entry['url'])

        log.debug('Eztv mirror `%s` chosen', url)
        try:
            soup = get_soup(page)
            mirrors = soup.find('a', attrs={'class': re.compile(r'download_\d')})
            if not mirrors:
                raise UrlRewritingError('Unable to locate download link from url %s'
                                        % url)
            entry['urls'] = [m.get('href') for m in mirrors]
            entry['url'] = mirrors[0].get('href')
        except Exception as e:
            raise UrlRewritingError(e)


@event('plugin.register')
def register_plugin():
    plugin.register(UrlRewriteEztv, 'eztv', groups=['urlrewriter'], api_ver=2)
