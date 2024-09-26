import json

import shopline.mixins as mixins
import threading
from .connection import Connection
from shopline.collection import PaginatedCollection
from .utils.formats import JSONFormat
from .collection import Collection


class ShopLineResource(mixins.CountMixins):
    _threadlocal = threading.local()
    _headers = {}
    _version = None
    _url = None
    page_size = 50
    connect = Connection()
    format = JSONFormat()

    def __init__(self):
        super().__init__()

    @classmethod
    def get_base_url(cls, details, id_=None, **kwargs):
        item = cls.__dict__.get("__module__").rsplit(".")[-1]
        if kwargs.get("item") is not None:
            item = kwargs.get("item")
        if kwargs.get("page"):
            url = "https://{url}{version}/{item}{detail}.json?limit={pagesize}".format(url=cls._url,
                                                                                       version=cls._version._path,
                                                                                       item=item,
                                                                                       detail=details,
                                                                                       pagesize=kwargs.get("page"))

        elif id_ is not None:
            url = "https://{url}{version}/{id}/{item}{detail}.json?limit={pagesize}".format(url=cls._url,
                                                                                       version=cls._version._path,
                                                                                       item=item, detail=details,
                                                                                       pagesize=kwargs.get("page"),
                                                                                       id=id_)
        else:
            url = "https://{url}{version}/{item}{detail}.json".format(url=cls._url, version=cls._version._path,
                                                                      item=item, detail=details)

        return url


    @classmethod
    def get_url(cls):
        return cls._url

    @classmethod
    def get_headers(cls):
        return cls._headers

    @classmethod
    def get_version(cls):
        return cls._version

    @classmethod
    def activate_session(cls, session):
        cls.site = session.site
        cls._url = session.url
        cls.user = None
        cls.password = None
        cls._version = session.api_version
        cls._headers["Authorization"] = "Bearer %s" % session.token

    @classmethod
    def clear_session(cls):
        cls.site = None
        cls._url = None
        cls.user = None
        cls.password = None
        cls._version = None
        cls._headers.pop("Authorization", None)


    @classmethod
    def find(cls, id_=None, from_=None, **kwargs):
        """Checks the resulting collection for pagination metadata."""
        if not from_:
            return None

        # Construct the base URL
        url = from_

        # Add the id to the URL if provided
        if id_:
            if "?" in url:
                url = f"{url}&ids={id_}"
            else:
                url = f"{url}?ids={id_}"

        # Append query parameters from kwargs
        if kwargs:
            query_params = "&".join(f"{k}={v}" for k, v in kwargs.items())
            if "?" in url:
                url = f"{url}&{query_params}"
            else:
                url = f"{url}?{query_params}"

        print(url)

        response = cls.connect.get(url, cls.get_headers())
        objs = cls.format.decode(response.body)
        print(objs)

        if not objs:
            return objs

        prefix_options = {}
        collection = cls._build_collection(objs, prefix_options, response.headers)

        if isinstance(collection, Collection) and "headers" in collection.metadata:
            return PaginatedCollection(collection, metadata={"resource_class": cls}, **kwargs)

        return collection

    @classmethod
    def create(cls, data, from_=None):
        """Create a new resource with the provided data."""
        if not from_:
            return None

        url = from_
        print(f"Creating resource at {url} with data: {data}")

        # Send POST request with the data to create a new resource
        response = cls.connect.post(url, data, cls.get_headers())

        if response.code == 200:
            json_payload = json.loads(response.read().decode("utf-8"))
            if json_payload.get("code") == 200:
                print('json', json_payload)
                data = json_payload

        return data

    @classmethod
    def delete(cls, id_, from_=None):
        """Delete a resource by its ID."""
        if not from_ or not id_:
            return None

        # Construct URL with the ID
        url = from_
        print(f"Deleting resource at {url}")

        # Send DELETE request to the resource URL
        response = cls.connect.delete(url, cls.get_headers())

        if response.status_code != 200:
            print(f"Failed to delete resource {id_}. Status code: {response.status_code}")
            return False
        else:
            print(f"Resource {id_} deleted successfully.")
            return True

    @classmethod
    def _build_collection(cls, elements, prefix_options=None, headers={}):
        """Create a Collection of objects from the given resources.

        Args:
            elements: A list of dictionaries representing resources.
            prefix_options: A dict of prefixes to add to the request for
                            nested URLs.
            headers: The response headers that came with the resources.
        Returns:
            A Collection of ActiveResource objects.
        """

        if isinstance(elements, dict):
            # FIXME(emdemir): this is not an ActiveResource object but is
            # preserved for backwards compatibility. What should this be
            # instead?
            elements = [elements]
        else:
            # elements = (
            #     cls._build_object(el, prefix_options) for el in elements
            # )
            pass

        # TODO(emdemir): Figure out whether passing all headers is needed.
        # I am currently assuming that the Link header is not standard
        # ActiveResource stuff so I am passing all headers up the chain to
        # python_shopify_api which will handle pagination.
        return Collection(elements, metadata={
            "headers": headers
        })