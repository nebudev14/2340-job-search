from django.core.management.base import BaseCommand
from django.utils import timezone
from home.models import SavedSearch
from django.contrib import messages
from django.contrib.messages import get_messages
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check saved searches for new matches and send notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually sending notifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        active_searches = SavedSearch.objects.filter(is_active=True)
        
        total_notifications = 0
        
        for search in active_searches:
            new_matches = search.get_new_matches_since_last_notification()
            
            if new_matches.exists():
                count = new_matches.count()
                total_notifications += count
                
                if dry_run:
                    self.stdout.write(
                        f"Would notify {search.recruiter.username} about {count} new matches for search '{search.name}'"
                    )
                else:
                    search.last_notified = timezone.now()
                    search.save()
                    
                    logger.info(
                        f"Notified {search.recruiter.username} about {count} new matches for search '{search.name}'"
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Notified {search.recruiter.username} about {count} new matches for search '{search.name}'"
                        )
                    )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would send {total_notifications} notifications total")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Sent {total_notifications} notifications total")
            )
