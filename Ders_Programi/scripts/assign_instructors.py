import random
from django.db.models import Q
from schedule.models import Ders, OgretimUyesi
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run():
    logger.info("Starting instructor assignment...")

    try:
        # Get target instructors
        vildan = OgretimUyesi.objects.get(ad_soyad__icontains='Vildan YAZICI')
        candide = OgretimUyesi.objects.get(ad_soyad__icontains='Candide ÖZTÜRK')
        eray = OgretimUyesi.objects.get(ad_soyad__icontains='Eray DURSUN')
        logger.info("Target instructors identified: Vildan, Candide, Eray.")
    except OgretimUyesi.DoesNotExist as e:
        logger.error(f"Could not find one of the target instructors: {e}")
        logger.error("Please ensure 'Vildan YAZICI', 'Candide ÖZTÜRK', 'Eray DURSUN' exist in the OgretimUyesi table.")
        return
    except OgretimUyesi.MultipleObjectsReturned as e:
        logger.error(f"Found multiple instructors matching a target name: {e}")
        logger.error("Please ensure instructor names are unique enough.")
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

    all_courses = Ders.objects.all()
    logger.info(f"Processing {all_courses.count()} courses...")

    for ders in all_courses:
        assigned_by_rule = False
        # Rule 1: MAT courses
        # Using explicit checks for ders_kodu or ders_adi
        is_mat = False
        if ders.ders_kodu and 'mat' in ders.ders_kodu.lower():
             is_mat = True
        elif ders.ders_adi and 'mat' in ders.ders_adi.lower():
             is_mat = True

        if is_mat:
            ders.ogretim_uyeleri.set([vildan])
            logger.info(f"Assigned Vildan YAZICI to MAT course: {ders.ders_kodu} - {ders.ders_adi}")
            mat_assigned_count += 1
            assigned_by_rule = True

        # Rule 2: LAB courses (only if not assigned in Rule 1)
        is_lab = False
        if not assigned_by_rule:
            if ders.ders_kodu and 'lab' in ders.ders_kodu.lower():
                 is_lab = True
            elif ders.ders_adi and 'lab' in ders.ders_adi.lower():
                 is_lab = True
            # Also check the 'tip' field
            elif ders.tip == 'LAB':
                 is_lab = True

        if is_lab:
            ders.ogretim_uyeleri.set([candide, eray])
            logger.info(f"Assigned Candide ÖZTÜRK & Eray DURSUN to LAB course: {ders.ders_kodu} - {ders.ders_adi}")
            lab_assigned_count += 1
            assigned_by_rule = True

        # Rule 3: Random assignment for remaining courses *only if they have no instructors*
        if not assigned_by_rule and not ders.ogretim_uyeleri.exists():
            if other_instructors:
                random_instructor = random.choice(other_instructors)
                ders.ogretim_uyeleri.set([random_instructor])
                logger.info(f"Assigned random instructor ({random_instructor.ad_soyad}) to course: {ders.ders_kodu} - {ders.ders_adi}")
                random_assigned_count += 1
            else:
                 logger.warning(f"Skipping random assignment for {ders.ders_kodu}: No other instructors available.")
                 skipped_no_others_count += 1
        elif not assigned_by_rule:
             # This course didn't match MAT/LAB and already had an instructor(s). Leave it alone.
             logger.debug(f"Course {ders.ders_kodu} - {ders.ders_adi} already has instructors, skipping random assignment.")
             skipped_already_assigned_count += 1


    logger.info("Assignment Summary:")
    logger.info(f"- Courses assigned to Vildan YAZICI (MAT): {mat_assigned_count}")
    logger.info(f"- Courses assigned to Candide ÖZTÜRK & Eray DURSUN (LAB): {lab_assigned_count}")
    logger.info(f"- Courses assigned a random instructor: {random_assigned_count}")
    logger.info(f"- Courses skipped (no other instructors for random): {skipped_no_others_count}")
    logger.info(f"- Courses skipped (already had instructor, not MAT/LAB): {skipped_already_assigned_count}")

# Call run() for shell execution
run() 