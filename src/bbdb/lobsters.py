"""
Helpers for dealing with lobste.rs
"""

from __future__ import absolute_import

from bbdb import schema
from bbdb.personas import merge_left
from bbdb.services import mk_service
from bbdb.twitter import insert_user as twitter_insert_user, insert_twitter
from bbdb.github import insert_user as gh_insert_user, insert_github, external_id as gh_external_id

from lobsters import User
from twitter.error import TwitterError
from arrow import utcnow as now


insert_lobsters = mk_service("Lobsters", ["http://lobste.rs"])


def lobsters_external_id(user_or_id):
  if isinstance(user_or_id, User):
    return lobsters_external_id(user_or_id.name)
  else:
    return "lobsters:%s" % user_or_id


def insert_user(session, twitter_api, user: User, when=None):
  when = when or now()

  existing = session.query(schema.Account)\
                    .filter_by(service=insert_lobsters(session),
                               external_id=lobsters_external_id(user))\
                    .first()
  if existing:
    return existing

  else:
    persona = schema.Persona()

    if user.github:
      _gh = insert_github(session)
      gh = session.query(schema.Account)\
                  .filter_by(service=_gh,
                             external_id=gh_external_id(user.github))\
                  .first()
      if gh and gh.persona:
        merge_left(session, persona, gh.persona)
      elif gh:
        gh.persona = persona
        session.add(gh)
        session.commit()
      else:
        print(gh_insert_user(session, user.github))

    if user.twitter:
      # If there isn't already a persona with this twitter account...
      tw = session.query(schema.Account)\
                  .filter(schema.Account.service == insert_twitter(session))\
                  .join(schema.Name)\
                  .filter(schema.Name.name.like("@" + user.twitter))\
                  .first()
      if tw:
        merge_left(session, persona, tw.persona)
      else:
        try:
          print("[DEBUG] Hitting Twitter API for user", user.twitter)
          tw = twitter_insert_user(session, twitter_api.GetUser(screen_name=user.twitter),
                                   persona=persona)
          persona = tw.persona
        except TwitterError as e:
          print(e)
          pass

    if not persona:
      persona = schema.Persona()
      session.add(persona)

    lobsters_user = schema.get_or_create(session, schema.Account,
                                         external_id=lobsters_external_id(user.name),
                                         persona=persona,
                                         service=insert_lobsters(session))

    schema.get_or_create(session, schema.Name,
                         persona=persona,
                         account=lobsters_user,
                         name=user.name)

    session.commit()
    session.refresh(lobsters_user)
    return lobsters_user
