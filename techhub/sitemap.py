from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['products:home', 'products:product_list']

    def location(self, item):
        try:
            return reverse(item)
        except:
            return '/'
