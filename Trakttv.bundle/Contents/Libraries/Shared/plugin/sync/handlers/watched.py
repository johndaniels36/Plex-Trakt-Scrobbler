from plugin.sync.core.enums import SyncData, SyncMedia
from plugin.sync.handlers.core.base import DataHandler, MediaHandler

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Base(MediaHandler):
    @staticmethod
    def build_action(action, rating_key, p_viewed_at, t_viewed_at):
        kwargs = {
            'rating_key': rating_key
        }

        if action in ['added', 'changed']:
            kwargs['t_viewed_at'] = t_viewed_at

        if action == 'changed':
            kwargs['p_viewed_at'] = p_viewed_at

        return kwargs

    @staticmethod
    def get_operands(p_item, t_item):
        return (
            p_item.get('settings', {}).get('last_viewed_at'),
            t_item.last_watched_at if t_item else None
        )

    @staticmethod
    def scrobble(rating_key):
        return Plex['library'].scrobble(rating_key)

    #
    # Modes
    #

    def fast_pull(self, action, rating_key, p_item, t_item):
        log.debug('fast_pull(%r, %r, %r, %r)', action, rating_key, p_item, t_item)

    def pull(self, rating_key, p_item, t_item):
        # Retrieve properties
        p_viewed_at, t_viewed_at = self.get_operands(p_item, t_item)

        # Determine performed action
        action = self.get_action(p_viewed_at, t_viewed_at)

        if not action:
            # No action required
            return

        # Execute action
        self.execute_action(action, (
            action,
            rating_key,
            p_viewed_at,
            t_viewed_at
        ))


class Movies(Base):
    media = SyncMedia.Movies

    def on_added(self, rating_key, t_viewed_at):
        log.debug('Movies.on_added(%r, %r)', rating_key, t_viewed_at)

        return self.scrobble(rating_key)


class Episodes(Base):
    media = SyncMedia.Episodes

    def on_added(self, rating_key, t_viewed_at):
        log.debug('Movies.on_added(%r, %r)', rating_key, t_viewed_at)

        return self.scrobble(rating_key)


class Watched(DataHandler):
    data = SyncData.Watched

    children = [
        Movies,
        Episodes
    ]
