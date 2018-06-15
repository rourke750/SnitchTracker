from celery.task import PeriodicTask
from celery.schedules import crontab

from django.core.exceptions import ObjectDoesNotExist

from .models import Snitch, Snitch_Record, WebhookTransaction

class ProcessMessages(PeriodicTask):
    run_every = crontab()  # this will run once a minute
    def run(self, **kwargs):
        unprocessed_trans = self.get_transactions_to_process()

        for trans in unprocessed_trans:
            try:
                self.process_trans(trans)
                trans.status = WebhookTransaction.PROCESSED
                trans.save()

            except Exception:
                trans.status = WebhookTransaction.ERROR
                trans.save()

    def get_transactions_to_process(self):
        return WebhookTransaction.objects.filter(
            event_name__in=self.event_names,
            status=WebhookTransaction.UNPROCESSED
        )
        
    def process_trans(self, trans):
        # Let's do this in steps.
        # First we need to get the main snitch or create it if it doesnt exist.
        try:
            snitch = Snitch.objects.get(
                    token=trans.token,
                    name=trans.body['snitch_name'],
                    x_pos=trans.body['x_pos'],
                    y_pos=trans.body['y_pos'],
                    z_pos=trans.body['z_pos'],
                    world=trans.body['world'],
                    server=trans.body['server']
                )
        except ObjectDoesNotExist:
            # If it failed means we need to create it.
            snitch = Snitch.objects.create(
                    token=trans.token,
                    name=trans.body['snitch_name'],
                    x_pos=trans.body['x_pos'],
                    y_pos=trans.body['y_pos'],
                    z_pos=trans.body['z_pos'],
                    world=trans.body['world'],
                    server=trans.body['server']
                )
        # Now let's make the record for it.
        # Todo build a Snitch_record model