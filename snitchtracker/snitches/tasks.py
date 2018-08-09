"""This class handles generic repeating tasks.
"""
from threading import Timer

from django.core.exceptions import ObjectDoesNotExist

from webpush import send_user_notification

from .models import Snitch, SnitchRecord, WebhookTransaction, GroupMember

class RepeatedTimer(object):
    """Class used to repeat run a method.
    """
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.function = function
        self.interval = interval
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        """Starts the task.
        """
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        """Stops the task.
        """
        self._timer.cancel()
        self.is_running = False

def run():
    """Method called on a timer.

    Used to process waiting webhooks async.
    """
    unprocessed_trans = get_transactions_to_process()
    for trans in unprocessed_trans:
        try:
            process_trans(trans)
            trans.status = WebhookTransaction.PROCESSED
            trans.save()
        except Exception as ex: # pylint: disable=W0703
            print(ex)
            trans.status = WebhookTransaction.ERROR
            trans.save()

def get_transactions_to_process():
    """Gets list of WebhookTransaction that need to be proccessed.
    """
    return WebhookTransaction.objects.filter(
        status=WebhookTransaction.UNPROCESSED
    )

def process_trans(trans):
    """This method proccesses the actual webhook transactions.
    """
    # Let's do this in steps.
    # First we need to get the main snitch or create it if it doesnt exist.
    j = trans.body
    try:
        snitch = Snitch.objects.get(
            token=trans.token,
            name=j['snitch_name'],
            x_pos=j['x'],
            y_pos=j['y'],
            z_pos=j['z'],
            world=j['world'],
            server=j['server']
        )
    except ObjectDoesNotExist:
        # If it failed means we need to create it.
        snitch = Snitch.objects.create(
            token=trans.token,
            name=j['snitch_name'],
            x_pos=j['x'],
            y_pos=j['y'],
            z_pos=j['z'],
            world=j['world'],
            server=j['server']
        )
    # Now let's make the record for it.
    if j['type'] == 'Enter':
        num = 0
    elif j['type'] == 'Login':
        num = 1
    elif j['type'] == 'Logout':
        num = 2
    else:
        num = -1
    record = SnitchRecord.objects.create(
        snitch=snitch,
        type=SnitchRecord.TYPES[num],
        user=j['user'],
        pub_date=trans.date_generated
    )
    # Now let's send a push notification
    payload = {"head": "Snitch Tracker", "body": "Snitch notification [%s] %s from %s at %s %d %d %d" % (j['type'], j['user'], j['server'], j['world'], j['x'], j['y'], j['z'])}
    # Now let's iterate through all the users
    group = trans.token.group
    group_members = GroupMember.objects.filter(belongs=group)
    for g in group_members:
        send_user_notification(user=g.user, payload=payload, ttl=1000)
    send_user_notification(user=group.owner, payload=payload, ttl=1000)
    return record
