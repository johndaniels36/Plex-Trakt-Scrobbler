from plugin.sync.core.enums import SyncMode, SyncMedia
from plugin.sync.modes.core.base import Mode

from plex_database.models import LibrarySectionType, LibrarySection
import logging

log = logging.getLogger(__name__)


class Movies(Mode):
    mode = SyncMode.FastPull

    def run(self):
        # Retrieve movie sections
        p_sections = self.plex.library.sections(
            LibrarySectionType.Movie,
            LibrarySection.id
        ).tuples()

        # Fetch movies with account settings
        # TODO use actual `account`
        p_items = self.plex.library.movies.mapped(
            p_sections,
            account=1,
            parse_guid=True
        )

        for rating_key, p_guid, p_item in p_items:
            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            if pk is None:
                # No `pk` found
                continue

            for (media, data), changes in self.trakt.changes:
                if media != SyncMedia.Movies:
                    # Ignore changes that aren't for movies
                    continue

                for action, items in changes.items():
                    t_item = items.get(pk)

                    if t_item is None:
                        # No item found in changes
                        continue

                    self.execute_handlers(
                        SyncMedia.Movies, data,
                        action=action,
                        rating_key=rating_key,

                        p_item=p_item,
                        t_item=t_item
                    )


class Shows(Mode):
    mode = SyncMode.FastPull

    def run(self):
        # Retrieve show sections
        p_sections = self.plex.library.sections(
            LibrarySectionType.Show,
            LibrarySection.id
        ).tuples()

        # Fetch episodes with account settings
        # TODO use actual `account`
        p_shows, p_seasons, p_episodes = self.plex.library.episodes.mapped(
            p_sections,
            account=1,
            parse_guid=True
        )

        # TODO process shows, seasons

        # Process episodes
        for ids, p_guid, (season_num, episode_num), p_item in p_episodes:
            key = (p_guid.agent, p_guid.sid)

            # Try retrieve `pk` for `key`
            pk = self.trakt.table.get(key)

            if pk is None:
                # No `pk` found
                continue

            if not ids.get('episode'):
                # Missing `episode` rating key
                continue

            for (media, data), changes in self.trakt.changes:
                if media != SyncMedia.Shows:
                    # Ignore changes that aren't for episodes
                    continue

                for action, items in changes.items():
                    t_show = items.get(pk)

                    if t_show is None:
                        # Unable to find matching show in trakt data
                        continue

                    t_season = t_show.get('seasons', {}).get(season_num)

                    if t_season is None:
                        # Unable to find matching season in `t_show`
                        continue

                    t_episode = t_season.get('episodes', {}).get(episode_num)

                    if t_episode is None:
                        # Unable to find matching episode in `t_season`
                        continue

                    self.execute_handlers(
                        SyncMedia.Episodes, data,
                        action=action,
                        rating_key=ids['episode'],

                        p_item=p_item,
                        t_item=t_episode
                    )


class FastPull(Mode):
    mode = SyncMode.FastPull

    children = [
        Movies,
        Shows
    ]

    def run(self):
        # Fetch changes from trakt.tv
        self.trakt.refresh()

        # Build key table for lookups
        self.trakt.build_table()

        # Run children
        self.execute_children()

        # Flush caches to archives
        self.current.state.flush()
