from ..base import ShopLineResource


class Webhooks(ShopLineResource):
    """webhooks """
    DETAIL = "/webhooks"

    def __init__(self):
        super().__init__()

    @classmethod
    def webhooks(cls, _id=None, prefix_options=None, **kwargs):
        url = cls.get_base_url(cls.DETAIL if not _id else "/{}".format(_id), page=cls.page_size if not _id else None)
        return cls.find(from_=url, **kwargs)

    @classmethod
    def create_webhook(cls, **kwargs):
        url = cls.get_base_url(cls.DETAIL)
        return cls.create(from_=url, **kwargs)

    @classmethod
    def delete_webhook(cls, id_=None, **kwargs):
        url = cls.get_base_url(cls.DETAIL, id_=id_)
        return cls.delete(from_=url, id_=id_)