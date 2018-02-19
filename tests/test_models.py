import pytest
import arrow
from django.conf import settings
from unittest.mock import patch

from openlobby.core.models import Report, User, OpenIdClient, LoginAttempt
from openlobby.core.documents import ReportDoc


pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures('django_es')]


def test_report__marks_user_as_author_on_save():
    author = User.objects.create(id=1, is_author=False)
    date = arrow.get(2018, 1, 1).datetime
    Report.objects.create(author=author, date=date, body='Lorem ipsum.')
    user = User.objects.get(id=1)
    assert user.is_author


def test_report__is_saved_in_elasticsearch():
    author = User.objects.create(id=6)
    date = arrow.get(2018, 1, 1).datetime
    published = arrow.get(2018, 1, 2).datetime
    Report.objects.create(
        id=3,
        author=author,
        date=date,
        published=published,
        title='It happened',
        body='Lorem ipsum.',
        received_benefit='coffee',
        provided_benefit='tea',
        our_participants='me',
        other_participants='them',
        extra={'a': 3},
    )
    docs = list(ReportDoc.search())
    assert len(docs) == 1
    doc = docs[0]
    assert doc.meta.id == '3'
    assert doc.author_id == 6
    assert doc.date == date
    assert doc.published == published
    assert doc.title == 'It happened'
    assert doc.body == 'Lorem ipsum.'
    assert doc.received_benefit == 'coffee'
    assert doc.provided_benefit == 'tea'
    assert doc.our_participants == 'me'
    assert doc.other_participants == 'them'
    assert doc.extra == {'a': 3}


def test_report__save_works_with_no_extra():
    author = User.objects.create(id=6)
    date = arrow.get(2018, 1, 1).datetime
    Report.objects.create(
        id=7,
        author=author,
        date=date,
        published=date,
        body='Lorem ipsum.',
    )
    docs = list(ReportDoc.search())
    assert len(docs) == 1
    doc = docs[0]
    assert doc.meta.id == '7'
    assert doc.extra is None


def test_login_attempt__default_expiration():
    client = OpenIdClient.objects.create(name='a', client_id='b', client_secret='c')
    with patch('openlobby.core.models.time.time', return_value=10000):
        attempt = LoginAttempt.objects.create(openid_client=client, state='foo',
            app_redirect_uri='http://openlobby/app')
    assert attempt.expiration == 10000 + settings.LOGIN_ATTEMPT_EXPIRATION