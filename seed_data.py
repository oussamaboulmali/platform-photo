"""
Seed script to populate initial data for the agency platform
Run this after all migrations are complete
"""
import os
import sys
import django

# Setup Django
sys.path.append('/workspace/backend/auth-service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from django.contrib.auth.hashers import make_password

def seed_users():
    """Create initial users"""
    print("Creating users...")
    from users.models import User, PhotographerProfile
    
    # Admin user
    admin, created = User.objects.get_or_create(
        email='admin@agency.local',
        defaults={
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'password': make_password('admin123')
        }
    )
    if created:
        print(f"  Created admin user: {admin.email}")
    
    # Validator
    validator, created = User.objects.get_or_create(
        email='validator@agency.local',
        defaults={
            'username': 'validator',
            'first_name': 'Validator',
            'last_name': 'User',
            'role': 'validator',
            'is_active': True,
            'password': make_password('validator123')
        }
    )
    if created:
        print(f"  Created validator user: {validator.email}")
    
    # Photographer
    photographer, created = User.objects.get_or_create(
        email='photographer@agency.local',
        defaults={
            'username': 'photographer',
            'first_name': 'John',
            'last_name': 'Photographer',
            'role': 'photographer',
            'is_active': True,
            'password': make_password('photo123')
        }
    )
    if created:
        print(f"  Created photographer user: {photographer.email}")
        PhotographerProfile.objects.create(
            user=photographer,
            display_name='John Photographer',
            bio='Professional photographer'
        )
    
    # Infographiste
    infographiste, created = User.objects.get_or_create(
        email='infographiste@agency.local',
        defaults={
            'username': 'infographiste',
            'first_name': 'Jane',
            'last_name': 'Designer',
            'role': 'infographiste',
            'is_active': True,
            'password': make_password('design123')
        }
    )
    if created:
        print(f"  Created infographiste user: {infographiste.email}")
        PhotographerProfile.objects.create(
            user=infographiste,
            display_name='Jane Designer',
            bio='Graphic designer'
        )
    
    # Customer
    customer, created = User.objects.get_or_create(
        email='customer@agency.local',
        defaults={
            'username': 'customer',
            'first_name': 'Test',
            'last_name': 'Customer',
            'role': 'customer',
            'is_active': True,
            'password': make_password('customer123')
        }
    )
    if created:
        print(f"  Created customer user: {customer.email}")

def seed_categories():
    """Create initial categories"""
    print("\nCreating categories...")
    sys.path.append('/workspace/backend/image-service')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_service.settings')
    django.setup()
    
    from images.models import Category
    
    categories = [
        ('news', 'News & Events'),
        ('sports', 'Sports'),
        ('nature', 'Nature & Landscape'),
        ('business', 'Business & Technology'),
        ('people', 'People & Lifestyle'),
        ('architecture', 'Architecture'),
        ('travel', 'Travel & Tourism'),
    ]
    
    for slug, name in categories:
        cat, created = Category.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'is_active': True}
        )
        if created:
            print(f"  Created category: {name}")

def seed_topics():
    """Create initial topics"""
    print("\nCreating topics...")
    from images.models import Topic
    
    topics = [
        ('event', 'event', 'Event Coverage'),
        ('document', 'document', 'Documentary'),
        ('top_shot', 'top_shot', 'Top Shot'),
        ('breaking-news', 'custom', 'Breaking News'),
        ('feature', 'custom', 'Feature Story'),
    ]
    
    for slug, topic_type, name in topics:
        topic, created = Topic.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'type': topic_type, 'is_active': True}
        )
        if created:
            print(f"  Created topic: {name}")

def seed_places():
    """Create initial places"""
    print("\nCreating places...")
    from images.models import Place
    
    places = [
        ('algiers', 'city', 'Algiers'),
        ('oran', 'city', 'Oran'),
        ('constantine', 'city', 'Constantine'),
        ('algeria', 'country', 'Algeria'),
    ]
    
    for slug, place_type, name in places:
        place, created = Place.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'type': place_type, 'is_active': True}
        )
        if created:
            print(f"  Created place: {name}")

def seed_subscription_plans():
    """Create subscription plans"""
    print("\nCreating subscription plans...")
    sys.path.append('/workspace/backend/order-service')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'order_service.settings')
    django.setup()
    
    from orders.models import SubscriptionPlan
    
    plans = [
        ('1-month', '1 Month Plan', 30, 2500, 10, 'Standard monthly subscription'),
        ('3-months', '3 Months Plan', 90, 6500, 35, 'Quarterly subscription with savings'),
        ('6-months', '6 Months Plan', 180, 12000, 80, 'Best value - half year subscription'),
    ]
    
    for slug, name, days, price, credits, desc in plans:
        plan, created = SubscriptionPlan.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'duration_days': days,
                'price': price,
                'quota_credits': credits,
                'description': desc,
                'is_active': True,
                'order': days // 30
            }
        )
        if created:
            print(f"  Created plan: {name}")

def seed_blocs():
    """Create initial blocs"""
    print("\nCreating blocs...")
    sys.path.append('/workspace/backend/admin-service')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_service.settings')
    django.setup()
    
    from content_admin.models import Bloc
    
    blocs = [
        ('homepage-hero', 'Homepage Hero', 'a_la_une', 'latest', None, ['homepage']),
        ('top-stories', 'Top Stories', 'topic_block', 'topic', 1, ['homepage']),
        ('latest-sports', 'Latest Sports', 'category_block', 'category', 2, ['homepage', 'search']),
    ]
    
    for slug, name, bloc_type, source_type, source_id, locations in blocs:
        bloc, created = Bloc.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'type': bloc_type,
                'source_type': source_type,
                'source_id': source_id,
                'visible': True,
                'page_locations': locations,
                'max_items': 10
            }
        )
        if created:
            print(f"  Created bloc: {name}")

if __name__ == '__main__':
    print("Starting seed process...\n")
    print("=" * 50)
    
    try:
        seed_users()
        seed_categories()
        seed_topics()
        seed_places()
        seed_subscription_plans()
        seed_blocs()
        
        print("\n" + "=" * 50)
        print("\n✓ Seed data created successfully!")
        print("\nDefault users created:")
        print("  Admin:        admin@agency.local / admin123")
        print("  Validator:    validator@agency.local / validator123")
        print("  Photographer: photographer@agency.local / photo123")
        print("  Infographiste: infographiste@agency.local / design123")
        print("  Customer:     customer@agency.local / customer123")
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
