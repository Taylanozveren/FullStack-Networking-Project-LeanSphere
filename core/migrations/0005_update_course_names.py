from django.db import migrations

def update_names(apps, schema_editor):
    Discipline = apps.get_model('core', 'Discipline')
    Course = apps.get_model('core', 'Course')
    
    # Update Discipline names - More general categories
    discipline_updates = {
        'Artificial Intelligence': 'AI & Data Science',
        'Operating Systems': 'System & OS Programming',
        'Network Programming': 'Network & Security',
        'Web Programming': 'Web Technologies'
    }
    
    for old_name, new_name in discipline_updates.items():
        try:
            discipline = Discipline.objects.get(name=old_name)
            discipline.name = new_name
            discipline.save()
        except Discipline.DoesNotExist:
            continue
    
    # Update Course titles - More specific course names
    course_updates = {
        'ACM465': {
            'code': 'ACM465',
            'title': 'TensorFlow & Deep Learning',
            'description': 'Deep learning with TensorFlow, neural networks, and AI applications.'
        },
        'ACM369': {
            'code': 'ACM369',
            'title': 'Linux System Programming',
            'description': 'Advanced Linux system programming, processes, and memory management.'
        },
        'ACM412': {
            'code': 'ACM412',
            'title': 'Django & Network Programming',
            'description': 'Network programming with Django, APIs, and web services.'
        },
        'ACM368': {
            'code': 'ACM368',
            'title': 'PHP & Web Programming',
            'description': 'Web development with PHP, MySQL, and modern web frameworks.'
        }
    }
    
    for old_code, new_data in course_updates.items():
        try:
            course = Course.objects.get(code=old_code)
            # Keep the original code to maintain relationships
            course.title = new_data['title']
            course.description = new_data['description']
            course.save()
        except Course.DoesNotExist:
            continue

def reverse_names(apps, schema_editor):
    Discipline = apps.get_model('core', 'Discipline')
    Course = apps.get_model('core', 'Course')
    
    # Reverse Discipline names
    discipline_updates = {
        'AI & Data Science': 'Artificial Intelligence',
        'System & OS Programming': 'Operating Systems',
        'Network & Security': 'Network Programming',
        'Web Technologies': 'Web Programming'
    }
    
    for old_name, new_name in discipline_updates.items():
        try:
            discipline = Discipline.objects.get(name=old_name)
            discipline.name = new_name
            discipline.save()
        except Discipline.DoesNotExist:
            continue
    
    # Original course titles
    course_updates = {
        'ACM465': 'Artificial Intelligence',
        'ACM369': 'Operating Systems',
        'ACM412': 'Network Programming',
        'ACM368': 'Web Programming'
    }
    
    for code, original_title in course_updates.items():
        try:
            course = Course.objects.get(code=code)
            course.title = original_title
            course.save()
        except Course.DoesNotExist:
            continue

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_post_pdf_summary'),
    ]

    operations = [
        migrations.RunPython(update_names, reverse_names),
    ] 