class WebHooks:

    def create(self, topic, handle, api_version, access_token):
        import requests
        import json

        url = f"https://{handle}.myshopline.com/admin/openapi/{api_version}/webhooks.json".format(
            handle=handle, api_version=api_version)

        payload = json.dumps({
            "webhook": {
                "address": "https://www.shopline.com/webhook",
                "api_version": "v20240601",
                "topic": topic
            }
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f"Bearer {access_token}".format(access_token=access_token)
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        webhook = json.loads(response.content)

        return {
            "id": webhook['webhook']['id'],
            "topic": webhook['webhook']['topic'],
            "address": webhook['webhook']['address'],
            "format": webhook['webhook']['format'],
        }

    def delete(self, webhook_id, handle, api_version, access_token):
        import requests

        url = f"https://{handle}.myshopline.com/admin/openapi/{api_version}/{id}/webhooks.json".format(
            id=webhook_id, handle=handle, api_version=api_version)

        payload = {}
        headers = {
            'Accept': 'application/json',
            'Authorization': f"Bearer {access_token}".format(access_token=access_token)
        }

        response = requests.request("DELETE", url, headers=headers, data=payload)

        if response.status_code != 200:
            return False

        return True