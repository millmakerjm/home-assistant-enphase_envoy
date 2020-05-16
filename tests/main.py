import asyncio

from envoy_local_reader.envoy_reader_factory import EnvoyReaderFactory

factory = EnvoyReaderFactory("envoy.local")

loop = asyncio.get_event_loop()
r = loop.run_until_complete(factory.get_reader())

d = loop.run_until_complete(r.get_data())
print(d)
