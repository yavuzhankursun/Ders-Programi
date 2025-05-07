import random
import logging
from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from schedule.models import Ders, OgretimUyesi

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class Command(BaseCommand):
    help = 'Assign instructors to courses based on predefined rules (MAT, LAB, Random for others).'

    def handle(self, *args, **options):
        logger.info("Starting instructor assignment...")

        try:
            # Get target instructors
            vildan = OgretimUyesi.objects.get(ad_soyad__icontains='Vildan YAZICI')
            candide = OgretimUyesi.objects.get(ad_soyad__icontains='Candide ÖZTÜRK')
            eray = OgretimUyesi.objects.get(ad_soyad__icontains='Eray DURSUN')
            logger.info("Target instructors identified: Vildan, Candide, Eray.")
        except OgretimUyesi.DoesNotExist as e:
            logger.error(f"Could not find one of the target instructors: {e}")
            self.stderr.write(self.style.ERROR("Please ensure 'Vildan YAZICI', 'Candide ÖZTÜRK', 'Eray DURSUN' exist in the OgretimUyesi table."))
            return
        except OgretimUyesi.MultipleObjectsReturned as e:
            logger.error(f"Found multiple instructors matching a target name: {e}")
            self.stderr.write(self.style.ERROR("Please ensure instructor names are unique enough."))
            return

        target_instructor_ids = [vildan.pk, candide.pk, eray.pk]

        # Get other instructors
        other_instructors = list(OgretimUyesi.objects.exclude(pk__in=target_instructor_ids))
        logger.info(f"Found {len(other_instructors)} other instructors.")

        # Counters
        mat_assigned_count = 0
        lab_assigned_count = 0
        random_assigned_count = 0
        skipped_no_others_count = 0
        skipped_already_assigned_count = 0
        processed_count = 0

        # Potansiyel olarak birden fazla bölümde olan ders kodlarını bulma kısmı kalabilir (bilgi amaçlı)
        # Ama atama mantığını etkilememeli
        duplicated_codes_info = Ders.objects.values('ders_kodu').annotate(bolum_count=Count('bolum', distinct=True)).filter(bolum_count__gt=1)
        duplicated_codes_set = {item['ders_kodu'] for item in duplicated_codes_info}
        logger.info(f"Found {len(duplicated_codes_set)} course codes appearing in multiple departments (FYI only, won't prevent assignment).")

        all_courses = Ders.objects.all()
        total_courses = all_courses.count()
        logger.info(f"Processing {total_courses} courses...")

        for ders in all_courses:
            processed_count += 1
            assigned_by_rule = False
            current_instructors = set(ders.ogretim_uyeleri.all())

            # Rule 1: MAT courses
            is_mat = False
            if ders.ders_kodu and 'mat' in ders.ders_kodu.lower():
                 is_mat = True
            elif ders.ders_adi and 'mat' in ders.ders_adi.lower():
                 is_mat = True

            if is_mat:
                if current_instructors != {vildan}:
                    ders.ogretim_uyeleri.set([vildan])
                    logger.info(f"[{processed_count}/{total_courses}] Assigned Vildan YAZICI to MAT course: {ders.ders_kodu} - {ders.ders_adi}")
                    mat_assigned_count += 1
                else:
                     logger.debug(f"[{processed_count}/{total_courses}] MAT course {ders.ders_kodu} already assigned correctly.")
                assigned_by_rule = True

            # Rule 2: LAB courses (only if not assigned in Rule 1)
            is_lab = False
            if not assigned_by_rule:
                if ders.ders_kodu and ('lab' in ders.ders_kodu.lower() or 'blm' in ders.ders_kodu.lower()):
                     is_lab = True
                elif ders.ders_adi and 'lab' in ders.ders_adi.lower():
                     is_lab = True
                elif ders.tip == 'LAB':
                     is_lab = True

            if is_lab:
                 target_lab_set = {candide, eray}
                 if current_instructors != target_lab_set:
                    ders.ogretim_uyeleri.set([candide, eray])
                    logger.info(f"[{processed_count}/{total_courses}] Assigned Candide ÖZTÜRK & Eray DURSUN to LAB course: {ders.ders_kodu} - {ders.ders_adi}")
                    lab_assigned_count += 1
                 else:
                    logger.debug(f"[{processed_count}/{total_courses}] LAB course {ders.ders_kodu} already assigned correctly.")
                 assigned_by_rule = True

            # Rule 3: Random assignment for remaining courses *only if they have no instructors*
            if not assigned_by_rule and not current_instructors:
                if other_instructors:
                    random_instructor = random.choice(other_instructors)
                    ders.ogretim_uyeleri.set([random_instructor])
                    logger.info(f"[{processed_count}/{total_courses}] Assigned random instructor ({random_instructor.ad_soyad}) to course: {ders.ders_kodu} - {ders.ders_adi}")
                    random_assigned_count += 1
                else:
                     logger.warning(f"[{processed_count}/{total_courses}] Skipping random assignment for {ders.ders_kodu}: No other instructors available.")
                     skipped_no_others_count += 1
            elif not assigned_by_rule and current_instructors:
                 # This course didn't match MAT/LAB and already had an instructor(s). Leave it alone.
                 logger.debug(f"[{processed_count}/{total_courses}] Course {ders.ders_kodu} already has instructor(s), skipping random assignment.")
                 skipped_already_assigned_count += 1

        # --- Final Summary --- #
        summary = (
            "\nAssignment Summary:\n"
            f"- Courses assigned/verified for Vildan YAZICI (MAT): {mat_assigned_count}\n"
            f"- Courses assigned/verified for Candide ÖZTÜRK & Eray DURSUN (LAB): {lab_assigned_count}\n"
            f"- Courses assigned a random instructor: {random_assigned_count}\n"
            f"- Courses skipped (no other instructors for random): {skipped_no_others_count}\n"
            f"- Courses skipped (already had instructor, not MAT/LAB): {skipped_already_assigned_count}\n"
            f"- Total courses processed: {processed_count}"
        )
        self.stdout.write(self.style.SUCCESS(summary))
        logger.info("Instructor assignment finished.") 