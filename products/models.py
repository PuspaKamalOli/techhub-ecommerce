# products/models.py
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class ProductQuerySet(models.QuerySet):
    def with_bayesian_score(self):
        from django.db.models import Count, Avg, F, FloatField, ExpressionWrapper, Value
        from django.db.models.expressions import RawSQL
        from django.db.models.functions import Power, Coalesce
        from products.models import ProductReview

        global_avg = ProductReview.objects.aggregate(Avg('rating'))['rating__avg'] or 0.0
        m = 2.0
        gravity = 1.5

        # Bayesian score: pulls low-review products toward global average
        # Age in days is computed from release_date if set, otherwise from created_at
        # Final score is divided by (age_days + 2)^gravity — newer products rank higher
        age_expr = ExpressionWrapper(
            RawSQL(
                "COALESCE(julianday('now') - julianday(products_product.release_date), julianday('now') - julianday(products_product.created_at))",
                []
            ),
            output_field=FloatField()
        )

        return self.annotate(
            v_count=Count('reviews'),
            r_avg=Avg('reviews__rating')
        ).annotate(
            bayesian_score=ExpressionWrapper(
                (
                    (F('v_count') / (F('v_count') + Value(m))) * Coalesce(F('r_avg'), Value(0.0)) +
                    (Value(m) / (F('v_count') + Value(m))) * Value(float(global_avg))
                ) / Power(age_expr + Value(2.0), Value(gravity)),
                output_field=FloatField()
            )
        )

class ProductManager(ActiveManager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db).filter(is_active=True)
        
    def with_bayesian_score(self):
        return self.get_queryset().with_bayesian_score()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    objects = ActiveManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:category_detail', args=[self.slug])

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()

class Product(models.Model):
    AVAILABILITY_CHOICES = [
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('pre_order', 'Pre Order'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Stock Keeping Unit")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_percentage = models.PositiveIntegerField(blank=True, null=True, help_text="Discount percentage (e.g., 20 for 20% off)")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    specifications = models.TextField(blank=True, help_text="Product specifications and technical details")
    release_date = models.DateField(blank=True, null=True, help_text="Official product release date (used for time-decay ranking)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='in_stock', db_index=True)
    
    objects = ProductManager()
    all_objects = models.Manager()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:product_detail', args=[self.slug])
    
    @property
    def get_price(self):
        """Return discount price if available, otherwise regular price"""
        return self.discount_price if self.discount_price else self.price
    
    @property
    def has_discount(self):
        """Check if product has a discount"""
        return self.discount_price is not None and self.discount_price < self.price

    @property
    def average_rating(self):
        if hasattr(self, 'r_avg'):
            return round(float(self.r_avg), 1) if self.r_avg else 0.0
        from django.db.models import Avg
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(float(avg), 1) if avg else 0.0

    @property
    def review_count(self):
        if hasattr(self, 'v_count'):
            return self.v_count
        return self.reviews.count()
    
    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided
        if not self.sku:
            self.sku = f"SKU-{self.id or 'NEW'}-{self.name[:10].upper().replace(' ', '')}"
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False, help_text="Mark as primary image for the product")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['product', '-is_primary']
    
    def __str__(self):
        return f"{self.product.name} - Image"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            try:
                from PIL import Image as PILImage
                img_path = self.image.path
                with PILImage.open(img_path) as img:
                    max_size = (800, 800)
                    if img.width > max_size[0] or img.height > max_size[1]:
                        img.thumbnail(max_size, PILImage.LANCZOS)
                        # Convert RGBA to RGB for JPEG compatibility
                        if img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                        img.save(img_path, optimize=True, quality=85)
            except Exception:
                pass  # Never break uploads due to resize failure

class ProductReview(models.Model):
    RATING_CHOICES = [
        (1.0, '1 Star'),
        (1.5, '1.5 Stars'),
        (2.0, '2 Stars'),
        (2.5, '2.5 Stars'),
        (3.0, '3 Stars'),
        (3.5, '3.5 Stars'),
        (4.0, '4 Stars'),
        (4.5, '4.5 Stars'),
        (5.0, '5 Stars'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=2, decimal_places=1, choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['product', 'user']
        indexes = [
            models.Index(fields=['product', 'rating'], name='review_product_rating_idx'),
            models.Index(fields=['product', '-created_at'], name='review_product_date_idx'),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.rating} stars"