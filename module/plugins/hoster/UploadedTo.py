# -*- coding: utf-8 -*-

import re
import time
import urlparse

from module.network.RequestFactory import getURL
from module.plugins.internal.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class UploadedTo(SimpleHoster):
    __name__    = "UploadedTo"
    __type__    = "hoster"
    __version__ = "0.92"

    __pattern__ = r'https?://(?:www\.)?(uploaded\.(to|net)|ul\.to)(/file/|/?\?id=|.*?&id=|/)(?P<ID>\w+)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Uploaded.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    CHECK_TRAFFIC = True
    DISPOSITION   = False

    API_KEY = "lhF2IeeprweDfu9ccWlxXVVypA5nA3EL"

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'http://uploaded.net/file/\g<ID>')]

    TEMP_OFFLINE_PATTERN = r'<title>uploaded\.net - Maintenance'

    WAIT_PATTERN   = r'Current waiting period: <span>(\d+)'
    DL_LIMIT_ERROR = r'You have reached the max. number of possible free downloads for this hour'


    @classmethod
    def apiInfo(cls, url):
        info = super(UploadedTo, cls).apiInfo(url)

        for _i in xrange(5):
            html = getURL("http://uploaded.net/api/filemultiple",
                          get={"apikey": cls.API_KEY, 'id_0': re.match(cls.__pattern__, url).group('ID')},
                          decode=True)

            if html != "can't find request":
                api = html.split(",", 4)
                if api[0] == "online":
                    info.update({'name': api[4].strip(), 'size': api[2], 'status': 2})
                else:
                    info['status'] = 1
                break
            else:
                time.sleep(3)

        return info


    def setup(self):
        self.multiDL = self.resumeDownload = self.premium
        self.chunkLimit = 1  # critical problems with more chunks


    def checkErrors(self):
        if 'var free_enabled = false;' in self.html:
            self.logError(_("Free-download capacities exhausted"))
            self.retry(24, 5 * 60)

        return super(UploadedTo, self).checkErrors()


    def handlePremium(self, pyfile):
        self.link = urlparse.urljoin(pyfile.url, "/ddl?pw=" + self.getPassword())


    def handleFree(self, pyfile):
        self.load("http://uploaded.net/language/en", just_header=True)

        self.html = self.load("http://uploaded.net/js/download.js", decode=True)

        recaptcha = ReCaptcha(self)
        response, challenge = recaptcha.challenge()

        self.html = self.load("http://uploaded.net/io/ticket/captcha/%s" % self.info['pattern']['ID'],
                              post={'recaptcha_challenge_field': challenge,
                                    'recaptcha_response_field' : response})

        if "type:'download'" in self.html:
            self.correctCaptcha()
            try:
                self.link = re.search("url:'(.+?)'", self.html).group(1)

            except Exception:
                pass


    def checkFile(self, rules={}):
        if self.checkDownload({'limit-dl': self.DL_LIMIT_ERROR}):
            self.wait(3 * 60 * 60, True)
            self.retry()

        return super(UploadedTo, self).checkFile(rules)


getInfo = create_getInfo(UploadedTo)
