import json

from ..base import ShopLineResource

from ..collection import Collection, PaginatedCollection


class Orders(ShopLineResource):
    """orders """
    # 弃单
    ABANDONED_ORDERS = "/abandoned_orders"

    def __init__(self):
        super().__init__()

    @classmethod
    def abandoned_orders(cls, id_=None, prefix_options=None, **kwargs):
        url = cls.get_base_url(cls.ABANDONED_ORDERS, page=cls.page_size)
        return cls.find(from_=url, **kwargs)

    @classmethod
    def orders(cls, prefix_options=None, **kwargs):
        url = cls.get_base_url("", page=cls.page_size)
        return cls.find(from_=url, **kwargs)

    def get_orders(self, handle, payload, access_token):
        import requests
        url = f"https://{handle}.myshopline.com/admin/openapi/v20250301/orders.json".format(handle=handle)
        headers = {
            'Accept': 'application/json',
            'Authorization': f"Bearer {access_token}".format(access_token=access_token)
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.content)

