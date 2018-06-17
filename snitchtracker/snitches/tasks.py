import json

from threading import Timer

from django.core.exceptions import ObjectDoesNotExist

from .models import Snitch, Snitch_Record, WebhookTransaction

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.function   = function
        self.interval   = interval
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
        
def run():
    unprocessed_trans = get_transactions_to_process()
    for trans in unprocessed_trans:
        try:
            process_trans(trans)
            trans.status = WebhookTransaction.PROCESSED
            trans.save()
        except Exception as ex:
            print(ex)
            trans.status = WebhookTransaction.ERROR
            trans.save()

def get_transactions_to_process():
    return WebhookTransaction.objects.filter(
        status=WebhookTransaction.UNPROCESSED
    )
        
def process_trans(trans):
    # Let's do this in steps.
    # First we need to get the main snitch or create it if it doesnt exist.
    j = trans.body
    try:
        snitch = Snitch.objects.get(
                token=trans.token,
                name=j['snitch_name'],
                x_pos=j['x_pos'],
                y_pos=j['y_pos'],
                z_pos=j['z_pos'],
                world=j['world'],
                server=j['server']
            )
    except ObjectDoesNotExist:
        # If it failed means we need to create it.
        snitch = Snitch.objects.create(
                token=trans.token,
                name=j['snitch_name'],
                x_pos=j['x_pos'],
                y_pos=j['y_pos'],
                z_pos=j['z_pos'],
                world=j['world'],
                server=j['server']
            )
    # Now let's make the record for it.
    record = Snitch_Record.objects.create(
        snitch=snitch,
        type=Snitch_Record.TYPES[j['type']],
        user=j['user'],
        pub_date=trans.date_generated
    )