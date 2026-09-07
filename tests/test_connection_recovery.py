"""Connection recovery without a live database, using real DatabaseSource reads."""
from unittest.mock import MagicMock, patch

import pytest
import psycopg2

from prompt_assemble.sources.database import DatabaseSource
from prompt_assemble.exceptions import SourceConnectionError, PromptNotFoundError


def connection(content='restored prompt'):
    conn = MagicMock()
    conn.closed = False
    conn.cursor.return_value.fetchone.return_value = (content,)
    return conn


def source(conn, factory=None):
    with patch.object(DatabaseSource, '_ensure_schema'), patch.object(DatabaseSource, 'refresh'):
        result = DatabaseSource(conn, connection_factory=factory)
    result.refresh_interval_seconds = float('inf')
    return result


def test_closed_connection_reopened_before_read():
    old, new = connection(), connection()
    old.closed = True
    factory = MagicMock(return_value=new)
    db = source(old, factory)
    assert db.get_raw('core') == 'restored prompt'
    factory.assert_called_once()
    old.cursor.assert_not_called()


@pytest.mark.parametrize('phase', ['execute', 'fetchone'])
def test_disconnect_during_read_retries_complete_read(phase):
    old, new = connection(), connection()
    getattr(old.cursor.return_value, phase).side_effect = psycopg2.OperationalError('socket lost')
    factory = MagicMock(return_value=new)
    db = source(old, factory)
    assert db.get_raw('core') == 'restored prompt'
    factory.assert_called_once()
    old.close.assert_called_once()
    new.cursor.return_value.execute.assert_called_once()


def test_retry_is_bounded():
    old, new = connection(), connection()
    for conn in (old, new):
        conn.cursor.return_value.execute.side_effect = psycopg2.OperationalError('socket lost')
    factory = MagicMock(return_value=new)
    with pytest.raises(psycopg2.OperationalError):
        source(old, factory).get_raw('core')
    factory.assert_called_once()


def test_reconnect_failure_can_recover_on_later_request():
    old = connection()
    old.closed = True
    factory = MagicMock(side_effect=[OSError('unavailable'), OSError('unavailable'), connection()])
    db = source(old, factory)
    with pytest.raises(SourceConnectionError):
        db.get_raw('core')
    assert db.get_raw('core') == 'restored prompt'


@pytest.mark.parametrize('error', [psycopg2.ProgrammingError('bad SQL'), PromptNotFoundError('absent')])
def test_non_connection_errors_not_retried(error):
    old = connection()
    old.cursor.return_value.execute.side_effect = error
    factory = MagicMock()
    with pytest.raises(type(error)):
        source(old, factory).get_raw('core')
    factory.assert_not_called()


def test_write_is_not_replayed():
    old = connection()
    old.cursor.return_value.execute.side_effect = psycopg2.OperationalError('socket lost')
    factory = MagicMock()
    with pytest.raises(psycopg2.OperationalError):
        source(old, factory).delete_prompt('core')
    factory.assert_not_called()


def test_legacy_connection_without_factory_reports_closure():
    old = connection()
    old.closed = True
    with pytest.raises(SourceConnectionError):
        source(old).get_raw('core')


def test_pool_and_factory_rejected():
    with pytest.raises(ValueError):
        DatabaseSource(connection_pool=MagicMock(), connection_factory=MagicMock())


@pytest.mark.parametrize('autocommit', [True, False])
def test_schema_initialization_preserves_transaction_mode(autocommit):
    conn = connection()
    conn.autocommit = autocommit
    conn.cursor.return_value.connection = conn
    db = source(conn)
    db._ensure_schema()
    assert conn.autocommit is autocommit


def test_failed_refresh_preserves_previous_metadata():
    old, new = connection(), connection()
    db = source(old, MagicMock(return_value=new))
    metadata = db._metadata_cache
    registry = db._registry
    metadata['existing'] = {'name': 'core'}
    for conn in (old, new):
        conn.cursor.return_value.execute.side_effect = psycopg2.OperationalError('socket lost')
    with pytest.raises(psycopg2.OperationalError):
        db.refresh()
    assert db._metadata_cache is metadata
    assert db._registry is registry
    assert metadata['existing']['name'] == 'core'


def test_factory_only_initialization():
    factory = MagicMock(return_value=connection())
    with patch.object(DatabaseSource, '_ensure_schema'), patch.object(DatabaseSource, 'refresh'):
        db = DatabaseSource(connection_factory=factory)
    assert db.connection is factory.return_value
    factory.assert_called_once()
