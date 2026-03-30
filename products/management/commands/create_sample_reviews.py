from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from products.models import Product, ProductReview

class Command(BaseCommand):
    help = 'Create sample product reviews for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample reviews...')
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'Created test user: {user.username}')
        
        # Sample reviews data
        reviews_data = [
            {
                'product_slug': 'samsung-galaxy-s24',
                'rating': 5,
                'comment': 'Excellent phone! The AI features are amazing and the camera quality is outstanding.'
            },
            {
                'product_slug': 'samsung-galaxy-s24',
                'rating': 4,
                'comment': 'Great phone overall, but the battery could be better. Love the design though.'
            },
            {
                'product_slug': 'macbook-pro-14',
                'rating': 5,
                'comment': 'Incredible performance! The M2 Pro chip is a game changer for my development work.'
            },
            {
                'product_slug': 'iphone-15-pro',
                'rating': 5,
                'comment': 'Best iPhone I\'ve ever owned. The titanium design is beautiful and the camera is incredible.'
            },
            {
                'product_slug': 'sony-wh-1000xm5',
                'rating': 4,
                'comment': 'Amazing noise cancellation and sound quality. Very comfortable for long listening sessions.'
            },
            {
                'product_slug': 'logitech-mx-master-3s',
                'rating': 5,
                'comment': 'Perfect mouse for productivity. The silent clicks and ergonomic design are fantastic.'
            }
        ]
        
        for review_data in reviews_data:
            try:
                product = Product.objects.get(slug=review_data['product_slug'])
                review, created = ProductReview.objects.get_or_create(
                    product=product,
                    user=user,
                    defaults={
                        'rating': review_data['rating'],
                        'comment': review_data['comment']
                    }
                )
                
                if created:
                    self.stdout.write(f'Created review for {product.name}: {review_data["rating"]} stars')
                else:
                    self.stdout.write(f'Review already exists for {product.name}')
                    
            except Product.DoesNotExist:
                self.stdout.write(f'Product with slug {review_data["product_slug"]} not found')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample reviews!')
        )
