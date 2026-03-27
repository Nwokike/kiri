from django.contrib.syndication.views import Feed
from django.urls import reverse
from projects.models import Project

class LatestProjectsFeed(Feed):
    title = "Kiri Research Labs Projects"
    link = "/projects/"
    description = "New open source tools, SLMs, and tinyML applications from Kiri Research Labs."

    def items(self):
        return Project.objects.filter(status='active').order_by('-created_at')[:10]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.description

    def item_link(self, item):
        return item.get_absolute_url()
