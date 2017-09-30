"""
Helpers for working with services.
"""

import sys

from skrode import schema

from arrow import utcnow as now

# FIXME: Py3k EVIL HACK
if sys.version >= (3, 0, 0):
  from urllib.parse import urlparse
else:
  from urlparse import urlparse


def normalize_url(url):
  """Normalizes a URL down to the netloc with a HTTP scheme."""

  parse_result = urlparse(url)
  return "http://{0.netloc}".format(parse_result)


def mk_service(name, urls, normalize=True):
  """Returns a partial function for getting/creating a Service record for a name and a domain."""

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


def mk_insert_user(service_ctor, external_id_fn):

  def helper(session, external_id, persona=None, when=None):
    when = when or now()
    _svc = service_ctor(session)
    _extid = external_id_fn(external_id)

    account = session.query(schema.Account)\
                     .filter_by(service=_svc,
                                external_id=_extid)\
                     .first()
    if not account:
      account = schema.Account(service=_svc, external_id=_extid)
      session.add(account)

    if when:
      account.when = when

    if account.persona and persona:
      from skrode.personas import merge_left
      merge_left(session, persona, account.persona)

    else:
       persona = account.persona = persona or schema.Persona()

    schema.get_or_create(session, schema.Name,
                         name=external_id,
                         account=account)

    session.commit()
    session.refresh(account)
    return account

  return helper
