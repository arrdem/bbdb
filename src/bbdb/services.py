"""
Helpers for working with services.
"""

from urllib.parse import urlparse

from bbdb import schema

from detritus import once


def normalize_url(url):
  """Normalizes a URL down to the netloc with a HTTP scheme."""

  parse_result = urlparse(url)
  return "http://{0.netloc}".format(parse_result)


def mk_service(name, urls, normalize=True):
  """Returns a partial function for getting/creating a Service record for a name and a domain."""

  @once
  def helper(session):
    service = session.query(schema.Service).filter(schema.Service.name == name.lower()).first()
    if not service:
      service = schema.get_or_create(session, schema.Service,
                                     name=name.lower())

    if service.more and  "pretty_name" not in service.more:
      service.more["pretty_name"] = name

    elif not service.more:
      service.more = {"pretty_name": name}

    for url in urls:
      schema.get_or_create(session, schema.ServiceURL, service=service,
                           url=normalize_url(url) if normalize else url)
    return service

  return helper
