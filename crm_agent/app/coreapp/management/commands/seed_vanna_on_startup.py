from django.core.management.base import BaseCommand
from crm_agent.agent.vanna_client import VannaClient
from crm_agent.ingestion.vanna_seed import VannaSeeder
import os

class Command(BaseCommand):
    help = 'Seed Vanna training data on startup'

    def handle(self, *args, **options):
        try:
            chroma_dir = os.getenv("CHROMA_DIR", "/tmp/chroma")
            os.makedirs(chroma_dir, exist_ok=True)
            
            vanna_client = VannaClient(chroma_dir=chroma_dir)
            seeder = VannaSeeder(vanna_client)
            result = seeder.seed()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Seeded Vanna: {result["ddl_items"]} DDL, {result["sql_examples"]} examples'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠ Vanna seed skipped: {e}')
            )

