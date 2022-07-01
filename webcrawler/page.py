class Page:
    def __init__(self, name, url, outlinks, page_rank=0) -> None:
        self.name = name
        self.url = url
        self.page_rank = page_rank
        self.outlinks = outlinks

    def get_outlink(self, index):
        try:
            link = self.outlinks[index]
        except:
            link = 'no outlinks'
        return link

    def set_page_rank(self, page_rank):
        self.page_rank = page_rank

    def get_page_rank(self):
        return self.page_rank

    # checks whether page_other links to this page
    def links_to(self, page_other):
        if self.url == page_other.url:
            return False
        if page_other.url in self.outlinks:
            return True
        return False

    def __str__(self) -> str:
        text = f"Name: {self.name}\nURL: {self.url} \nPageRank: {self.page_rank}\
                    \nOutlinks count: {len(self.outlinks)}"
        return text
