from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from products.models import Category, Product
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create sample categories and products for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create categories
        categories_data = [
            {
                'name': 'Laptops',
                'slug': 'laptops',
                'description': 'High-performance laptops for work and gaming'
            },
            {
                'name': 'Smartphones',
                'slug': 'smartphones',
                'description': 'Latest smartphones with advanced features'
            },
            {
                'name': 'Audio',
                'slug': 'audio',
                'description': 'Premium audio equipment and accessories'
            },
            {
                'name': 'Accessories',
                'slug': 'accessories',
                'description': 'Essential tech accessories and peripherals'
            }
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat_data['slug']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')
        
        # Create sample products
        products_data = [
            {
                'name': 'MacBook Pro 14"',
                'slug': 'macbook-pro-14',
                'category': categories['laptops'],
                'description': 'Powerful laptop with M2 Pro chip, perfect for professionals and creatives.',
                'price': Decimal('1999.99'),
                'discount_price': Decimal('1799.99'),
                'discount_percentage': 10,
                'stock_quantity': 15,
                'availability': 'in_stock',
                'featured': True,
                'specifications': 'M2 Pro chip, 16GB RAM, 512GB SSD, 14-inch Liquid Retina XDR display'
            },
            {
                'name': 'iPhone 15 Pro',
                'slug': 'iphone-15-pro',
                'category': categories['smartphones'],
                'description': 'Latest iPhone with A17 Pro chip and titanium design.',
                'price': Decimal('999.99'),
                'stock_quantity': 25,
                'availability': 'in_stock',
                'featured': True,
                'specifications': 'A17 Pro chip, 6.1-inch Super Retina XDR display, 48MP camera, Titanium design'
            },
            {
                'name': 'Sony WH-1000XM5',
                'slug': 'sony-wh-1000xm5',
                'category': categories['audio'],
                'description': 'Industry-leading noise canceling wireless headphones.',
                'price': Decimal('399.99'),
                'discount_price': Decimal('349.99'),
                'discount_percentage': 12,
                'stock_quantity': 8,
                'availability': 'in_stock',
                'featured': False,
                'specifications': '30-hour battery life, LDAC codec, Touch controls, Multipoint connection'
            },
            {
                'name': 'Logitech MX Master 3S',
                'slug': 'logitech-mx-master-3s',
                'category': categories['accessories'],
                'description': 'Premium wireless mouse with ultra-fast scrolling.',
                'price': Decimal('99.99'),
                'stock_quantity': 30,
                'availability': 'in_stock',
                'featured': False,
                'specifications': '8000 DPI sensor, 70-day battery life, Silent clicks, MagSpeed scroll wheel'
            },
            {
                'name': 'Dell XPS 13',
                'slug': 'dell-xps-13',
                'category': categories['laptops'],
                'description': 'Ultra-thin laptop with InfinityEdge display.',
                'price': Decimal('1299.99'),
                'stock_quantity': 12,
                'availability': 'in_stock',
                'featured': False,
                'specifications': 'Intel Core i7, 16GB RAM, 512GB SSD, 13.4-inch 4K display'
            },
            {
                'name': 'Samsung Galaxy S24',
                'slug': 'samsung-galaxy-s24',
                'category': categories['smartphones'],
                'description': 'Flagship Android smartphone with AI features.',
                'price': Decimal('899.99'),
                'discount_price': Decimal('799.99'),
                'discount_percentage': 11,
                'stock_quantity': 20,
                'availability': 'in_stock',
                'featured': True,
                'specifications': 'Snapdragon 8 Gen 3, 6.2-inch Dynamic AMOLED, 50MP camera, AI features'
            }
        ]
        
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                slug=product_data['slug'],
                defaults=product_data
            )
            if created:
                self.stdout.write(f'Created product: {product.name}')
            else:
                self.stdout.write(f'Product already exists: {product.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write('You can now access the admin interface at http://127.0.0.1:8000/admin/')
        self.stdout.write('Login with your superuser credentials to manage products.')
