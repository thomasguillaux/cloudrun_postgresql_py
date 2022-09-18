import json

from google.cloud import pubsub_v1


class PubSubService(object):
    def __init__(self):
        self.project_id = 'nft-indexor-staging'
        self.topic = 'get_nfts'

    def start_bot(self, data, topic=None):
        client = pubsub_v1.PublisherClient()

        topic_path = client.topic_path(self.project_id, self.topic if topic is None else topic)

        data = json.dumps(
            data
        ).encode('utf-8')

        client.publish(
            topic_path,
            data=data,
        )
